import pandas as pd
import numpy as np

# Load datasets
stable_df = pd.read_csv("../result/time-series-data/t2-stable.csv")
# stepup_df = pd.read_csv("../result/time-series-data/t2-stepup.csv")

# Enrichment Function
def enrich_dataset(df, workload_label):
    df = df.copy()
    df['requests_per_core'] = df['rps_user'] / df['envoy_cpu_cores'].replace(0, np.nan)
    df['bandwidth_per_request'] = (df['inbond_bandwidth'] + df['outbond_bandwidth']) / df['rps_user'].replace(0, np.nan)
    df['memory_per_request'] = df['envoy_mem_bytes'] / df['rps_user'].replace(0, np.nan)
    df['latency_spread'] = df['latency_p99_ms'] - df['latency_p50_ms']
    df['workload_type'] = workload_label
    return df

# Apply enrichment
stable_enriched = enrich_dataset(stable_df, "Stable Load")
# stepup_enriched = enrich_dataset(stepup_df, "Ramp-up Load")

# Combine datasets
# combined_df = pd.concat([stable_enriched, stepup_enriched], ignore_index=True)

# Save to CSV
stable_enriched.to_csv("../result/time-series-data/t2_stable_enriched.csv", index=False)
# print("Combined enriched dataset saved as 't2_combined_enriched.csv'")