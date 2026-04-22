import time
import snowflake.connector
from neo4j import GraphDatabase
import pandas as pd

# ==========================================
# 1. CREDENTIALS AND SETUP
# ==========================================
# Replace these with your actual Snowflake login details
SF_USER = 'POUSHALI.DEBPURKAYASTHA'
SF_PASSWORD = 'Pogoislove0220'
SF_ACCOUNT = 'czfjtep-beb38705'
SF_WAREHOUSE = 'COMPUTE_WH'
SF_DATABASE = 'SEPSIS_LOGICGRAPH'
SF_SCHEMA = 'SILVER'

# Neo4j Credentials (default localhost)
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "sepsis123"

# ==========================================
# 2. THE TARGET COHORTS
# ==========================================
COHORT_SIZES = [100, 500, 1000, 5000]

# ==========================================
# 3. QUERIES
# ==========================================
# Neo4j Cypher Query (Filters by specific subjects)
CYPHER_QUERY = """
MATCH (p:Patient)-[:ADMITTED_TO]->(i:ICUStay)-[:HAS_INFECTION]->(d:InfectionDiagnosis)
WHERE p.subject_id IN $subject_list
MATCH (i)-[:HAS_LAB_EVENT]->(l:LabEvent)
WHERE l.charttime >= i.intime AND l.charttime <= i.intime + duration('P1D')
WITH p, i, sum(l.sofa_score) as Total_24hr_SOFA
WHERE Total_24hr_SOFA >= 2
RETURN p.subject_id, i.stay_id, Total_24hr_SOFA
"""

# Snowflake SQL Query (Filters by specific subjects)
SQL_QUERY = """
SELECT 
    c.SUBJECT_ID, 
    c.STAY_ID, 
    SUM(l.SOFA_SCORE) as Total_24hr_SOFA
FROM SEPSIS_LOGICGRAPH.SILVER.ICU_COHORT_CLEAN c
JOIN SEPSIS_LOGICGRAPH.SILVER.INFECTION_DIAGNOSIS_CLEAN inf 
    ON c.HADM_ID = inf.HADM_ID
JOIN SEPSIS_LOGICGRAPH.GOLD.SOFA_LAB_FACT l 
    ON c.HADM_ID = l.HADM_ID
WHERE c.SUBJECT_ID IN ({})
  AND l.CHARTTIME >= c.INTIME 
  AND l.CHARTTIME <= DATEADD(hour, 24, c.INTIME)
GROUP BY c.SUBJECT_ID, c.STAY_ID
HAVING SUM(l.SOFA_SCORE) >= 2;
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

    # Get a list of 5000 unique patients to act as our test pool
    sf_cursor.execute("SELECT DISTINCT SUBJECT_ID FROM SEPSIS_LOGICGRAPH.SILVER.ICU_COHORT_CLEAN LIMIT 5000")
    all_subjects = [str(row[0]) for row in sf_cursor.fetchall()]
    
    results_log = []

    for size in COHORT_SIZES:
        print(f"\n--- Running Benchmark for Cohort Size: {size} ---")
        test_subjects = all_subjects[:size]
        
        # ---------------------------
        # NEO4J BENCHMARK
        # ---------------------------
        start_time = time.time()
        neo4j_count = 0
        with neo4j_driver.session() as session:
            result = session.run(CYPHER_QUERY, subject_list=test_subjects)
            neo4j_count = len(list(result))
        neo4j_time = time.time() - start_time
        print(f"Neo4j: Found {neo4j_count} sepsis cases in {neo4j_time:.4f} seconds.")

        # ---------------------------
        # SNOWFLAKE BENCHMARK
        # ---------------------------
        # Format the SQL query to insert our list of subject strings
        formatted_list = ",".join([f"'{sub}'" for sub in test_subjects])
        filled_sql = SQL_QUERY.format(formatted_list)
        
        start_time = time.time()
        sf_cursor.execute(filled_sql)
        sf_data = sf_cursor.fetchall()
        sf_count = len(sf_data)
        sf_time = time.time() - start_time
        print(f"Snowflake: Found {sf_count} sepsis cases in {sf_time:.4f} seconds.")

        # Ensure Consistency Metric
        if sf_count != neo4j_count:
            print("WARNING: Data consistency mismatch between databases!")
        
        results_log.append({
            "Cohort_Size": size,
            "Neo4j_Time_sec": neo4j_time,
            "Snowflake_Time_sec": sf_time,
            "Patients_Found": neo4j_count
        })

    # Save to CSV
    df = pd.DataFrame(results_log)
    df.to_csv("benchmark_results.csv", index=False)
    print("\nBenchmark complete! Results saved to 'benchmark_results.csv'")

    sf_cursor.close()
    sf_conn.close()
    neo4j_driver.close()

if __name__ == "__main__":
    main()
