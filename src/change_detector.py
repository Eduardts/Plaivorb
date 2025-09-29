
# In change_detector.py
cursor.execute("""
    SELECT
        gf_curr.id,
        gf_curr.name,
        gf_curr.feature_type,
        ST_AsText(gf_curr.geometry) AS current_geometry,
        ST_AsText(gf_prev.geometry) AS previous_geometry,
        VECTOR_DISTANCE(gf_curr.semantic_embedding, gf_prev.semantic_embedding) AS semantic_dist,
        gf_curr.ROW_START,
        gf_prev.ROW_START
    FROM geo_features FOR SYSTEM_TIME AS OF NOW() AS gf_curr
    JOIN geo_features FOR SYSTEM_TIME AS OF (NOW() - INTERVAL 1 DAY) AS gf_prev
        ON gf_curr.id = gf_prev.id
    WHERE VECTOR_DISTANCE(gf_curr.semantic_embedding, gf_prev.semantic_embedding) > 0.1 -- threshold
    OR ST_Equals(gf_curr.geometry, gf_prev.geometry) = 0; -- check for geometric change
""")
