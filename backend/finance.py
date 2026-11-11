"""BarFlow 2.1: movimentos de caixa e mesas dinâmicas. Persistência SQLite."""
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import get_db
from .models import User, Table, Account, Payment, CashShift, now, CashExpense
from .services import current_shift, active_account, fail, serialize_account
from .security import auth, admin

router = APIRouter(prefix='/api')
TZ = ZoneInfo('America/Sao_Paulo')

class TableIn(BaseModel):
    number: int = Field(ge=1, le=9999)

class ExpenseIn(BaseModel):
    description: str = Field(min_length=3, max_length=160)
    category: str = Field(min_length=2, max_length=60)
    method: str = Field(pattern=r'^(dinheiro|pix|cartao)$')
    amount_cents: int = Field(gt=0, le=100000000)


def money_totals(pays, expenses, start=0):
    receipts = {k: sum(p.applied_cents for p in pays if p.method == k) for k in ('dinheiro', 'pix', 'cartao')}
    spent = {k: sum(e.amount_cents for e in expenses if e.method == k) for k in ('dinheiro', 'pix', 'cartao')}
    return {
        'receipts_cents': receipts,
        'expenses_cents': spent,
        'net_cents': {k: receipts[k]-spent[k] for k in receipts},
        'total_receipts_cents': sum(receipts.values()),
        'total_expenses_cents': sum(spent.values()),
        'net_operations_cents': sum(receipts.values())-sum(spent.values()),
        'expected_cash_cents': start + receipts['dinheiro']-spent['dinheiro'],
    }


def ledger_rows(db, pays, expenses):
    rows = []
    for p in pays:
        account = db.get(Account,p.account_id)
        table = db.get(Table,account.table_id) if account else None
        rows.append({'id': 'P'+str(p.id), 'kind': 'entrada', 'description': f'Pagamento comanda #{p.account_id} / Mesa {table.number if table else "?"}',
                     'category':'Venda', 'method':p.method, 'amount_cents':p.applied_cents,
                     'created_at':p.created_at.isoformat()})
    for e in expenses:
        rows.append({'id':'E'+str(e.id), 'kind':'saida','description':e.description,'category':e.category,
                     'method':e.method,'amount_cents':e.amount_cents,'created_at':e.created_at.isoformat()})
    return sorted(rows,key=lambda r:(r['created_at'],r['id']),reverse=True)


@router.post('/tables', status_code=201)
def create_table(body:TableIn, user:User=Depends(admin),db:Session=Depends(get_db)):
    t=db.query(Table).filter_by(number=body.number).first()
    if t:
        if t.active:fail('Essa mesa já está cadastrada.',409)
        t.active=True
    else:
        t=Table(number=body.number,active=True);db.add(t)
    db.commit()
    return {'number':body.number,'active':True}

@router.delete('/tables/{number}')
def deactivate_table(number:int,user:User=Depends(admin),db:Session=Depends(get_db)):
    t=db.query(Table).filter_by(number=number,active=True).first()
    if not t:fail('Mesa não encontrada.',404)
    if active_account(db,number):fail('Encerre a comanda antes de ocultar a mesa.',409)
    t.active=False;db.commit()
    return {'number':number,'active':False}

@router.post('/cash/expenses',status_code=201)
def create_expense(body:ExpenseIn,user:User=Depends(auth),db:Session=Depends(get_db)):
    shift=current_shift(db)
    if shift is None:fail('Abra o caixa para registrar uma saída.')
    if body.method=='dinheiro':
        pays=db.query(Payment).filter_by(cash_shift_id=shift.id).all()
        expenses=db.query(CashExpense).filter_by(cash_shift_id=shift.id).all()
        expected=money_totals(pays,expenses,shift.starting_cash_cents)['expected_cash_cents']
        if body.amount_cents>expected:fail('Dinheiro insuficiente no caixa para esta saída.')
    item=CashExpense(cash_shift_id=shift.id,description=body.description.strip(),category=body.category.strip(),
                     method=body.method,amount_cents=body.amount_cents,created_by=user.id)
    db.add(item);db.commit();db.refresh(item)
    return {'id':item.id,'amount_cents':item.amount_cents}

@router.get('/cash/ledger')
def cash_ledger(user:User=Depends(auth),db:Session=Depends(get_db)):
    shift=current_shift(db)
    if not shift:return {'open':False,'rows':[]}
    pays=db.query(Payment).filter_by(cash_shift_id=shift.id).all()
    expenses=db.query(CashExpense).filter_by(cash_shift_id=shift.id).all()
    return {'open':True,'shift_id':shift.id,'rows':ledger_rows(db,pays,expenses),
            **money_totals(pays,expenses,shift.starting_cash_cents)}

@router.get('/reports/finance')
def finance_report(start:str|None=None,end:str|None=None,user:User=Depends(admin),db:Session=Depends(get_db)):
    try:
        d1=datetime.strptime(start,'%Y-%m-%d').date() if start else datetime.now(TZ).date()
        d2=datetime.strptime(end,'%Y-%m-%d').date() if end else d1
    except ValueError:fail('Datas inválidas. Use AAAA-MM-DD.')
    if d2<d1 or (d2-d1).days>365:fail('Intervalo inválido: máximo de 366 dias.')
    def in_range(dt):
        if dt is None:return False
        if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)
        return d1<=dt.astimezone(TZ).date()<=d2
    pays=[p for p in db.query(Payment).all() if in_range(p.created_at)]
    expenses=[e for e in db.query(CashExpense).all() if in_range(e.created_at)]
    closed=[a for a in db.query(Account).filter_by(status='CLOSED') if in_range(a.closed_at)]
    shifts=[s for s in db.query(CashShift).all() if in_range(s.opened_at)]
    summary=money_totals(pays,expenses)
    return {'start':str(d1),'end':str(d2),'closed_accounts':len(closed),
            'closed_sales_cents':sum(serialize_account(a)['total_cents'] for a in closed),
            'open_accounts':db.query(Account).filter_by(status='OPEN').count(),
            'shifts':len(shifts),'rows':ledger_rows(db,pays,expenses),**summary}
