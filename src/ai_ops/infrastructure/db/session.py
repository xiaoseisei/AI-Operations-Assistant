from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def create_session_factory(
    database_url: str = "sqlite:///./.runtime/app.sqlite3",
) -> sessionmaker[Session]:
    engine = create_engine(database_url)
    return sessionmaker(bind=engine, expire_on_commit=False)
