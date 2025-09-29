import mariadb
import json
import numpy as np
import configparser

def get_db_connection():
    """Reads database connection details from config.ini and returns a connection object."""
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        conn = mariadb.connect(
            host=config['mariadb']['host'],
            port=int(config['mariadb']['port']),
            user=config['mariadb']['user'],
            password=config['mariadb']['password'],
            database=config['mariadb']['database']
        )
        return conn
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        return None

def generate_synthetic_embedding(feature_type: str, seed=None) -> list[float]:
    """
    Generates a synthetic 128-dimension vector embedding based on feature type.
    For demonstration, different feature types will have slightly different baseline vectors.
    """
    np.random.seed(seed) # for reproducibility in demo

    base_vector = np.zeros(128)
    if feature_type == 'building':
        base_vector[0:10] = np.random.rand(10) * 0.5 + 0.5 # High values for first few dimensions
    elif feature_type == 'road':
        base_vector[10:20] = np.random.rand(10) * 0.5 + 0.5
    elif feature_type == 'forest':
        base_vector[20:30] = np.random.rand(10) * 0.5 + 0.5
    elif feature_type == 'water':
        base_vector[30:40] = np.random.rand(10) * 0.5 + 0.5
    else: # default for 'unknown' or 'other'
        base_vector[40:50] = np.random.rand(10) * 0.5 + 0.5

    # Add some random noise to make vectors slightly unique
    noise = np.random.rand(128) * 0.1
    embedding = base_vector + noise
    embedding = np.clip(embedding, 0, 1) # Keep values between 0 and 1

    return embedding.tolist()

def geometry_to_wkt(lat: float, lon: float, geom_type: str = 'POINT') -> str:
    """Converts latitude/longitude to WKT point. Extend for other geometries."""
    if geom_type == 'POINT':
        return f"ST_GeomFromText('POINT({lon} {lat})', 4326)"
    # Add more complex WKT generation if needed for polygons, etc.
    return None

if __name__ == '__main__':
    # Simple test for connection
    conn = get_db_connection()
    if conn:
        print("Successfully connected to MariaDB!")
        conn.close()
    else:
        print("Failed to connect to MariaDB.")

    # Test embedding generation
    print("\nSynthetic embedding for 'building':")
    print(generate_synthetic_embedding('building', seed=42)[:5], "...") # print first 5 elements

    print("\nSynthetic embedding for 'road':")
    print(generate_synthetic_embedding('road', seed=42)[:5], "...")
