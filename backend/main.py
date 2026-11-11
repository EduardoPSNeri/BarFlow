import os, time, secrets, hashlib
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict
from fastapi import FastAPI, Depends, Request, Response, HTTPException, Body
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .database import Base,engine,get_db,SessionLocal,ROOT
from .models import User,AuthSession,Table,Product,Setting,Account,OrderItem,Payment,StockMovement,CashShift,now
from .schemas import LoginIn,ChangePasswordIn,OpenIn,ItemIn,PayIn,ProductIn,MovementIn,SettingIn,ShiftOpenIn,ShiftCloseIn,CancelIn,UserIn
from .security import auth,admin,login_session,hash_password,verify_password,digest
from .services import active_account,require_account,serialize_account,open_account,add_item,pay,close_account,current_shift,fail

app=FastAPI(title='BarFlow API',version='1.0.0',docs_url=None,redoc_url=None,openapi_url=None)
FRONT=ROOT/'Frontend'
app.mount('/css',StaticFiles(directory=FRONT/'css'),name='css')
app.mount('/js',StaticFiles(directory=FRONT/'js'),name='js')
# An existing database may predate the password-rotation column.
# SQLite requires an explicit additive migration for this backward-compatible change.
with engine.begin() as connection:
    if "users" in __import__('sqlalchemy').inspect(connection).get_table_names():
        fields = {row[1] for row in connection.execute(text('PRAGMA table_info(users)'))}
        if 'must_change_password' not in fields:
            connection.execute(text('ALTER TABLE users ADD COLUMN must_change_password BOOLEAN NOT NULL DEFAULT 0'))
Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    if not db.query(Table).first():
        db.add_all([Table(number=i) for i in range(1,11)])
    if not db.get(Setting,'allow_negative_stock'):
        db.add(Setting(key='allow_negative_stock',value='false'))
    db.commit()

@app.middleware('http')
async def headers(request:Request,call_next):
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['Cache-Control']='no-store'
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
    return response

@app.get('/')
def home():return RedirectResponse('/index.html')
@app.get('/{page}.html')
def page(page:str):
    if page not in {'index','pedidos','pagamentos','estoque','caixa','relatorios','usuarios','login','alterar-senha'}:raise HTTPException(404)
    return FileResponse(FRONT/(page+'.html'))

# Brute-force throttle per username+remote address (per process)
FAILURES=defaultdict(list)
@app.post('/api/auth/login')
def login(body:LoginIn,response:Response,request:Request,db:Session=Depends(get_db)):
    key=(request.client.host if request.client else 'local',body.username.lower())
    now_s=time.monotonic();FAILURES[key]=[t for t in FAILURES[key] if now_s-t<300]
    if len(FAILURES[key])>=5:raise HTTPException(429,'Muitas tentativas. Aguarde cinco minutos.')
    user=db.query(User).filter(User.username==body.username).first()
    if not user or not user.active or not verify_password(user.password_hash,body.password):
        FAILURES[key].append(now_s)
        raise HTTPException(401,'Usuário ou senha inválidos.')
    FAILURES.pop(key,None)
    csrf=login_session(db,response,user)
    return {'user':{'username':user.username,'role':user.role,'must_change_password':user.must_change_password},'csrf_token':csrf}

@app.get('/api/auth/me')
def me(request:Request,user:User=Depends(auth)):
    sess=request.state.auth_session
    # New CSRF token is issued only during login; JS caches it in sessionStorage.
    return {'username':user.username,'role':user.role,'must_change_password':user.must_change_password}
@app.post('/api/auth/change-password')
def change_password(body:ChangePasswordIn, request:Request, user:User=Depends(auth), db:Session=Depends(get_db)):
    if not verify_password(user.password_hash, body.current_password):
        raise HTTPException(400, 'Senha atual incorreta.')
    if body.new_password == body.current_password or body.new_password.lower() == 'admin':
        raise HTTPException(400, 'Escolha uma senha nova e diferente da senha provisória.')
    user.password_hash = hash_password(body.new_password)
    user.must_change_password = False
    # Invalidate every session after rotating the password, including the current one.
    for session in db.query(AuthSession).filter_by(user_id=user.id, revoked=False):
        session.revoked = True
    db.commit()
    return {'ok':True,'message':'Senha alterada. Entre novamente.'}

