
INSERT INTO geo_features (name, geometry, semantic_embedding, feature_type, description) VALUES
('Building A', ST_GeomFromText('POLYGON((10 10, 10 20, 20 20, 20 10, 10 10))', 4326), '[0.1, 0.2, ..., 0.128]', 'building', 'Original state of Building A');

-- Simulate a change (e.g., a new semantic embedding due to renovation)
UPDATE geo_features SET semantic_embedding = '[0.15, 0.25, ..., 0.130]' WHERE name = 'Building A';

INSERT INTO raw_sensor_data (timestamp, latitude, longitude, sensor_reading) VALUES
('2025-09-29 10:00:00', 34.0522, -118.2437, '{"temp":25.5, "humidity":60}');
