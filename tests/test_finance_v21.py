"""Testes de regressão das melhorias de caixa, relatórios e mesas (BarFlow 2.1)."""
import sys
from pathlib import Path
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def test_cash_expenses_tables_and_reports(tmp_path, monkeypatch):
    monkeypatch.setenv('BARFLOW_DATA_DIR',str(tmp_path))
    for name in list(sys.modules):
        if name=='backend' or name.startswith('backend.'):
            del sys.modules[name]
    from backend.main import app
    from backend.database import SessionLocal
    from backend.models import User
    from backend.security import hash_password
    with SessionLocal() as db:
        db.add(User(username='admin',password_hash=hash_password('senha-teste-123'),role='ADMINISTRADOR'))
        db.commit()
    with TestClient(app) as client:
        login=client.post('/api/auth/login',json={'username':'admin','password':'senha-teste-123'})
        assert login.status_code==200,login.text
        h={'X-CSRF-Token':login.json()['csrf_token']}
        assert client.get('/api/tables').json()==[]
        assert client.post('/api/tables',json={'number':7},headers=h).status_code==201
        assert client.post('/api/tables',json={'number':7},headers=h).status_code==409
        assert len(client.get('/api/tables').json())==1
        assert client.post('/api/cash/expenses',json={'description':'Diária','category':'Pessoal','method':'dinheiro','amount_cents':100},headers=h).status_code==400
        assert client.post('/api/cash/open',json={'starting_cash_cents':5000},headers=h).status_code==200
        good={'description':'Diária do funcionário','category':'Diária','method':'dinheiro','amount_cents':2000}
        assert client.post('/api/cash/expenses',json=good,headers=h).status_code==201
        assert client.get('/api/cash/current').json()['expected_cash_cents']==3000
        assert client.post('/api/cash/expenses',json={**good,'amount_cents':3001},headers=h).status_code==400
        ledger=client.get('/api/cash/ledger').json()
        assert ledger['total_expenses_cents']==2000
        assert len(ledger['rows'])==1
        today=__import__('datetime').datetime.now(__import__('zoneinfo').ZoneInfo('America/Sao_Paulo')).date().isoformat()
        report=client.get('/api/reports/finance',params={'start':today,'end':today})
        assert report.status_code==200,report.text
        assert report.json()['total_expenses_cents']==2000
        assert client.delete('/api/tables/7',headers=h).status_code==200
        assert client.get('/api/tables').json()[0]['active'] is False
        assert client.post('/api/tables',json={'number':7},headers=h).status_code==201
