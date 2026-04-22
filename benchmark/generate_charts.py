import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set visual style
sns.set_theme(style="whitegrid")

def plot_comparison(df, neo4j_col, snowflake_col, title, filename):
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(df['Cohort_Size']))
    width = 0.35
    
    # Replaced colors to be highly distinct: Orange for Neo4j, Cyan-Blue for Snowflake
    rects1 = ax.bar(x - width/2, df[neo4j_col], width, label='Neo4j (Knowledge Graph)', color='#FF8C00')
    rects2 = ax.bar(x + width/2, df[snowflake_col], width, label='Snowflake (Data Warehouse)', color='#29B5E8')
    
    ax.set_ylabel('Execution Time (Seconds)', fontsize=12, fontweight='bold')
    ax.set_xlabel('Cohort Size (Number of Patients)', fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(df['Cohort_Size'])
    ax.legend(fontsize=12)
    
    # Add numerical labels on top of bars
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.2f}s',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=10)
                        
    autolabel(rects1)
    autolabel(rects2)
    
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.close()

try:
    print("Generating charts...")
    
    # 1. Chronological Timeline
    df1 = pd.read_csv('benchmark_results.csv')
    plot_comparison(df1, 'Neo4j_Time_sec', 'Snowflake_Time_sec', 
                   'Benchmark 1: Chronological Patient Pathway (Sepsis-3 24hr Window)', 
                   'chart_1_chronological.png')

    # 2. Multi-hop (Cross-patient)
    df2 = pd.read_csv('multihop_benchmark_results.csv')
    plot_comparison(df2, 'Neo4j_Time_sec', 'Snowflake_Time_sec', 
                   'Benchmark 2: Cross-Patient Text Matching (Graph Database Weakness)', 
                   'chart_2_multihop.png')

    # 3. Missing Data / Anti-Pattern
    df3 = pd.read_csv('final_architecture_benchmarks.csv')
    plot_comparison(df3, 'AntiPattern_Neo4j_sec', 'AntiPattern_Snowflake_sec', 
                   'Benchmark 3: Anti-Pattern Detection (Finding Missing Medical Data)', 
                   'chart_3_missing_data.png')
    
    # 4. Global OLAP Aggregation
    plot_comparison(df3, 'Aggregation_Neo4j_sec', 'Aggregation_Snowflake_sec', 
                   'Benchmark 4: Global Data Aggregation (OLAP Math)', 
                   'chart_4_aggregation.png')

    print("Success! 4 high-resolution PNG charts have been created.")
except Exception as e:
    print(f"Error generating charts: {e}")
