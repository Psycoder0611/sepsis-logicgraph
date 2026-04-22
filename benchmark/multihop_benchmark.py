import time
import snowflake.connector
from neo4j import GraphDatabase
import pandas as pd

# ==========================================
# 1. CREDENTIALS AND SETUP
# ==========================================
SF_USER = 'POUSHALI.DEBPURKAYASTHA'
SF_PASSWORD = 'Pogoislove0220'
SF_ACCOUNT = 'czfjtep-beb38705'
SF_WAREHOUSE = 'COMPUTE_WH'
SF_DATABASE = 'SEPSIS_LOGICGRAPH'
SF_SCHEMA = 'SILVER'

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "sepsis123"

# ==========================================
# 2. THE TARGET COHORTS (Reduced max since SQL will bottleneck)
# ==========================================
COHORT_SIZES = [100, 500, 1000, 5000]

# ==========================================
# 3. MULTI-HOP QUERIES (Shared Critical Profile)
# ==========================================
# Neo4j Cypher Query
CYPHER_MULTIHOP = """
MATCH (p1:Patient)-[:ADMITTED_TO]->(i1)-[:HAS_INFECTION]->(d1:InfectionDiagnosis)
MATCH (p2:Patient)-[:ADMITTED_TO]->(i2)-[:HAS_INFECTION]->(d2:InfectionDiagnosis)
WHERE p1.subject_id IN $subject_list AND p2.subject_id IN $subject_list
  AND toInteger(p1.subject_id) > toInteger(p2.subject_id)
  AND d1.icd_code = d2.icd_code
MATCH (i1)-[:HAS_LAB_EVENT]->(l1:LabEvent), (i2)-[:HAS_LAB_EVENT]->(l2:LabEvent)
WHERE l1.sofa_score = 4 
  AND l2.sofa_score = 4 
RETURN COUNT(DISTINCT p1.subject_id) AS Matched_Patients
"""

# Snowflake SQL Query 
SQL_MULTIHOP = """
SELECT COUNT(DISTINCT c1.SUBJECT_ID) AS Matched_Patients
FROM SEPSIS_LOGICGRAPH.SILVER.ICU_COHORT_CLEAN c1
JOIN SEPSIS_LOGICGRAPH.SILVER.INFECTION_DIAGNOSIS_CLEAN inf1 
    ON c1.HADM_ID = inf1.HADM_ID
JOIN SEPSIS_LOGICGRAPH.SILVER.ICU_COHORT_CLEAN c2 
    ON c1.SUBJECT_ID > c2.SUBJECT_ID
JOIN SEPSIS_LOGICGRAPH.SILVER.INFECTION_DIAGNOSIS_CLEAN inf2 
    ON c2.HADM_ID = inf2.HADM_ID 
    AND inf1.ICD_CODE = inf2.ICD_CODE
JOIN SEPSIS_LOGICGRAPH.GOLD.SOFA_LAB_FACT l1 
    ON c1.HADM_ID = l1.HADM_ID
JOIN SEPSIS_LOGICGRAPH.GOLD.SOFA_LAB_FACT l2 
    ON c2.HADM_ID = l2.HADM_ID 
WHERE c1.SUBJECT_ID IN ({0}) AND c2.SUBJECT_ID IN ({0})
  AND l1.SOFA_SCORE = 4 
  AND l2.SOFA_SCORE = 4;
"""

def main():
    print("Connecting to Snowflake...")
    sf_conn = snowflake.connector.connect(
        user=SF_USER,
        password=SF_PASSWORD,
        account=SF_ACCOUNT,
        warehouse=SF_WAREHOUSE,
        database=SF_DATABASE,
        schema=SF_SCHEMA
    )
    sf_cursor = sf_conn.cursor()

    print("Connecting to Neo4j...")
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    sf_cursor.execute("SELECT DISTINCT SUBJECT_ID FROM SEPSIS_LOGICGRAPH.SILVER.ICU_COHORT_CLEAN LIMIT 5000")
    all_subjects = [str(row[0]) for row in sf_cursor.fetchall()]
    
    results_log = []

    for size in COHORT_SIZES:
        print(f"\n--- Running MULTI-HOP Benchmark for Cohort Size: {size} ---")
        test_subjects = all_subjects[:size]
        
        # ---------------------------
        # NEO4J BENCHMARK
        # ---------------------------
        start_time = time.time()
        neo4j_count = 0
        with neo4j_driver.session() as session:
            result = session.run(CYPHER_MULTIHOP, subject_list=test_subjects)
            record = result.single()
            neo4j_count = record["Matched_Patients"] if record else 0
        neo4j_time = time.time() - start_time
        print(f"Neo4j: Found {neo4j_count} connections in {neo4j_time:.4f} seconds.")

        # ---------------------------
        # SNOWFLAKE BENCHMARK
        # ---------------------------
        formatted_list = ",".join([f"'{sub}'" for sub in test_subjects])
        filled_sql = SQL_MULTIHOP.format(formatted_list)
        
        start_time = time.time()
        sf_cursor.execute(filled_sql)
        sf_data = sf_cursor.fetchone()
        sf_count = sf_data[0] if sf_data else 0
        sf_time = time.time() - start_time
        print(f"Snowflake: Found {sf_count} connections in {sf_time:.4f} seconds.")
        
        results_log.append({
            "Cohort_Size": size,
            "Neo4j_Time_sec": neo4j_time,
            "Snowflake_Time_sec": sf_time,
            "Connections_Found": neo4j_count
        })

    df = pd.DataFrame(results_log)
    df.to_csv("multihop_benchmark_results.csv", index=False)
    print("\nBenchmark complete! Results saved to 'multihop_benchmark_results.csv'")

    sf_cursor.close()
    sf_conn.close()
    neo4j_driver.close()

if __name__ == "__main__":
    main()
