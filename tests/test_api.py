import os, sys, tempfile, importlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setenv('BARFLOW_DATA_DIR',str(tmp_path))
    for name in list(sys.modules):
        if name.startswith('backend.') or name=='backend':del sys.modules[name]
    from backend.database import SessionLocal
    from backend.models import User
    from backend.security import hash_password
    from backend.main import app
    with SessionLocal() as db:
        db.add(User(username='admin',password_hash=hash_password('SenhaMuitoForte2026!'),role='ADMINISTRADOR'))
        db.commit()
    client=TestClient(app)
    r=client.post('/api/auth/login',json={'username':'admin','password':'SenhaMuitoForte2026!'})
    assert r.status_code==200,r.text
    token=r.json()['csrf_token']
    # v2.1: mesas são cadastradas sob demanda. Pré-condição explícita para os testes legados.
    for number in (2, 3, 5, 6, 8):
        created = client.post('/api/tables', json={'number': number}, headers={'X-CSRF-Token': token})
        assert created.status_code == 201, created.text
    def req(method,url,body=None):
        return client.request(method,url,json=body,headers={'X-CSRF-Token':token})
    yield req, client
    client.close()


def test_open_orders_payments_stock_and_close(setup):
    req,client=setup
    r=req('POST','/api/products',{'name':'Refrigerante','price_cents':800,'stock_qty':10,'track_stock':True,'active':True});assert r.status_code==200,r.text
    pid=r.json()['id']
    assert req('POST','/api/cash/open',{'starting_cash_cents':10000}).status_code==200
    a=req('POST','/api/tables/5/open');assert a.status_code==200
    first=a.json()['id']
    assert req('POST','/api/tables/5/open').json()['id']==first
    assert req('POST','/api/tables/6/open').json()['id']!=first
    item={'product_id':pid,'qty':2,'request_id':'order-unique-01'}
    assert req('POST','/api/tables/5/items',item).status_code==200
    assert req('POST','/api/tables/5/items',item).status_code==200
    assert len(client.get('/api/tables/5/account').json()['items'])==1
    assert req('POST','/api/tables/5/close').status_code==400
    assert req('POST','/api/tables/5/payments',{'method':'pix','received_cents':1700,'request_id':'pay-invalid-pix'}).status_code==400
    r=req('POST','/api/tables/5/payments',{'method':'pix','received_cents':1000,'request_id':'pay-first-001'});assert r.status_code==200
    r=req('POST','/api/tables/5/payments',{'method':'dinheiro','received_cents':1000,'request_id':'pay-second-01'});assert r.status_code==200;assert r.json()['change_cents']==400
    assert client.get('/api/tables/5/account').json()['due_cents']==0
    assert req('POST','/api/tables/5/close').status_code==200
    assert next(p for p in client.get('/api/products').json() if p['id']==pid)['stock_qty']==8
    assert req('POST','/api/tables/5/open').json()['id']!=first
    assert client.get('/api/reports/summary').json()['gross_sales_cents']==1600


def test_auth_permissions_and_stock_policy(setup):
    req,client=setup
    u=req('POST','/api/users',{'username':'caixa1','password':'NovaSenhaBemForte!', 'role':'CAIXA'});assert u.status_code==200
    r=req('POST','/api/products',{'name':'Água','price_cents':500,'stock_qty':0,'track_stock':True,'active':True});assert r.status_code==200
    pid=r.json()['id']
    assert req('POST','/api/cash/open',{'starting_cash_cents':0}).status_code==200
    assert req('POST','/api/tables/2/open').status_code==200
    assert req('POST','/api/tables/2/items',{'product_id':pid,'qty':1,'request_id':'water-item-001'}).status_code==200
    assert req('POST','/api/tables/2/payments',{'method':'pix','received_cents':500,'request_id':'water-pay-001'}).status_code==200
    assert req('POST','/api/tables/2/close').status_code==400
    assert req('PUT','/api/settings',{'allow_negative_stock':True}).status_code==200
    assert req('POST','/api/tables/2/close').status_code==200
    assert next(p for p in client.get('/api/products').json() if p['id']==pid)['stock_qty']==-1
    assert client.post('/api/tables/8/open').status_code==403
    operator=TestClient(client.app)
    login=operator.post('/api/auth/login',json={'username':'caixa1','password':'NovaSenhaBemForte!'})
    assert login.status_code==200
    csrf=login.json()['csrf_token']
    assert operator.get('/api/reports/summary').status_code==403
    assert operator.post('/api/products',json={'name':'Outra','price_cents':10,'stock_qty':1,'track_stock':True,'active':True},headers={'X-CSRF-Token':csrf}).status_code==403
    operator.close()


def test_cancel_empty_and_must_have_reason(setup):
    req,client=setup
    assert req('POST','/api/tables/3/open').status_code==200
    assert req('POST','/api/tables/3/cancel',{'reason':'Cliente trocou de mesa'}).status_code==200
    assert client.get('/api/tables/3/account').status_code==404
    assert req('POST','/api/tables/3/open').status_code==200
