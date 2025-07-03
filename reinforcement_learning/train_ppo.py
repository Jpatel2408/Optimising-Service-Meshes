from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from istio_env import IstioEnv
from reward_logger import RewardLogger

env = make_vec_env(IstioEnv, n_envs=1)

callback = RewardLogger(log_path="reward_log.csv")
model = PPO("MlpPolicy", env, verbose=1, n_steps=64)
model.learn(total_timesteps=512, callback=callback)  
model.save("ppo_istio")
