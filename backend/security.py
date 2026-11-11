import hashlib, secrets
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from .database import get_db
from .models import User, AuthSession
ph=PasswordHasher()
def hash_password(password:str)->str:return ph.hash(password)
def verify_password(encoded:str,password:str)->bool:
    try:return ph.verify(encoded,password)
    except (VerifyMismatchError,VerificationError):return False

def digest(s:str)->str:return hashlib.sha256(s.encode()).hexdigest()

def login_session(db:Session,response:Response,user:User)->str:
    token=secrets.token_urlsafe(40);csrf=secrets.token_urlsafe(32)
    db.add(AuthSession(token_hash=digest(token),csrf_hash=digest(csrf),user_id=user.id,expires_at=datetime.now(timezone.utc)+timedelta(hours=8)))
    db.commit()
    response.set_cookie('barflow_session',token,max_age=8*3600,httponly=True,samesite='strict',secure=False,path='/')
    return csrf

def auth(request:Request,db:Session=Depends(get_db))->User:
    token=request.cookies.get('barflow_session')
    if not token:raise HTTPException(401,'Sessão não autenticada.')
    session=db.query(AuthSession).filter_by(token_hash=digest(token),revoked=False).first()
    if not session or session.expires_at.replace(tzinfo=timezone.utc)<datetime.now(timezone.utc):raise HTTPException(401,'Sessão expirada ou inválida.')
    user=db.get(User,session.user_id)
    if not user or not user.active:raise HTTPException(401,'Usuário inativo.')
    if user.must_change_password and request.url.path not in {'/api/auth/me','/api/auth/logout','/api/auth/change-password'}:
        raise HTTPException(403,'É obrigatório alterar a senha provisória antes de continuar.')
    if request.method in {'POST','PUT','PATCH','DELETE'}:
        csrf=request.headers.get('X-CSRF-Token','')
        if not csrf or not secrets.compare_digest(digest(csrf),session.csrf_hash):raise HTTPException(403,'Token CSRF ausente ou inválido.')
    request.state.auth_session=session
    return user

def admin(user:User=Depends(auth))->User:
    if user.role!='ADMINISTRADOR':raise HTTPException(403,'Acesso restrito ao administrador.')
    return user
