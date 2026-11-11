from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .models import Table,Account,Product,OrderItem,Payment,Setting,StockMovement,CashShift
from .schemas import ItemIn,PayIn

def fail(msg,code=400):raise HTTPException(code,msg)
def active_account(db:Session,number:int)->Account|None:
    return db.query(Account).join(Table).filter(Table.number==number,Account.status=='OPEN').first()
def require_account(db:Session,number:int)->Account:
    a=active_account(db,number)
    if not a:fail('Mesa sem comanda aberta.',404)
    return a

def serialize_account(a:Account)->dict:
    items=[{'id':i.id,'product_id':i.product_id,'name':i.product_name,'price_cents':i.unit_price_cents,'qty':i.qty} for i in a.items]
    pays=[{'id':p.id,'method':p.method,'received_cents':p.received_cents,'applied_cents':p.applied_cents,'change_cents':p.change_cents,'created_at':p.created_at.isoformat()} for p in a.payments]
    total=sum(i['price_cents']*i['qty'] for i in items);paid=sum(p['applied_cents'] for p in pays)
    return {'id':a.id,'table_number':a.table_id,'status':a.status,'items':items,'payments':pays,'total_cents':total,'paid_cents':paid,'due_cents':max(0,total-paid),'opened_at':a.opened_at.isoformat(),'closed_at':a.closed_at.isoformat() if a.closed_at else None}

def open_account(db:Session,number:int,user_id:int)->Account:
    table=db.query(Table).filter_by(number=number,active=True).first()
    if not table:fail('Mesa inexistente ou inativa.',404)
    existing=active_account(db,number)
    if existing:return existing
    a=Account(table_id=table.id,opened_by=user_id)
    db.add(a);db.commit();db.refresh(a);return a

def add_item(db:Session,number:int,data:ItemIn,user_id:int)->OrderItem:
    existing=db.query(OrderItem).filter_by(idempotency_key=data.request_id).first()
    if existing:
        if existing.account_id != require_account(db,number).id:fail('Identificador reutilizado em outra comanda.',409)
        return existing
    a=require_account(db,number)
    product=db.get(Product,data.product_id)
    if not product or not product.active:fail('Produto indisponível.',404)
    item=OrderItem(account_id=a.id,product_id=product.id,product_name=product.name,unit_price_cents=product.price_cents,qty=data.qty,idempotency_key=data.request_id,created_by=user_id)
    db.add(item)
    try: db.commit()
    except IntegrityError:db.rollback();fail('Pedido duplicado, consulte a comanda.',409)
    db.refresh(item);return item

def current_shift(db:Session)->CashShift|None:
    return db.query(CashShift).filter_by(status='OPEN').first()

def pay(db:Session,number:int,data:PayIn,user_id:int)->Payment:
    existing=db.query(Payment).filter_by(idempotency_key=data.request_id).first()
    if existing:
        if existing.account_id != require_account(db,number).id:fail('Identificador reutilizado em outra comanda.',409)
        return existing
    shift=current_shift(db)
    if not shift:fail('Abra o caixa antes de registrar pagamentos.')
    a=require_account(db,number);summary=serialize_account(a);due=summary['due_cents']
    if due<=0:fail('Comanda sem saldo pendente.')
    if data.method!='dinheiro' and data.received_cents>due:fail('Pix ou cartão não pode exceder o saldo.')
    applied=min(data.received_cents,due);change=data.received_cents-applied if data.method=='dinheiro' else 0
    p=Payment(account_id=a.id,cash_shift_id=shift.id,method=data.method,received_cents=data.received_cents,applied_cents=applied,change_cents=change,idempotency_key=data.request_id,created_by=user_id)
    db.add(p)
    try:db.commit()
    except IntegrityError:db.rollback();fail('Pagamento duplicado, atualize a página.',409)
    db.refresh(p);return p

def close_account(db:Session,number:int,user_id:int)->Account:
    a=require_account(db,number);summary=serialize_account(a)
    if not a.items:fail('Não é possível encerrar uma comanda vazia.')
    if summary['due_cents']>0:fail('Não é possível encerrar uma comanda com saldo pendente.')
    allow_neg=db.get(Setting,'allow_negative_stock');allow_negative=allow_neg and allow_neg.value=='true'
    aggregated={}
    for i in a.items:aggregated[i.product_id]=aggregated.get(i.product_id,0)+i.qty
    for product_id,qty in aggregated.items():
        p=db.get(Product,product_id)
        if p and p.track_stock and not allow_negative and p.stock_qty<qty:fail('Estoque insuficiente para '+p.name+'. Ajuste o estoque ou a configuração.')
    for product_id,qty in aggregated.items():
        p=db.get(Product,product_id)
        if p and p.track_stock:
            p.stock_qty-=qty
            db.add(StockMovement(product_id=p.id,delta=-qty,reason='Baixa por encerramento da comanda',account_id=a.id,created_by=user_id))
    from .models import now
    a.status='CLOSED';a.closed_at=now();a.closed_by=user_id;db.commit();db.refresh(a);return a
