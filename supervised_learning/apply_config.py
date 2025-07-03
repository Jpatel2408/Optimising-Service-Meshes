from kubernetes import client, config
import yaml

def fetch_current_config(namespace="boutique", vs_name="frontend", dr_name="frontend"):
    config.load_kube_config()
    custom_api = client.CustomObjectsApi()

    configs = {}

    try:
        # --- Fetch VirtualService ---
        vs = custom_api.get_namespaced_custom_object(
            group="networking.istio.io", version="v1beta1",
            namespace=namespace, plural="virtualservices", name=vs_name
        )
        http_settings = vs.get("spec", {}).get("http", [{}])[0]
        configs["timeout_sec"] = float(http_settings.get("timeout", "3s").replace("s", ""))
        # configs["retry_attempts"] = http_settings.get("retries", {}).get("attempts", 0)

        # --- Fetch DestinationRule ---
        dr = custom_api.get_namespaced_custom_object(
            group="networking.istio.io", version="v1beta1",
            namespace=namespace, plural="destinationrules", name=dr_name
        )
        tp = dr.get("spec", {}).get("trafficPolicy", {})
        configs["http2MaxRequests"] = tp.get("connectionPool", {}).get("http", {}).get("http2MaxRequests")
        configs["http1MaxPendingRequests"] = tp.get("connectionPool", {}).get("http", {}).get("http1MaxPendingRequests")
        # configs["consecutive5xxErrors"] = tp.get("outlierDetection", {}).get("consecutive5xxErrors")

        print("Current Istio Config:")
        print(configs)

    except Exception as e:
        print(f"❌ Failed to fetch Istio config: {e}")

    return configs


def apply_istio_config(configs, namespace="boutique", vs_name="frontend", dr_name="frontend"):
    config.load_kube_config()
    custom_api = client.CustomObjectsApi()

    try:
        # --- Fetch existing VirtualService ---
        vs = custom_api.get_namespaced_custom_object(
            group="networking.istio.io", version="v1beta1",
            namespace=namespace, plural="virtualservices", name=vs_name
        )
        http_block = vs["spec"]["http"][0]

        if "timeout_sec" in configs:
            http_block["timeout"] = f"{configs['timeout_sec']}s"
        if "retry_attempts" in configs:
            http_block["retries"] = {"attempts": configs["retry_attempts"]}

        vs_patch = {
            "spec": {
                "http": [http_block]
            }
        }

        custom_api.patch_namespaced_custom_object(
            group="networking.istio.io", version="v1beta1",
            namespace=namespace, plural="virtualservices",
            name=vs_name, body=vs_patch
        )
        print("✅ Patched VirtualService")

        # --- Fetch existing DestinationRule ---
        dr = custom_api.get_namespaced_custom_object(
            group="networking.istio.io", version="v1beta1",
            namespace=namespace, plural="destinationrules", name=dr_name
        )
        tp = dr.get("spec", {}).get("trafficPolicy", {})
        http_pool = tp.get("connectionPool", {}).get("http", {})

        if "http2MaxRequests" in configs:
            http_pool["http2MaxRequests"] = configs["http2MaxRequests"]
        if "http1MaxPendingRequests" in configs:
            http_pool["http1MaxPendingRequests"] = configs["http1MaxPendingRequests"]

        if "connectionPool" not in tp:
            tp["connectionPool"] = {}
        tp["connectionPool"]["http"] = http_pool

        if "consecutive5xxErrors" in configs:
            tp["outlierDetection"] = tp.get("outlierDetection", {})
            tp["outlierDetection"]["consecutive5xxErrors"] = configs["consecutive5xxErrors"]

        dr_patch = {
            "spec": {
                "trafficPolicy": tp
            }
        }

        custom_api.patch_namespaced_custom_object(
            group="networking.istio.io", version="v1beta1",
            namespace=namespace, plural="destinationrules",
            name=dr_name, body=dr_patch
        )
        print("✅ Patched DestinationRule")

    except Exception as e:
        print(f"❌ Failed to apply Istio config: {e}")


