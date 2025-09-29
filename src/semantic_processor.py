import mariadb
import json
from datetime import datetime, timedelta
from src.utils import get_db_connection, generate_synthetic_embedding
from shapely.wkt import loads as wkt_loads
import random
import numpy as np
from embedding_model import EmbeddingModel

embedding_model = EmbeddingModel()


def process_raw_data_into_geo_features(conn: mariadb.MariaDBConnection):
    """
    Processes new raw sensor data, generates synthetic embeddings, and
    updates/inserts into `geo_features`.
    """
    cursor = conn.cursor(dictionary=True) # Use dictionary cursor for easier access by column name
    print("\n--- Processing raw data into geo_features ---")


    #     cursor = conn.cursor(dictionary=True) 
    # print("\n--- Processing raw data into geo_features ---")
    # cursor.execute("SELECT id, timestamp, latitude, longitude, sensor_reading, feature_type, ST_AsText(geometry) as geometry_wkt FROM raw_sensor_data WHERE processed_status = 'NEW';")
    # new_raw_data = cursor.fetchall()
    # for record in new_raw_data:
    #     # Adding complexity: Instead of just generating random embeddings
    #     # Use the real model to generate them (could integrate training as pseudo-code)
    #     feature_type = record['feature_type']
        
    #     # Assuming sensor_reading is JSON structured data
    #     # Convert sensor reading to Numpy array to create embeddings
    #     # (This will require processing the JSON data properly, e.g., flattening it)
    #     # Example (pretend sensor_data has more refined features for X):
    #     sensor_data = json.loads(record['sensor_reading'])
    #     embeddings_input = np.array([[sensor_data['temperature'], sensor_data['humidity'], sensor_data['pressure']]])
    #     # Now generate embedding correctly
    #     semantic_embedding = embedding_model.predict(embeddings_input)[0].tolist()
        

    # Select unprocessed raw data
    cursor.execute("SELECT id, timestamp, latitude, longitude, sensor_reading, feature_type, ST_AsText(geometry) as geometry_wkt FROM raw_sensor_data WHERE processed_status = 'NEW'")
    new_raw_data = cursor.fetchall()

    if not new_raw_data:
        print("No new raw data to process.")
        return

    for record in new_raw_data:
        raw_id = record['id']
        feature_type = record['feature_type']
        
        # Generate synthetic semantic embedding
        # Use record ID as seed for reproducible synthetic embeddings for a given raw record
        semantic_embedding = generate_synthetic_embedding(feature_type, seed=raw_id)
        
        # In a real scenario, the geometry might also be processed/refined here
        geometry_wkt = record['geometry_wkt']

        # Check if a similar feature already exists
        # For simplicity, we'll check based on a small buffer around the point
        # A more robust check might involve comparing WKT or a unique identifier from sensor_reading
        try:
            # First, try to find an existing feature that overlaps spatially
            # Use a small buffer for point data to find nearby features
            # This is a simplification; a real system might use other criteria for 'sameness'
            
            # Use ST_Intersects with a buffer for points or direct equality for polygons
            
            # Attempt to find an existing feature by its geometry
            cursor.execute(
                f"""
                SELECT id, semantic_embedding
                FROM geo_features
                WHERE ST_Intersects(geometry, ST_Buffer(ST_GeomFromText(%s, 4326), 0.0001));
                """, (geometry_wkt,) # Buffer by 0.0001 degrees
            )
            existing_feature = cursor.fetchone()

            if existing_feature:
                # Update existing feature (simulating change over time)
                feature_id = existing_feature['id']
                
                # Introduce a slight variation to the embedding to simulate change
                # This is crucial for demonstrating VECTOR_DISTANCE and change detection
                current_embedding_np = np.array(semantic_embedding)
                noise = np.random.rand(128) * 0.05 * (1 if random.random() > 0.3 else -1) # small random change
                new_embedding_np = np.clip(current_embedding_np + noise, 0, 1)
                new_embedding = new_embedding_np.tolist()


                print(f"  Updating existing feature {feature_id} with new embedding and geometry.")
                cursor.execute(
                    """
                    UPDATE geo_features
                    SET semantic_embedding = %s,
                        geometry = ST_GeomFromText(%s, 4326),
                        feature_type = %s,
                        description = JSON_SET(description, '$.last_updated_raw_id', ?)
                    WHERE id = ?
                    """,
                    (json.dumps(new_embedding), geometry_wkt, feature_type, raw_id, feature_id)
                )
            else:
                # Insert new feature
                print(f"  Inserting new feature (type: {feature_type}).")
                cursor.execute(
                    """
                    INSERT INTO geo_features (name, geometry, semantic_embedding, feature_type, description)
                    VALUES (?, ST_GeomFromText(?, 4326), ?, ?, JSON_OBJECT('initial_raw_id', ?))
                    """,
                    (f"Feature-{raw_id}", geometry_wkt, json.dumps(semantic_embedding), feature_type, raw_id)
                )
            
            # Mark raw data as processed
            cursor.execute("UPDATE raw_sensor_data SET processed_status = 'PROCESSED' WHERE id = ?", (raw_id,))
            conn.commit()

        except mariadb.Error as e:
            print(f"  Error processing raw data record {raw_id}: {e}")
            conn.rollback()

    print("--- Raw data processing complete ---")

if __name__ == '__main__':
    conn = get_db_connection()
    if conn:
        process_raw_data_into_geo_features(conn)
        conn.close()
    else:
        print("Failed to get database connection.")
