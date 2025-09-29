import mariadb
import json
import time
import random
import uuid
from datetime import datetime, timedelta
from shapely.geometry import Point, Polygon
from shapely import wkt
from src.utils import get_db_connection, generate_synthetic_embedding

def generate_random_point_in_area(min_lat, max_lat, min_lon, max_lon):
    """Generates a random point within a specified bounding box."""
    lat = random.uniform(min_lat, max_lat)
    lon = random.uniform(min_lon, max_lon)
    return Point(lon, lat)

def generate_random_polygon_around_point(center_point, size_degrees=0.0005):
    """Generates a simple square polygon around a center point."""
    lon, lat = center_point.x, center_point.y
    half_size = size_degrees / 2.0
    coords = [
        (lon - half_size, lat - half_size),
        (lon + half_size, lat - half_size),
        (lon + half_size, lat + half_size),
        (lon - half_size, lat + half_size),
        (lon - half_size, lat - half_size) # Close the polygon
    ]
    return Polygon(coords)

def ingest_raw_sensor_data(conn: mariadb.MariaDBConnection, num_records: int = 5):
    """
    Simulates ingesting raw sensor data into the `raw_sensor_data` table.
    Generates random points and sensor readings.
    """
    cursor = conn.cursor()
    print(f"\n--- Ingesting {num_records} raw sensor data records ---")

    feature_types = ['building', 'road', 'forest', 'water']
    min_lat, max_lat = 34.0, 34.1 # Example bounding box for Los Angeles area
    min_lon, max_lon = -118.3, -118.2

    for _ in range(num_records):
        timestamp = datetime.now() - timedelta(minutes=random.randint(0, 60))
        center_point = generate_random_point_in_area(min_lat, max_lat, min_lon, max_lon)
        # Use a square polygon for simplicity in demo, or just a point
        geometry_wkt = generate_random_polygon_around_point(center_point).wkt if random.random() > 0.5 else center_point.wkt
        
        sensor_reading = {
            "temperature": round(random.uniform(20, 35), 2),
            "humidity": round(random.uniform(40, 80), 2),
            "pressure": round(random.uniform(900, 1100), 2),
            "sensor_id": str(uuid.uuid4())
        }
        feature_type = random.choice(feature_types)
        
        try:
            cursor.execute(
                "INSERT INTO raw_sensor_data (timestamp, latitude, longitude, sensor_reading, feature_type, geometry) VALUES (?, ?, ?, ?, ?, ST_GeomFromText(?, 4326))",
                (timestamp, center_point.y, center_point.x, json.dumps(sensor_reading), feature_type, geometry_wkt)
            )
            print(f"  Ingested record at {center_point.y:.4f},{center_point.x:.4f}")
        except mariadb.Error as e:
            print(f"  Error ingesting raw data: {e}")
            conn.rollback()
            continue
    conn.commit()
    print("--- Raw sensor data ingestion complete ---")


if __name__ == '__main__':
    conn = get_db_connection()
    if conn:
        ingest_raw_sensor_data(conn, num_records=10)
        conn.close()
    else:
        print("Failed to get database connection.")
