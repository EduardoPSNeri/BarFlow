"""Health check publico, sem dados do estabelecimento ou detalhes internos."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from .database import get_db

router = APIRouter()


@router.get('/health', tags=['monitoramento'])
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text('SELECT 1')).scalar_one()
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail='Serviço indisponível') from None
    return {'status': 'ok'}
