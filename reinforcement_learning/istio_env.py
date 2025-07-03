import gym
import numpy as np
from gym import spaces
from collect_metrics import fetch_live_metrics
from apply_config import apply_istio_config
import time 

METRIC_KEYS = [
            "latency_p99_ms", "latency_spread", "error_rate_5xx", "envoy_cpu_cores",
            "rps_user", "success_rate"
        ]

class IstioEnv(gym.Env):
   
    def __init__(self):
        super(IstioEnv, self).__init__()

        self.action_space = spaces.Box(low=0, high=1, shape=(5,), dtype=np.float32)

        
        self.observation_space = spaces.Box(
            low=np.array([0.0] * 8), high=np.array([np.inf] * 8), dtype=np.float32
        )
        
        self.log_file = "rl_trace.csv"
        with open(self.log_file, "w") as f:
            f.write("action_1,action_2,action_3,action_4,action_5,timeout_sec,http2MaxRequests,http1MaxPendingRequests,retry_attempts,consecutive5xxErrors,reward," +",".join(METRIC_KEYS) + "\n")
            # f.write("timeout_sec,http2MaxRequests,http1MaxPendingRequests,retry_attempts,consecutive5xxErrors,reward," +",".join(METRIC_KEYS) + "\n")  

    def seed(self, seed=None):
        np.random.seed(seed)

    
    def step(self, action):
        config = {
            "timeout_sec": round(1.0 + action[0] * 2.0, 2),                     # 1 to 3 sec
            "http2MaxRequests": int(100 + action[1] * 400),                     # 100 to 500
            "http1MaxPendingRequests": int(50 + action[2] * 450),              # 50 to 500
            "retry_attempts": int(action[3] * 5),                               # 0 to 5
            "consecutive5xxErrors": int(1 + action[4] * 9)                      # 1 to 10
        }
        print(f"Applying Istio config: {config}")
        apply_istio_config(config)
        time.sleep(20)

        metrics = fetch_live_metrics()

        state = np.array([
            metrics["latency_p99_ms"],
            metrics["bandwidth_per_request"],
            metrics["outbond_bandwidth"],
            metrics["inbond_bandwidth"],
            metrics["envoy_mem_bytes"],
            metrics["latency_spread"],
            metrics["requests_per_core"],
            metrics["memory_per_request"]
        ])
        state = np.nan_to_num(state, nan=0.0, posinf=0.0, neginf=0.0)
        # Define reward (negative weighted latency/error + positive throughput)
        reward = (
            (1 - metrics["latency_p99_ms"] / 60000) * 0.25 +
            (1 - metrics["error_rate_5xx"] / 1.0) * 0.25 +
            (1 - metrics["latency_spread"] / 60000) * 0.25 +
            (1 - metrics["envoy_cpu_cores"] / 2.0) * 0.25
        )
        reward = 0.0 if np.isnan(reward) or np.isinf(reward) else reward
        done = False
        info = {}
        print(f"Reward: {reward}")
        action_str = ",".join(map(str, action)) 

        with open(self.log_file, "a") as f:
            f.write(f"{action_str},"
                    f"{config['timeout_sec']},{config['http2MaxRequests']},{config['http1MaxPendingRequests']},"
                    f"{config['retry_attempts']},{config['consecutive5xxErrors']},{reward}," +
                    ",".join(str(metrics.get(k, 0.0)) for k in METRIC_KEYS) + "\n")
        return state, reward, done, info

    def reset(self):
        metrics = fetch_live_metrics()
        state = np.array([
            metrics["latency_p99_ms"],
            metrics["bandwidth_per_request"],
            metrics["outbond_bandwidth"],
            metrics["inbond_bandwidth"],
            metrics["envoy_mem_bytes"],
            metrics["latency_spread"],
            metrics["requests_per_core"],
            metrics["memory_per_request"]
        ])
        return np.nan_to_num(state, nan=0.0, posinf=0.0, neginf=0.0)