@app.post('/api/auth/logout')
def logout(request:Request,response:Response,user:User=Depends(auth),db:Session=Depends(get_db)):
    request.state.auth_session.revoked=True;db.commit();response.delete_cookie('barflow_session',path='/');return {'ok':True}

@app.get('/api/tables')
def tables(user:User=Depends(auth),db:Session=Depends(get_db)):
    out=[]
    for table in db.query(Table).order_by(Table.number).all():
        a=active_account(db,table.number)
        out.append({'number':table.number,'active':table.active,'account':serialize_account(a) if a else None})
    return out
@app.post('/api/tables/{number}/open')
def open_table(number:int,user:User=Depends(auth),db:Session=Depends(get_db)):
    return serialize_account(open_account(db,number,user.id))
@app.get('/api/tables/{number}/account')
def account(number:int,user:User=Depends(auth),db:Session=Depends(get_db)):
    return serialize_account(require_account(db,number))
@app.post('/api/tables/{number}/items')
def item(number:int,body:ItemIn,user:User=Depends(auth),db:Session=Depends(get_db)):
    i=add_item(db,number,body,user.id);return {'id':i.id,'qty':i.qty,'name':i.product_name}
@app.post('/api/tables/{number}/payments')
def payment(number:int,body:PayIn,user:User=Depends(auth),db:Session=Depends(get_db)):
    p=pay(db,number,body,user.id)
    return {'id':p.id,'applied_cents':p.applied_cents,'change_cents':p.change_cents}
@app.post('/api/tables/{number}/close')
def close(number:int,user:User=Depends(auth),db:Session=Depends(get_db)):
    a=close_account(db,number,user.id);return {'id':a.id,'status':a.status,'table_number':number}
@app.post('/api/tables/{number}/cancel')
def cancel(number:int,body:CancelIn,user:User=Depends(admin),db:Session=Depends(get_db)):
    a=require_account(db,number)
    if a.items or a.payments:fail('Somente comandas vazias e sem pagamentos podem ser canceladas.')
    a.status='CANCELLED';a.cancel_reason=body.reason;a.closed_at=now();a.closed_by=user.id;db.commit()
    return {'id':a.id,'status':a.status}

@app.get('/api/products')
def products(user:User=Depends(auth),db:Session=Depends(get_db)):
    return [{'id':p.id,'name':p.name,'price_cents':p.price_cents,'stock_qty':p.stock_qty,'track_stock':p.track_stock,'active':p.active} for p in db.query(Product).order_by(Product.name).all()]
@app.post('/api/products')
def create_product(body:ProductIn,user:User=Depends(admin),db:Session=Depends(get_db)):
    p=Product(**body.model_dump());db.add(p)
    try:db.commit()
    except IntegrityError:db.rollback();fail('Já existe produto com esse nome.',409)
    db.refresh(p)
    if p.stock_qty:
        db.add(StockMovement(product_id=p.id,delta=p.stock_qty,reason="Estoque inicial",created_by=user.id))
        db.commit()
    return {'id':p.id}
@app.put('/api/products/{id}')
def update_product(id:int,body:ProductIn,user:User=Depends(admin),db:Session=Depends(get_db)):
    p=db.get(Product,id)
    if not p:fail('Produto não encontrado.',404)
    # No direct stock edits after creation: use audited movements.
    if p.stock_qty != body.stock_qty:fail('Altere o estoque utilizando movimentação de estoque.')
    for k in ['name','price_cents','track_stock','active']:setattr(p,k,getattr(body,k))
    db.commit();return {'id':p.id}
@app.post('/api/products/{id}/stock')
def movement(id:int,body:MovementIn,user:User=Depends(admin),db:Session=Depends(get_db)):
    p=db.get(Product,id)
    if not p:fail('Produto não encontrado.',404)
    new_qty=p.stock_qty+body.delta
    if new_qty<0 and db.get(Setting,'allow_negative_stock').value!='true':fail('Estoque negativo não permitido.')
    p.stock_qty=new_qty;db.add(StockMovement(product_id=id,delta=body.delta,reason=body.reason,created_by=user.id));db.commit()
    return {'product_id':id,'stock_qty':p.stock_qty}
