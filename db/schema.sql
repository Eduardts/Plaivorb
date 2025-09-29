-- Enable system versioning if needed (for Temporal Tables)
-- This might be set at the server level or per-session, but good to note.
-- SET GLOBAL system_versioning_of_rowids = ON;

-- Create your main table for geospatial features with semantic embeddings
CREATE TABLE IF NOT EXISTS geo_features (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    geometry GEOMETRY NOT NULL SRID 4326, -- Assuming WGS84
    semantic_embedding VECTOR<FLOAT, 128>, -- MariaDB Vector type
    feature_type VARCHAR(50), -- e.g., 'building', 'forest', 'road'
    description TEXT,
    -- System-versioned temporal table setup
    ROW START hidden_row_start_timestamp DATETIME(6) AS ROW START,
    ROW END hidden_row_end_timestamp DATETIME(6) AS ROW END,
    PERIOD FOR SYSTEM_TIME (hidden_row_start_timestamp, hidden_row_end_timestamp)
) WITH SYSTEM VERSIONING;

-- Create a table for raw incoming data (e.g., from drones)
CREATE TABLE IF NOT EXISTS raw_sensor_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME(6),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    sensor_reading JSON, -- For capturing arbitrary sensor data, e.g., thermal, LiDAR points
    processed_status VARCHAR(20) DEFAULT 'NEW',
    SPATIAL INDEX(geometry) -- Ensure spatial indexing for performance
);

-- Create a ColumnStore table for historical archives or large-scale analytics
-- This table could store aggregated or summarized versions of geo_features over time
CREATE TABLE IF NOT EXISTS historical_geo_summary (
    snapshot_date DATE,
    feature_type VARCHAR(50),
    avg_semantic_value FLOAT, -- Example: average of a specific embedding dimension
    count_features BIGINT,
    total_area DECIMAL(18, 2), -- Example: total area for a feature type
    -- Other aggregated metrics suitable for columnar storage
    INDEX (snapshot_date, feature_type) USING CLUSTERED COLUMNSTORE
) ENGINE=ColumnStore;

-- Table for storing detected changes/anomalies
CREATE TABLE IF NOT EXISTS detected_changes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    change_timestamp DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    feature_id INT,
    feature_name VARCHAR(255),
    change_type VARCHAR(100), -- e.g., 'new_structure', 'deforestation', 'land_use_change'
    severity ENUM('low', 'medium', 'high'),
    details JSON, -- Store more info about the change
    location GEOMETRY NOT NULL SRID 4326,
    FOREIGN KEY (feature_id) REFERENCES geo_features(id) ON DELETE CASCADE
);

-- Stored procedure example: function to compare semantic embeddings and detect change
DELIMITER //
CREATE PROCEDURE DetectSemanticChange(
    IN current_id INT,
    IN threshold FLOAT
)
BEGIN
    DECLARE prev_embedding VECTOR<FLOAT, 128>;
    DECLARE current_embedding VECTOR<FLOAT, 128>;
    DECLARE dist FLOAT;

    -- Get current embedding
    SELECT semantic_embedding INTO current_embedding
    FROM geo_features WHERE id = current_id FOR SYSTEM_TIME AS OF NOW();

    -- Get previous embedding (e.g., 1 day ago)
    SELECT semantic_embedding INTO prev_embedding
    FROM geo_features WHERE id = current_id FOR SYSTEM_TIME AS OF (NOW() - INTERVAL 1 DAY);

    IF prev_embedding IS NOT NULL AND current_embedding IS NOT NULL THEN
        SET dist = VECTOR_DISTANCE(current_embedding, prev_embedding);
        IF dist > threshold THEN
            INSERT INTO detected_changes (feature_id, feature_name, change_type, severity, location, details)
            SELECT
                current_id,
                name,
                'Semantic Shift',
                'high',
                geometry,
                JSON_OBJECT('distance', dist)
            FROM geo_features WHERE id = current_id;
        END IF;
    END IF;
END //
DELIMITER ;
