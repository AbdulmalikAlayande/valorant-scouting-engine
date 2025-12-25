import os
from environs import Env

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env = Env()

env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_path):
	env.read_env(env_path)
