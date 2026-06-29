from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)


class Config:
    SECRET_KEY = "hr-personnel-system-secret-key"
    DB_DRIVER = os.getenv("DB_DRIVER", "sqlite")
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "hr_personnel")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
        if DB_DRIVER == "mysql"
        else f"sqlite:///{INSTANCE_DIR / 'hr_personnel.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