@app.get('/api/stock/movements')
def movements(user:User=Depends(auth),db:Session=Depends(get_db)):
    out=[]
    for m in db.query(StockMovement).order_by(StockMovement.id.desc()).limit(100):
        p=db.get(Product,m.product_id)
        out.append({'id':m.id,'product':p.name if p else str(m.product_id),'delta':m.delta,'reason':m.reason,'created_at':m.created_at.isoformat()})
    return out
@app.get('/api/settings')
def settings(user:User=Depends(auth),db:Session=Depends(get_db)):
    return {'allow_negative_stock':db.get(Setting,'allow_negative_stock').value=='true'}
@app.put('/api/settings')
def update_settings(body:SettingIn,user:User=Depends(admin),db:Session=Depends(get_db)):
    db.get(Setting,'allow_negative_stock').value='true' if body.allow_negative_stock else 'false';db.commit()
    return body

@app.get('/api/cash/current')
def cash_current(user:User=Depends(auth),db:Session=Depends(get_db)):
    s=current_shift(db)
    if not s:return {'open':False}
    pays=db.query(Payment).filter_by(cash_shift_id=s.id).all()
    totals={method:sum(p.applied_cents for p in pays if p.method==method) for method in ['dinheiro','pix','cartao']}
    return {'open':True,'id':s.id,'starting_cash_cents':s.starting_cash_cents,'totals':totals,'expected_cash_cents':s.starting_cash_cents+totals['dinheiro'],'opened_at':s.opened_at.isoformat()}
@app.post('/api/cash/open')
def cash_open(body:ShiftOpenIn,user:User=Depends(auth),db:Session=Depends(get_db)):
    if current_shift(db):fail('Já existe caixa aberto.')
    s=CashShift(opened_by=user.id,starting_cash_cents=body.starting_cash_cents)
    db.add(s);db.commit();return {'id':s.id,'status':'OPEN'}
@app.post('/api/cash/close')
def cash_close(body:ShiftCloseIn,user:User=Depends(admin),db:Session=Depends(get_db)):
    s=current_shift(db)
    if not s:fail('Nenhum caixa aberto.')
    pays=db.query(Payment).filter_by(cash_shift_id=s.id,method='dinheiro').all()
    expected=s.starting_cash_cents+sum(p.applied_cents for p in pays)
    s.status='CLOSED';s.closed_at=now();s.closed_by=user.id;s.closing_cash_cents=body.counted_cash_cents;db.commit()
    return {'expected_cents':expected,'counted_cents':body.counted_cash_cents,'difference_cents':body.counted_cash_cents-expected}

@app.get('/api/reports/summary')
def report(user:User=Depends(admin),db:Session=Depends(get_db)):
    closed=db.query(Account).filter_by(status='CLOSED').order_by(Account.id).all()
    totals=[serialize_account(a) for a in closed]
    pays=db.query(Payment).all()
    from zoneinfo import ZoneInfo
    local_day=now().astimezone(ZoneInfo("America/Sao_Paulo")).date()
    today_accounts=[a for a in closed if a.closed_at and a.closed_at.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("America/Sao_Paulo")).date()==local_day]
    return {'closed_accounts':len(closed),'gross_sales_cents':sum(a['total_cents'] for a in totals),'today_sales_cents':sum(serialize_account(a)['total_cents'] for a in today_accounts),'today_closed_accounts':len(today_accounts),
            'payments_cents':{m:sum(p.applied_cents for p in pays if p.method==m) for m in ['dinheiro','pix','cartao']},
            'open_accounts':db.query(Account).filter_by(status='OPEN').count(),
            'history':[{'id':a.id,'table_number':db.get(Table,a.table_id).number,'closed_at':a.closed_at.isoformat() if a.closed_at else None,'total_cents':serialize_account(a)['total_cents']} for a in closed[-100:][::-1]]}
@app.get('/api/users')
def users(user:User=Depends(admin),db:Session=Depends(get_db)):
    return [{'id':u.id,'username':u.username,'role':u.role,'active':u.active} for u in db.query(User).all()]
@app.post('/api/users')
def create_user(body:UserIn,user:User=Depends(admin),db:Session=Depends(get_db)):
    u=User(username=body.username,role=body.role,password_hash=hash_password(body.password));db.add(u)
    try:db.commit()
    except IntegrityError:db.rollback();fail('Usuário já cadastrado.',409)
    return {'id':u.id,'username':u.username}
