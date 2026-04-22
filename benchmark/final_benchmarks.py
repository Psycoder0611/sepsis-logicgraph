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

COHORT_SIZES = [100, 500, 1000, 5000]

# ==========================================
# TEST 1: THE ANTI-PATTERN (Missing Data)
# ==========================================
CYPHER_ANTI = """
MATCH (p:Patient)-[:ADMITTED_TO]->(i:ICUStay)-[:HAS_INFECTION]->(d:InfectionDiagnosis)
WHERE p.subject_id IN $subject_list
  AND NOT (i)-[:HAS_LAB_EVENT]->()
RETURN COUNT(p.subject_id) AS Missing_Labs
"""

SQL_ANTI = """
SELECT COUNT(DISTINCT c.SUBJECT_ID) AS Missing_Labs
FROM SEPSIS_LOGICGRAPH.SILVER.ICU_COHORT_CLEAN c
JOIN SEPSIS_LOGICGRAPH.SILVER.INFECTION_DIAGNOSIS_CLEAN inf 
    ON c.HADM_ID = inf.HADM_ID
LEFT JOIN SEPSIS_LOGICGRAPH.GOLD.SOFA_LAB_FACT l 
    ON c.HADM_ID = l.HADM_ID
WHERE c.SUBJECT_ID IN ({0})
  AND l.HADM_ID IS NULL;
"""

# ==========================================
# TEST 2: GLOBAL AGGREGATION (OLAP Grouping)
# ==========================================
CYPHER_AGG = """
MATCH (p:Patient)-[:ADMITTED_TO]->(i:ICUStay)-[:HAS_LAB_EVENT]->(l:LabEvent)
WHERE p.subject_id IN $subject_list
RETURN p.gender AS Gender, COUNT(l) AS Total_Labs, AVG(l.sofa_score) AS Average_SOFA
ORDER BY Gender
"""

SQL_AGG = """
SELECT c.GENDER, COUNT(l.ITEMID) AS Total_Labs, AVG(l.SOFA_SCORE) AS Average_SOFA
FROM SEPSIS_LOGICGRAPH.SILVER.ICU_COHORT_CLEAN c
JOIN SEPSIS_LOGICGRAPH.GOLD.SOFA_LAB_FACT l 
    ON c.HADM_ID = l.HADM_ID
WHERE c.SUBJECT_ID IN ({0})
GROUP BY c.GENDER
ORDER BY c.GENDER;
"""

def main():
    print("Connecting to Snowflake...")
    sf_conn = snowflake.connector.connect(
        user=SF_USER, password=SF_PASSWORD, account=SF_ACCOUNT,
        warehouse=SF_WAREHOUSE, database=SF_DATABASE, schema=SF_SCHEMA
    )
    sf_cursor = sf_conn.cursor()

    print("Connecting to Neo4j...")
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    sf_cursor.execute("SELECT DISTINCT SUBJECT_ID FROM SEPSIS_LOGICGRAPH.SILVER.ICU_COHORT_CLEAN LIMIT 5000")
    all_subjects = [str(row[0]) for row in sf_cursor.fetchall()]
    
    results_log = []

    for size in COHORT_SIZES:
        print(f"\n==========================================")
        print(f"   RUNNING COHORT SIZE: {size}")
        print(f"==========================================")
        test_subjects = all_subjects[:size]
        formatted_list = ",".join([f"'{sub}'" for sub in test_subjects])
        
        # ------------------------------------------------
        # 1. ANTI-PATTERN TEST
        # ------------------------------------------------
        print("--- Test 1: The Anti-Pattern (Missing Data) ---")
        
        # Neo4j
        start_time = time.time()
        with neo4j_driver.session() as session:
            res = session.run(CYPHER_ANTI, subject_list=test_subjects)
            n_anti_count = res.single()[0]
        n_anti_time = time.time() - start_time
        print(f"Neo4j: Found {n_anti_count} missing labs in {n_anti_time:.4f} seconds.")

        # Snowflake
        start_time = time.time()
        sf_cursor.execute(SQL_ANTI.format(formatted_list))
        s_anti_count = sf_cursor.fetchone()[0]
        s_anti_time = time.time() - start_time
        print(f"Snowflake: Found {s_anti_count} missing labs in {s_anti_time:.4f} seconds.")

        # ------------------------------------------------
        # 2. GLOBAL AGGREGATION TEST
        # ------------------------------------------------
        print("\n--- Test 2: Global Aggregation (OLAP Math) ---")
        
        # Neo4j
        start_time = time.time()
        with neo4j_driver.session() as session:
            res = session.run(CYPHER_AGG, subject_list=test_subjects)
            n_agg_count = len(list(res)) # Just counting how many grouping rows returned
        n_agg_time = time.time() - start_time
        print(f"Neo4j: Aggregated data in {n_agg_time:.4f} seconds.")

        # Snowflake
        start_time = time.time()
        sf_cursor.execute(SQL_AGG.format(formatted_list))
        s_agg_count = len(sf_cursor.fetchall())
        s_agg_time = time.time() - start_time
        print(f"Snowflake: Aggregated data in {s_agg_time:.4f} seconds.")

        results_log.append({
            "Cohort_Size": size,
            "AntiPattern_Neo4j_sec": n_anti_time,
            "AntiPattern_Snowflake_sec": s_anti_time,
            "Aggregation_Neo4j_sec": n_agg_time,
            "Aggregation_Snowflake_sec": s_agg_time,
        })

    df = pd.DataFrame(results_log)
    df.to_csv("final_architecture_benchmarks.csv", index=False)
    print("\nBenchmark complete! Results saved to 'final_architecture_benchmarks.csv'")

    sf_cursor.close()
    sf_conn.close()
    neo4j_driver.close()

if __name__ == "__main__":
    main()
