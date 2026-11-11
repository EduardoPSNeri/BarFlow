import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get('BARFLOW_DATA_DIR', str(ROOT / 'data'))).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / 'barflow.db'
engine = create_engine(f'sqlite:///{DB_PATH.as_posix()}', connect_args={'check_same_thread': False, 'timeout': 20})
@event.listens_for(engine, 'connect')
def enable_sqlite(dbapi_conn, _):
    cursor = dbapi_conn.cursor()
    cursor.execute('PRAGMA foreign_keys=ON')
    cursor.execute('PRAGMA busy_timeout=20000')
    cursor.execute('PRAGMA journal_mode=WAL')
    cursor.close()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
class Base(DeclarativeBase):
    pass

def get_db():
    with SessionLocal() as db:
        yield db
