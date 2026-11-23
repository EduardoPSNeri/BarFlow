"""Testes independentes da demo Render; usam SQLite em memoria."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from backend.cloud import provision_cloud_admin
from backend.health import health
from backend.database import Base
from backend.models import User
from backend.security import hash_password, verify_password


@pytest.fixture
def database():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine)
    engine.dispose()


def test_cloud_admin_is_provisioned_only_when_enabled(monkeypatch, database):
    monkeypatch.setenv('BARFLOW_CLOUD_DEMO', '1')
    monkeypatch.setenv('BARFLOW_ADMIN_PASSWORD', 'ExemploForte123456789!')
    assert provision_cloud_admin(database, User, hash_password) is True
    assert provision_cloud_admin(database, User, hash_password) is False
    with database() as db:
        admin = db.query(User).filter_by(username='admin').one()
        assert admin.role == 'ADMINISTRADOR'
        assert not admin.must_change_password
        assert admin.password_hash != 'ExemploForte123456789!'
        assert verify_password(admin.password_hash, 'ExemploForte123456789!')


def test_cloud_fails_closed_without_strong_password(monkeypatch, database):
    monkeypatch.setenv('BARFLOW_CLOUD_DEMO', '1')
    monkeypatch.delenv('BARFLOW_ADMIN_PASSWORD', raising=False)
    with pytest.raises(RuntimeError, match='BARFLOW_ADMIN_PASSWORD'):
        provision_cloud_admin(database, User, hash_password)
    monkeypatch.setenv('BARFLOW_ADMIN_PASSWORD', 'admin')
    with pytest.raises(RuntimeError, match='BARFLOW_ADMIN_PASSWORD'):
        provision_cloud_admin(database, User, hash_password)


def test_local_mode_does_not_create_admin(monkeypatch, database):
    monkeypatch.delenv('BARFLOW_CLOUD_DEMO', raising=False)
    monkeypatch.delenv('BARFLOW_ADMIN_PASSWORD', raising=False)
    assert provision_cloud_admin(database, User, hash_password) is False
    with database() as db:
        assert db.query(User).count() == 0


def test_health_checks_database(database):
    with database() as db:
        assert health(db) == {'status': 'ok'}


def test_health_returns_503_on_database_error():
    class BadSession:
        def execute(self, _):
            from sqlalchemy.exc import OperationalError
            raise OperationalError('SELECT 1', (), Exception('unavailable'))
    with pytest.raises(HTTPException) as exc:
        health(BadSession())
    assert exc.value.status_code == 503
