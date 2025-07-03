from stable_baselines3 import PPO
from istio_env import IstioEnv
import time

model = PPO.load("round4/ppo_istio")
env = IstioEnv()

state = env.reset()

for _ in range (100):  
    action, _ = model.predict(state)
    state, reward, done, _ = env.step(action)
    
    print(f"Action: {action}, Reward: {reward}")
    
    # Wait for environment stabilization
    time.sleep(30)  # Update interval, adjust based on practical stability
