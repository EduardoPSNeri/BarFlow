"""Regressão: primeiro login, bloqueio, troca e migração."""
import os, sys, subprocess
from pathlib import Path
from fastapi.testclient import TestClient

ROOT=Path(__file__).resolve().parents[1]

def test_default_admin_forced_rotation(tmp_path, monkeypatch):
    monkeypatch.setenv('BARFLOW_DATA_DIR', str(tmp_path))
    for name in list(sys.modules):
        if name == 'backend' or name.startswith('backend.'):
            del sys.modules[name]
    from backend.main import app
    from backend.database import SessionLocal
    from backend.models import User
    from backend.security import verify_password
    # Installer creates admin without interaction.
    env={**os.environ,'BARFLOW_DATA_DIR':str(tmp_path)}
    created=subprocess.run([sys.executable,str(ROOT/'scripts/criar_admin.py')],env=env,capture_output=True,text=True)
    assert created.returncode==0,created.stderr
    assert 'admin / admin' in created.stdout
    with SessionLocal() as db:
        user=db.query(User).filter_by(username='admin').one()
        assert user.must_change_password
        assert user.password_hash != 'admin'
        assert verify_password(user.password_hash,'admin')
    client=TestClient(app)
    login=client.post('/api/auth/login',json={'username':'admin','password':'admin'})
    assert login.status_code==200
    assert login.json()['user']['must_change_password'] is True
    csrf=login.json()['csrf_token']
    assert client.get('/api/tables').status_code==403
    assert client.get('/api/auth/me').json()['must_change_password'] is True
    assert client.get('/alterar-senha.html').status_code==200
    headers={'X-CSRF-Token':csrf}
    assert client.post('/api/auth/change-password',json={'current_password':'incorrect','new_password':'SenhaForte123!'},headers=headers).status_code==400
    assert client.post('/api/auth/change-password',json={'current_password':'admin','new_password':'admin'},headers=headers).status_code==400
    changed=client.post('/api/auth/change-password',json={'current_password':'admin','new_password':'SenhaForte123!'},headers=headers)
    assert changed.status_code==200,changed.text
    assert client.get('/api/auth/me').status_code==401
    assert client.post('/api/auth/login',json={'username':'admin','password':'admin'}).status_code==401
    relog=client.post('/api/auth/login',json={'username':'admin','password':'SenhaForte123!'})
    assert relog.status_code==200
    assert relog.json()['user']['must_change_password'] is False
    assert client.get('/api/tables').status_code==200
    # Re-running installer does not reset credentials.
    rerun=subprocess.run([sys.executable,str(ROOT/'scripts/criar_admin.py')],env=env,capture_output=True,text=True)
    assert rerun.returncode==0
    assert 'preservado' in rerun.stdout
    assert client.post('/api/auth/login',json={'username':'admin','password':'admin'}).status_code==401
    client.close()
