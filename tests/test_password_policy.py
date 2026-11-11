"""Regressão da política de senhas 4–20 caracteres."""
from pydantic import ValidationError
import pytest
from backend.schemas import ChangePasswordIn, UserIn

def test_password_change_length_boundaries():
    for value in ('abcd', 'x'*20):
        assert ChangePasswordIn(current_password='admin', new_password=value).new_password == value
    for value in ('abc', 'x'*21):
        with pytest.raises(ValidationError):
            ChangePasswordIn(current_password='admin', new_password=value)

def test_user_creation_length_boundaries():
    for value in ('abcd', 'x'*20):
        assert UserIn(username='caixa1',password=value,role='CAIXA').password == value
    for value in ('abc', 'x'*21):
        with pytest.raises(ValidationError):
            UserIn(username='caixa1',password=value,role='CAIXA')

def test_long_existing_password_can_still_be_checked():
    # A senha anterior pode ter sido criada em uma versão antiga (>20 caracteres).
    assert ChangePasswordIn(current_password='old-long-password-more-than-20',new_password='nova').new_password == 'nova'
