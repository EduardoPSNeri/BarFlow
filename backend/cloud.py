"""Provisionamento seguro do ambiente DEMONSTRATIVO em nuvem.

Nao modifica a instalacao local quando BARFLOW_CLOUD_DEMO nao esta ativo.
Nunca publica uma senha padrao para a internet.
"""
import os
from sqlalchemy.orm import Session


def is_cloud_demo() -> bool:
    return os.environ.get('BARFLOW_CLOUD_DEMO', '').strip() == '1'


def provision_cloud_admin(session_factory, user_model, hash_password) -> bool:
    """Cria admin apenas se o modo nuvem esta ativo e ainda nao ha administrador.

    A senha e definida exclusivamente em BARFLOW_ADMIN_PASSWORD no painel Render.
    Este procedimento nao sobrescreve contas existentes.
    """
    if not is_cloud_demo():
        return False
    password = os.environ.get('BARFLOW_ADMIN_PASSWORD', '')
    if not 12 <= len(password) <= 128 or password.lower() == 'admin':
        raise RuntimeError(
            'Deploy demonstrativo bloqueado: configure BARFLOW_ADMIN_PASSWORD '
            'com senha exclusiva de 12 a 128 caracteres no painel Render.'
        )
    with session_factory() as db:
        existing_admin = db.query(user_model).filter_by(role='ADMINISTRADOR').first()
        if existing_admin:
            # A conta provisoria nao pode liberar o acesso publico.
            if existing_admin.must_change_password:
                raise RuntimeError('Admin provisório encontrado: nao exponha essa base de dados na nuvem.')
            return False
        if db.query(user_model).filter_by(username='admin').first():
            raise RuntimeError('Usuario admin existente com perfil incorreto: verifique a base demonstrativa.')
        db.add(user_model(
            username='admin',
            role='ADMINISTRADOR',
            password_hash=hash_password(password),
            must_change_password=False,
        ))
        db.commit()
        return True
