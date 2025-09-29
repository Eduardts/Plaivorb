DELIMITER //

-- Function to generate a random vector (for demonstration purposes)
-- In a real application, this would come from an ML model
DROP FUNCTION IF EXISTS GenerateRandomVector;
CREATE FUNCTION GenerateRandomVector(size INT)
RETURNS VARCHAR(8000)
DETERMINISTIC
BEGIN
    DECLARE i INT DEFAULT 0;
    DECLARE vec_str VARCHAR(8000) DEFAULT '[';
    WHILE i < size DO
        SET vec_str = CONCAT(vec_str, CAST(RAND() AS CHAR));
        IF i < size - 1 THEN
            SET vec_str = CONCAT(vec_str, ', ');
        END IF;
        SET i = i + 1;
    END WHILE;
    SET vec_str = CONCAT(vec_str, ']');
    RETURN vec_str;
END //


-- Stored procedure to detect semantic and geometric changes for a given feature
-- Compares current state with a previous state (e.g., 1 day ago)
DROP PROCEDURE IF EXISTS DetectFeatureChange;
CREATE PROCEDURE DetectFeatureChange(
    IN p_feature_id INT,
    IN p_semantic_threshold FLOAT,
    IN p_geometry_tolerance FLOAT -- e.g., for ST_Area or ST_HausdorffDistance
)
BEGIN
    DECLARE v_current_embedding VECTOR<FLOAT, 128>;
    DECLARE v_prev_embedding VECTOR<FLOAT, 128>;
    DECLARE v_semantic_distance FLOAT;
    DECLARE v_current_geometry GEOMETRY;
    DECLARE v_prev_geometry GEOMETRY;
    DECLARE v_geometry_changed BOOLEAN DEFAULT FALSE;
    DECLARE v_feature_name VARCHAR(255);
    DECLARE v_feature_type VARCHAR(50);

    -- Get current feature state
    SELECT
        gf.semantic_embedding,
        gf.geometry,
        gf.name,
        gf.feature_type
    INTO
        v_current_embedding,
        v_current_geometry,
        v_feature_name,
        v_feature_type
    FROM geo_features FOR SYSTEM_TIME AS OF NOW() AS gf
    WHERE gf.id = p_feature_id;

    -- Get previous feature state (e.g., 1 day ago, adjust interval as needed)
    -- This assumes there was a version of the record 1 day ago.
    SELECT
        gf.semantic_embedding,
        gf.geometry
    INTO
        v_prev_embedding,
        v_prev_geometry
    FROM geo_features FOR SYSTEM_TIME AS OF (NOW() - INTERVAL 1 DAY) AS gf
    WHERE gf.id = p_feature_id;

    -- Check if a previous version exists
    IF v_prev_embedding IS NOT NULL AND v_prev_geometry IS NOT NULL THEN
        -- Calculate semantic distance
        SET v_semantic_distance = VECTOR_DISTANCE(v_current_embedding, v_prev_embedding);

        -- Check for geometric change (e.g., area change, or significant difference)
        IF NOT ST_Equals(v_current_geometry, v_prev_geometry) THEN
            -- More sophisticated geometric change detection (e.g., area difference or Hausdorff distance)
            -- For simplicity, we just check if geometries are not equal.
            -- A real system might compare ST_Area(v_current_geometry) vs ST_Area(v_prev_geometry)
            -- or ST_HausdorffDistance(v_current_geometry, v_prev_geometry)
            SET v_geometry_changed = TRUE;
        END IF;

        -- Record semantic change if above threshold
        IF v_semantic_distance > p_semantic_threshold THEN
            INSERT INTO detected_changes (feature_id, feature_name, change_type, severity, details, location)
            VALUES (
                p_feature_id,
                v_feature_name,
                'Semantic Shift',
                'high',
                JSON_OBJECT('semantic_distance', v_semantic_distance),
                v_current_geometry
            );
        END IF;

        -- Record geometric change
        IF v_geometry_changed THEN
            INSERT INTO detected_changes (feature_id, feature_name, change_type, severity, details, location)
            VALUES (
                p_feature_id,
                v_feature_name,
                'Geometric Change',
                'medium',
                JSON_OBJECT(
                    'description', 'Geometry has significantly changed'
                    -- Could add ST_Area(v_current_geometry), ST_Area(v_prev_geometry) here
                ),
                v_current_geometry
            );
        END IF;

    ELSE
        -- If no previous version, it's a new feature (if not already recorded as such)
        -- You might want to handle initial insertions differently or record them as "new"
        -- For this demo, we assume initial inserts are handled by the ingestion process.
        SELECT COUNT(*) INTO @new_feature_exists FROM detected_changes
        WHERE feature_id = p_feature_id AND change_type = 'New Feature';

        IF @new_feature_exists = 0 THEN
            INSERT INTO detected_changes (feature_id, feature_name, change_type, severity, location)
            VALUES (p_feature_id, v_feature_name, 'New Feature', 'low', v_current_geometry);
        END IF;
    END IF;

END //


-- Stored procedure to process all features and detect changes
DROP PROCEDURE IF EXISTS ProcessAllFeaturesForChangeDetection;
CREATE PROCEDURE ProcessAllFeaturesForChangeDetection(
    IN p_semantic_threshold FLOAT,
    IN p_geometry_tolerance FLOAT
)
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE feature_id INT;
    DECLARE cur CURSOR FOR SELECT id FROM geo_features FOR SYSTEM_TIME AS OF NOW();
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cur;

    read_loop: LOOP
        FETCH cur INTO feature_id;
        IF done THEN
            LEAVE read_loop;
        END IF;
        CALL DetectFeatureChange(feature_id, p_semantic_threshold, p_geometry_tolerance);
    END LOOP;

    CLOSE cur;
END //

DELIMITER ;
