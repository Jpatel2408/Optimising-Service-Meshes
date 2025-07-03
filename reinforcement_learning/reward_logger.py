from stable_baselines3.common.callbacks import BaseCallback
import os

class RewardLogger(BaseCallback):
    def __init__(self, log_path="reward_log.csv", verbose=0):
        super().__init__(verbose)
        self.log_path = log_path
        self.rewards = []

    def _on_step(self) -> bool:
        if 'rewards' in self.locals:
            reward = self.locals['rewards'][0]
            self.rewards.append((self.num_timesteps, reward))
            with open(self.log_path, "a") as f:
                f.write(f"{self.num_timesteps},{reward}\n")
        return True
