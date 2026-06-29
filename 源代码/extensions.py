from __future__ import annotations

from sqlalchemy import create_engine, func
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker


Base = declarative_base()
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False))


class DB:
    session = SessionLocal
    func = func

    def init_app(self, app) -> None:
        uri = app.config["SQLALCHEMY_DATABASE_URI"]
        connect_args = {}
        if uri.startswith("sqlite:///"):
            connect_args["check_same_thread"] = False

        engine = create_engine(uri, connect_args=connect_args)
        SessionLocal.configure(bind=engine)
        Base.metadata.bind = engine
        Base.query = SessionLocal.query_property()
        Base.metadata.create_all(bind=engine)

        @app.teardown_appcontext
        def remove_session(exception=None):
            SessionLocal.remove()


db = DB()
