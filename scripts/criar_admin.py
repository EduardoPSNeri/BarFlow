"""Cria admin/admin provisório somente na primeira instalação.
Acesso operacional permanece bloqueado até a troca da senha no navegador.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.database import Base,engine,SessionLocal
from sqlalchemy import inspect, text
from backend.models import User
from backend.security import hash_password

# Migração mínima para bancos existentes (não apaga usuários nem dados).
with engine.begin() as conn:
    if 'users' in inspect(conn).get_table_names():
        existing={column['name'] for column in inspect(conn).get_columns('users')}
        if 'must_change_password' not in existing:
            conn.execute(text('ALTER TABLE users ADD COLUMN must_change_password BOOLEAN NOT NULL DEFAULT 0'))
Base.metadata.create_all(engine)
with SessionLocal() as db:
    if db.query(User).filter_by(role='ADMINISTRADOR').first():
        print('Administrador existente preservado. Nenhuma senha foi alterada.')
    elif db.query(User).filter_by(username='admin').first():
        sys.exit('Usuario admin ja existe com outro perfil. Resolva o conflito manualmente.')
    else:
        db.add(User(username='admin',role='ADMINISTRADOR',password_hash=hash_password('admin'),must_change_password=True))
        db.commit()
        print('Usuario provisório criado: admin / admin')
        print('A TROCA DE SENHA É OBRIGATÓRIA NO PRIMEIRO ACESSO.')
