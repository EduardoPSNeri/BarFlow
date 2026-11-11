from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, CheckConstraint, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

def now(): return datetime.now(timezone.utc)

class User(Base):
    __tablename__='users'
    id:Mapped[int]=mapped_column(primary_key=True)
    username:Mapped[str]=mapped_column(String(60),unique=True,nullable=False)
    password_hash:Mapped[str]=mapped_column(String(255),nullable=False)
    role:Mapped[str]=mapped_column(String(20),nullable=False,default='CAIXA')
    active:Mapped[bool]=mapped_column(Boolean,default=True)
    must_change_password:Mapped[bool]=mapped_column(Boolean,default=False,nullable=False)

class AuthSession(Base):
    __tablename__='auth_sessions'
    id:Mapped[int]=mapped_column(primary_key=True)
    token_hash:Mapped[str]=mapped_column(String(64),unique=True,index=True)
    csrf_hash:Mapped[str]=mapped_column(String(64),nullable=False)
    user_id:Mapped[int]=mapped_column(ForeignKey('users.id'))
    expires_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    revoked:Mapped[bool]=mapped_column(Boolean,default=False)

class Table(Base):
    __tablename__='tables'
    id:Mapped[int]=mapped_column(primary_key=True)
    number:Mapped[int]=mapped_column(Integer,unique=True,nullable=False)
    active:Mapped[bool]=mapped_column(Boolean,default=True)

class Product(Base):
    __tablename__='products'
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(120),unique=True,nullable=False)
    price_cents:Mapped[int]=mapped_column(Integer,nullable=False)
    stock_qty:Mapped[int]=mapped_column(Integer,default=0)
    track_stock:Mapped[bool]=mapped_column(Boolean,default=True)
    active:Mapped[bool]=mapped_column(Boolean,default=True)
    __table_args__=(CheckConstraint('price_cents >= 0'),)

class Setting(Base):
    __tablename__='settings'
    key:Mapped[str]=mapped_column(String(80),primary_key=True)
    value:Mapped[str]=mapped_column(String(200),nullable=False)

class CashShift(Base):
    __tablename__='cash_shifts'
    id:Mapped[int]=mapped_column(primary_key=True)
    opened_by:Mapped[int]=mapped_column(ForeignKey('users.id'))
    closed_by:Mapped[int|None]=mapped_column(ForeignKey('users.id'),nullable=True)
    opened_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    closed_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    starting_cash_cents:Mapped[int]=mapped_column(Integer,default=0)
    closing_cash_cents:Mapped[int|None]=mapped_column(Integer,nullable=True)
    status:Mapped[str]=mapped_column(String(12),default='OPEN')

class Account(Base):
    __tablename__='accounts'
    id:Mapped[int]=mapped_column(primary_key=True)
    table_id:Mapped[int]=mapped_column(ForeignKey('tables.id'),nullable=False)
    opened_by:Mapped[int]=mapped_column(ForeignKey('users.id'),nullable=False)
    status:Mapped[str]=mapped_column(String(12),default='OPEN',nullable=False)
    opened_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    closed_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    closed_by:Mapped[int|None]=mapped_column(ForeignKey('users.id'),nullable=True)
    cancel_reason:Mapped[str|None]=mapped_column(String(250),nullable=True)
    __table_args__=(Index("uq_open_account_per_table", "table_id", unique=True, sqlite_where=text("status = 'OPEN'")),)
    items:Mapped[list['OrderItem']]=relationship(back_populates='account',cascade='all, delete-orphan')
    payments:Mapped[list['Payment']]=relationship(back_populates='account',cascade='all, delete-orphan')

class OrderItem(Base):
    __tablename__='order_items'
    id:Mapped[int]=mapped_column(primary_key=True)
    account_id:Mapped[int]=mapped_column(ForeignKey('accounts.id'),index=True)
    product_id:Mapped[int]=mapped_column(ForeignKey('products.id'))
    product_name:Mapped[str]=mapped_column(String(120))
    unit_price_cents:Mapped[int]=mapped_column(Integer)
    qty:Mapped[int]=mapped_column(Integer)
    idempotency_key:Mapped[str]=mapped_column(String(100),unique=True,nullable=False)
    created_by:Mapped[int]=mapped_column(ForeignKey('users.id'))
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    account:Mapped[Account]=relationship(back_populates='items')
    __table_args__=(CheckConstraint('qty > 0'),)

class Payment(Base):
    __tablename__='payments'
    id:Mapped[int]=mapped_column(primary_key=True)
    account_id:Mapped[int]=mapped_column(ForeignKey('accounts.id'),index=True)
    cash_shift_id:Mapped[int]=mapped_column(ForeignKey('cash_shifts.id'))
    method:Mapped[str]=mapped_column(String(12))
    received_cents:Mapped[int]=mapped_column(Integer)
    applied_cents:Mapped[int]=mapped_column(Integer)
    change_cents:Mapped[int]=mapped_column(Integer,default=0)
    idempotency_key:Mapped[str]=mapped_column(String(100),unique=True,nullable=False)
    created_by:Mapped[int]=mapped_column(ForeignKey('users.id'))
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    account:Mapped[Account]=relationship(back_populates='payments')

class StockMovement(Base):
    __tablename__='stock_movements'
    id:Mapped[int]=mapped_column(primary_key=True)
    product_id:Mapped[int]=mapped_column(ForeignKey('products.id'))
    delta:Mapped[int]=mapped_column(Integer)
    reason:Mapped[str]=mapped_column(String(120))
    account_id:Mapped[int|None]=mapped_column(ForeignKey('accounts.id'),nullable=True)
    created_by:Mapped[int]=mapped_column(ForeignKey('users.id'))
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)


class CashExpense(Base):
    __tablename__='cash_expenses'
    id:Mapped[int]=mapped_column(primary_key=True)
    cash_shift_id:Mapped[int]=mapped_column(ForeignKey('cash_shifts.id'),nullable=False,index=True)
    description:Mapped[str]=mapped_column(String(160),nullable=False)
    category:Mapped[str]=mapped_column(String(60),nullable=False)
    method:Mapped[str]=mapped_column(String(12),nullable=False)
    amount_cents:Mapped[int]=mapped_column(Integer,nullable=False)
    created_by:Mapped[int]=mapped_column(ForeignKey('users.id'),nullable=False)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    __table_args__=(CheckConstraint('amount_cents > 0'),)
