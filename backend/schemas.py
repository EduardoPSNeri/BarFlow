from typing import Literal
from pydantic import BaseModel, Field

class LoginIn(BaseModel):
    username: str = Field(min_length=1,max_length=60)
    password: str = Field(min_length=1)
class ChangePasswordIn(BaseModel):
    current_password: str = Field(min_length=1,max_length=128)
    new_password: str = Field(min_length=4,max_length=20)

class OpenIn(BaseModel):
    number:int = Field(ge=1)
class ItemIn(BaseModel):
    product_id:int=Field(gt=0)
    qty:int=Field(ge=1,le=999)
    request_id:str=Field(min_length=8,max_length=100)
class PayIn(BaseModel):
    method:Literal['pix','cartao','dinheiro']
    received_cents:int=Field(gt=0,le=100000000)
    request_id:str=Field(min_length=8,max_length=100)
class ProductIn(BaseModel):
    name:str=Field(min_length=2,max_length=120)
    price_cents:int=Field(ge=0,le=100000000)
    stock_qty:int=Field(ge=0,le=1000000)
    track_stock:bool=True
    active:bool=True
class MovementIn(BaseModel):
    delta:int=Field(ge=-100000,le=100000)
    reason:str=Field(min_length=3,max_length=120)
class SettingIn(BaseModel):
    allow_negative_stock:bool
class ShiftOpenIn(BaseModel):
    starting_cash_cents:int=Field(ge=0,le=100000000)
class ShiftCloseIn(BaseModel):
    counted_cash_cents:int=Field(ge=0,le=100000000)
class CancelIn(BaseModel):
    reason:str=Field(min_length=5,max_length=250)
class UserIn(BaseModel):
    username:str=Field(min_length=3,max_length=60,pattern=r'^[a-zA-Z0-9._-]+$')
    password:str=Field(min_length=4,max_length=20)
    role:Literal['ADMINISTRADOR','CAIXA']
