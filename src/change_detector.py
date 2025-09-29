
# In change_detector.py
# cursor.execute("""
#     SELECT
#         gf_curr.id,
#         gf_curr.name,
#         gf_curr.feature_type,
#         ST_AsText(gf_curr.geometry) AS current_geometry,
#         ST_AsText(gf_prev.geometry) AS previous_geometry,
#         VECTOR_DISTANCE(gf_curr.semantic_embedding, gf_prev.semantic_embedding) AS semantic_dist,
#         gf_curr.ROW_START,
#         gf_prev.ROW_START
#     FROM geo_features FOR SYSTEM_TIME AS OF NOW() AS gf_curr
#     JOIN geo_features FOR SYSTEM_TIME AS OF (NOW() - INTERVAL 1 DAY) AS gf_prev
#         ON gf_curr.id = gf_prev.id
#     WHERE VECTOR_DISTANCE(gf_curr.semantic_embedding, gf_prev.semantic_embedding) > 0.1 -- threshold
#     OR ST_Equals(gf_curr.geometry, gf_prev.geometry) = 0; -- check for geometric change
# """)

import mariadb
import time
from src.utils import get_db_connection

def run_change_detection(conn: mariadb.MariaDBConnection,
                         semantic_threshold: float = 0.08, # Adjust this threshold
                         geometry_tolerance: float = 0.001): # Not heavily used in current SQL SP
    """
    Executes the stored procedure in MariaDB to detect changes.
    """
    cursor = conn.cursor()
    print(f"\n--- Running Plaivorb Change Detection ---")
    print(f"  Using semantic threshold: {semantic_threshold}")

    try:
        # Call the stored procedure to process all features
        cursor.callproc('ProcessAllFeaturesForChangeDetection', (semantic_threshold, geometry_tolerance))
        conn.commit()
        print("  Change detection procedure executed.")

        # Fetch newly detected changes
        cursor.execute("SELECT * FROM detected_changes WHERE change_timestamp > (NOW() - INTERVAL 5 MINUTE)")
        new_changes = cursor.fetchall()

        if new_changes:
            print("\n--- NEW DETECTED CHANGES ---")
            for change in new_changes:
                print(f"  ID: {change[0]}, Feature ID: {change[2]}, Type: {change[4]}, Severity: {change[5]}")
                print(f"    Details: {change[6]}, Location: {change[7]}")
        else:
            print("  No new changes detected in the last 5 minutes.")

    except mariadb.Error as e:
        print(f"  Error during change detection: {e}")
        conn.rollback()
    finally:
        cursor.close()

if __name__ == '__main__':
    conn = get_db_connection()
    if conn:
        print("Simulating continuous change detection...")
        for i in range(3): # Run a few times
            run_change_detection(conn)
            print(f"\nWaiting 5 seconds before next detection run ({i+1}/3)...")
            time.sleep(5) # Simulate a delay between runs
        conn.close()
    else:
        print("Failed to get database connection.")
