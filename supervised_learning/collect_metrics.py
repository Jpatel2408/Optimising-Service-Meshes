from prometheus_api_client import PrometheusConnect
import time

prom = PrometheusConnect(url="http://192.168.0.150:32479", disable_ssl=True)

METRICS = {
    "rps_user": 'sum(rate(istio_requests_total{connection_security_policy="none"}[30s]))',
    "avg_latency_ms": '''
        sum(rate(istio_request_duration_milliseconds_sum{connection_security_policy="none"}[30s]))
        /
        sum(rate(istio_request_duration_milliseconds_count{connection_security_policy="none"}[30s]))
    ''',
    "latency_p99_ms": 'histogram_quantile(0.99, sum(rate(istio_request_duration_milliseconds_bucket{connection_security_policy="none"}[30s])) by (le))',
    "latency_p95_ms": 'histogram_quantile(0.95, sum(rate(istio_request_duration_milliseconds_bucket{connection_security_policy="none"}[30s])) by (le))',
    "latency_p50_ms": 'histogram_quantile(0.50, sum(rate(istio_request_duration_milliseconds_bucket{connection_security_policy="none"}[30s])) by (le))',

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

    "inbond_bandwidth": 'sum(rate(istio_request_bytes_sum{connection_security_policy="none"}[5m]))',
    "outbond_bandwidth": 'sum(rate(istio_response_bytes_sum{connection_security_policy="none"}[5m]))',
    "retries_per_sec": 'sum(rate(envoy_cluster_upstream_rq_retry[30s]))',
    "envoy_cpu_cores": 'sum(rate(container_cpu_usage_seconds_total{container="istio-proxy"}[30s]))',
    "envoy_mem_bytes": 'sum(container_memory_usage_bytes{container="istio-proxy"})',
    "upstream_rq_pending_overflow": 'sum(rate(envoy_cluster_upstream_rq_pending_overflow[30s]))',
}

def fetch_live_metrics():
    raw = {}

    # Step 1: Query Prometheus for base metrics
    for key, query in METRICS.items():
        try:
            res = prom.custom_query(query)
            raw[key] = float(res[0]["value"][1]) if res else None
        except Exception as e:
            print(f"⚠️ Failed to fetch {key}: {e}")
            raw[key] = None

    # Step 2: Add derived features (calculate only if dependencies exist)
    try:
        if raw["rps_user"] and raw["envoy_cpu_cores"]:
            raw["requests_per_core"] = raw["rps_user"] / raw["envoy_cpu_cores"]
        else:
            raw["requests_per_core"] = None

        if raw["rps_user"] and raw["inbond_bandwidth"] is not None and raw["outbond_bandwidth"] is not None:
            raw["bandwidth_per_request"] = (raw["inbond_bandwidth"] + raw["outbond_bandwidth"]) / raw["rps_user"]
        else:
            raw["bandwidth_per_request"] = None

        if raw["rps_user"] and raw["envoy_mem_bytes"]:
            raw["memory_per_request"] = raw["envoy_mem_bytes"] / raw["rps_user"]
        else:
            raw["memory_per_request"] = None

        if raw["latency_p99_ms"] is not None and raw["latency_p50_ms"] is not None:
            raw["latency_spread"] = raw["latency_p99_ms"] - raw["latency_p50_ms"]
        else:
            raw["latency_spread"] = None
    except Exception as e:
        print(f"⚠️ Error computing derived features: {e}")

    return raw

print(fetch_live_metrics())