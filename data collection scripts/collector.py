import time
import pandas as pd
from datetime import datetime, timedelta
from prometheus_api_client import PrometheusConnect
from kubernetes import client, config
import os

# --- Setup Clients ---
prom = PrometheusConnect(url="http://192.168.0.150:32479", disable_ssl=True)  # Update if needed
config.load_kube_config()
custom_api = client.CustomObjectsApi()

# --- Top 5 Istio Knobs to Fetch ---
def fetch_istio_configs():
    configs = {
        # VirtualService
        "timeout_sec": None,
        "retry_attempts": None,
        # DestinationRule
        "http2MaxRequests": None,
        "http1MaxPendingRequests": None,
        "consecutive5xxErrors": None,
        
    }

    try:
        # Fetch VirtualService (timeout/retries)
        vs = custom_api.get_namespaced_custom_object(
            group="networking.istio.io", version="v1beta1",
            namespace="boutique", plural="virtualservices", name="frontend"
        )
        http_settings = vs.get("spec", {}).get("http", [{}])[0]
        configs.update({
            "timeout_sec": float(http_settings.get("timeout", "3s").replace('s', '')),
            "retry_attempts": http_settings.get("retries", {}).get("attempts", 0)
        })

        # Fetch DestinationRule (connection pools/outlier detection)
        dr = custom_api.get_namespaced_custom_object(
            group="networking.istio.io", version="v1beta1",
            namespace="boutique", plural="destinationrules", name="frontend"
        )
        tp = dr.get("spec", {}).get("trafficPolicy", {})
        configs.update({
            "http2MaxRequests": tp.get("connectionPool", {}).get("http", {}).get("http2MaxRequests"),
            "http1MaxPendingRequests": tp.get("connectionPool", {}).get("http", {}).get("http1MaxPendingRequests"),
            "consecutive5xxErrors": tp.get("outlierDetection", {}).get("consecutive5xxErrors"),
        })
    except Exception as e:
        print(f"⚠️ Config fetch failed: {e}")

    return configs

# --- Focused Metrics (Aligned with Knobs) ---
METRICS = {
    # User-facing throughput
    "rps_user": 'sum(rate(istio_requests_total{connection_security_policy="none"}[30s]))',
    "avg_latency_ms": '''
        sum(rate(istio_request_duration_milliseconds_sum{connection_security_policy="none"}[30s]))
        /
        sum(rate(istio_request_duration_milliseconds_count{connection_security_policy="none"}[30s]))
    ''',
    # Latency
    "latency_p99_ms": 'histogram_quantile(0.99, sum(rate(istio_request_duration_milliseconds_bucket{connection_security_policy="none"}[30s])) by (le))',
    "latency_p95_ms": 'histogram_quantile(0.95, sum(rate(istio_request_duration_milliseconds_bucket{connection_security_policy="none"}[30s])) by (le))',
    "latency_p50_ms": 'histogram_quantile(0.50, sum(rate(istio_request_duration_milliseconds_bucket{connection_security_policy="none"}[30s])) by (le))',
    
    # Errors/Resilience
    "success_rate": '''
        sum(rate(istio_requests_total{connection_security_policy="none",response_code=~"2.."}[30s]))
        /
        sum(rate(istio_requests_total{connection_security_policy="none"}[30s]))
    ''',
    "error_rate_5xx": '''
        sum(rate(istio_requests_total{connection_security_policy="none",response_code=~"5.."}[30s])) 
        / 
        sum(rate(istio_requests_total{connection_security_policy="none"}[30s]))
    ''',
    "inbond_bandwidth": 'sum(rate(istio_request_bytes_sum{connection_security_policy="none"}[30s]))',
    
    "outbond_bandwidth": 'sum(rate(istio_response_bytes_sum{connection_security_policy="none"}[30s]))',

    "retries_per_sec": 'sum(rate(envoy_cluster_upstream_rq_retry[30s]))',
    
    # System (Istio-Proxy Only)
    "envoy_cpu_cores": 'sum(rate(container_cpu_usage_seconds_total{container="istio-proxy"}[30s]))',
    "envoy_mem_bytes": 'sum(container_memory_usage_bytes{container="istio-proxy"})',

    # Circuit Breaking Events
    "upstream_rq_pending_overflow": 'sum(rate(envoy_cluster_upstream_rq_pending_overflow[30s]))',
}

def scrape_metrics():
    results = {}
    for name, query in METRICS.items():
        try:
            data = prom.custom_query(query)
            results[name] = float(data[0]["value"][1]) if data else None
        except Exception as e:
            print(f"⚠️ Metric {name} failed: {e}")
            results[name] = None
    return results

# --- Main Collector ---
def run_collector(duration_min, interval_sec):
    run_id = f"run_03_{datetime.now().strftime('%H%M%S')}"
    data = []
    
    # Fetch static configs once
    istio_configs = fetch_istio_configs()
    print(f"🔧 Initial Configs: {istio_configs}")

    end_time = datetime.now() + timedelta(minutes=duration_min)
    while datetime.now() < end_time:
        timestamp = datetime.now().strftime("%H:%M:%S")
        row = {"timestamp": timestamp}
        
        # Add metrics
        row.update(scrape_metrics())
        
        # Add configs (same for all rows)
        row.update(istio_configs)
        
        data.append(row)
        print(f"📊 Collected: {timestamp} ")
        time.sleep(interval_sec)
    
    # Save to CSV
    df = pd.DataFrame(data)
    os.makedirs("data", exist_ok=True)
    df.to_csv(f"data/{run_id}.csv", index=False)
    print(f"🔧 Configs: {istio_configs}")
    print(f"💾 Saved to data/{run_id}.csv")

if __name__ == "__main__":
    run_collector(duration_min=10, interval_sec=5)  # Adjust as needed