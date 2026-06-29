from __future__ import annotations

import os
from pathlib import Path

from app import create_app
from extensions import Base, SessionLocal, db
from models import Course, Department, Employee, Patent, Publication, ResearchProject, TeachingAssignment, User
from seed_data import seed_database


def reset_demo_database() -> None:
    os.environ["DB_DRIVER"] = "sqlite"
    app = create_app()
    with app.app_context():
        SessionLocal.remove()
        for model in [User, TeachingAssignment, Publication, Patent, ResearchProject, Course, Employee, Department]:
            db.session.query(model).delete()
        db.session.commit()
        seed_database(db)


if __name__ == "__main__":
    reset_demo_database()
    print("演示数据库已重建完成。")
