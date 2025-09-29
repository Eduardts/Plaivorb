# Plaivorb: Galera Cluster Deployment Notes

Plaivorb is designed to leverage MariaDB's advanced features, including the high availability and real-time consistency offered by a MariaDB Galera Cluster. While a full multi-node Galera deployment is beyond the scope of this hackathon's immediate reference implementation, this document outlines how Plaivorb benefits from and is compatible with such an architecture.

## Why Galera Cluster for Plaivorb?

Plaivorb's core functionality—real-time geo-semantic change detection—requires both high availability and strong data consistency.
*   **High Availability:** Continuous monitoring systems cannot afford downtime. Galera Cluster provides active-active multi-master replication, meaning if one node fails, others can immediately take over, ensuring uninterrupted service for data ingestion, processing, and change detection.
*   **Real-time Consistency:** For accurate change detection, all nodes in the cluster must have the same, up-to-date view of the data. Galera's synchronous replication ensures "virtually synchronous" data consistency across all nodes, preventing stale reads that could lead to missed or false-positive change detections. This is crucial when comparing current and previous states of geospatial features.
*   **Scalability for Reads/Writes:** As the volume of geo-semantic data increases, Galera allows for scaling out read operations across multiple nodes. While write operations are still globally ordered, the multi-master nature can distribute write load across nodes more effectively than traditional primary-replica setups.

## Galera Cluster Integration with Plaivorb

Plaivorb's design inherently supports a Galera Cluster backend due to its reliance on standard MariaDB SQL functionalities and careful handling of potential replication nuances.

### Data Types and Replication
*   **GEOMETRY / SPATIAL:** MariaDB's spatial data types and functions are fully compatible with Galera Cluster. Spatial indexes are replicated like any other index.
*   **VECTOR:** The `VECTOR` data type is a standard MariaDB feature. Operations involving `VECTOR_DISTANCE` and storage of `VECTOR` columns will replicate seamlessly across Galera nodes.
*   **Temporal Tables (`WITH SYSTEM VERSIONING`):** System-versioned temporal tables (used in `geo_features`) function correctly within a Galera Cluster. Changes to the current table and additions to the history table are replicated, maintaining the temporal history consistently across all nodes.
*   **ColumnStore:** MariaDB ColumnStore is an analytical engine and typically runs as a separate distributed system or on a dedicated node, integrated via a federated table or by directly querying the ColumnStore nodes. For high availability of ColumnStore itself, a separate ColumnStore cluster would be deployed. The `historical_geo_summary` table in Plaivorb would interact with ColumnStore as a backend for large-scale analytical queries, complementing the real-time detection on the transactional (InnoDB/Galera) part.

### Application Compatibility
*   Plaivorb's Python scripts (`ingest_data.py`, `semantic_processor.py`, `change_detector.py`) use the standard `mariadb-connector-python`. This connector can be configured to connect to any node in a Galera Cluster. For optimal performance and failover, a load balancer (e.g., ProxySQL, MaxScale) is typically placed in front of the Galera Cluster, and the application connects to the load balancer's virtual IP.
*   Stored Procedures (`DetectFeatureChange`, `ProcessAllFeaturesForChangeDetection`): These SQL routines execute entirely within the database and are replicated reliably across the cluster, ensuring that the change detection logic is consistent regardless of which node executes them.

## Deployment Considerations for Plaivorb on Galera Cluster

If deploying Plaivorb with a full Galera Cluster, consider the following:

1.  **Load Balancer:** Implement a load balancer (e.g., ProxySQL, MariaDB MaxScale) to manage connections from Plaivorb's Python application to the Galera nodes. This provides automatic failover and load distribution.
2.  **Node Count:** A minimum of three nodes is recommended for a robust Galera Cluster to avoid split-brain scenarios and ensure quorum.
3.  **Network Latency:** Galera's synchronous nature means network latency between nodes can impact performance. Nodes should ideally be in the same data center or region.
4.  **Schema Management:** Schema changes in Galera are handled using Total Order Isolation (TOI) or Rolling Schema Upgrade (RSU) methods. For `ALTER TABLE` statements (like adding `WITH SYSTEM VERSIONING`), ensure they are compatible with Galera's operational model.
5.  **Large Transactions:** Very large transactions (e.g., bulk inserts of millions of geospatial features) can be problematic in a synchronous replication environment, as they must commit on all nodes. Batching inserts and processing data in smaller chunks is a good practice for Plaivorb's ingestion pipeline.
6.  **Monitoring:** Robust monitoring of the Galera Cluster (e.g., `wsrep_cluster_size`, `wsrep_local_state_comment`) is essential to ensure health and consistency.

By architecting Plaivorb with these considerations in mind, it forms a resilient, highly available, and consistent solution for real-time geo-semantic change detection that fully leverages MariaDB Galera Cluster.
