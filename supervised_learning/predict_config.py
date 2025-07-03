from apply_config import apply_istio_config, fetch_current_config
from collect_metrics import fetch_live_metrics
import yaml
import joblib
import pandas as pd

# Load individual models (adjust paths if needed)
timeout_model = joblib.load("models/timeout_model.pkl")
http2_model = joblib.load("models/http2_model.pkl")
http1_model = joblib.load("models/http1_model.pkl")

input_features = [
    "latency_p99_ms", "bandwidth_per_request", "outbond_bandwidth",
    "inbond_bandwidth", "envoy_mem_bytes", "latency_spread",
    "rps_user", "memory_per_request"
]

def predict_config(metrics_dict):
    # Filter only selected input features
    filtered = {key: metrics_dict.get(key, None) for key in input_features}
    df = pd.DataFrame([filtered])

    predictions = {}

    try:
        predictions["timeout_sec"] = round(float(timeout_model.predict(df)[0]), 2)
    except Exception as e:
        print(f"⚠️ Failed to predict timeout_sec: {e}")

    try:
        predictions["http2MaxRequests"] = int(http2_model.predict(df)[0])
    except Exception as e:
        print(f"⚠️ Failed to predict http2MaxRequests: {e}")

    try:
        predictions["http1MaxPendingRequests"] = int(http1_model.predict(df)[0])
    except Exception as e:
        print(f"⚠️ Failed to predict http1MaxPendingRequests: {e}")

    return predictions

if __name__ == "__main__":

    metrics = fetch_live_metrics()
    old_config = fetch_current_config()
    result = predict_config(metrics)
    print("Predicted Istio Config:")
    print(result)





#     # print("🔍 Fetching current config...")
#     # old_config = fetch_current_config()


#     new_config_from+model = {
#         "timeout_sec": 2,
#         "http2MaxRequests": 200,
#         "http1MaxPendingRequests": 100
 
#     }

#     print("\n⚙️ Applying new config:")
#     print(yaml.dump(new_config, default_flow_style=False))

#     apply_istio_config(new_config)

#     print("\n🔍 Re-fetching config after patch:")
#     fetch_current_config()