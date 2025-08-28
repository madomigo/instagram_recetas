import os
from dotenv import load_dotenv


load_dotenv()


class Settings:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "recetas")


settings = Settings()