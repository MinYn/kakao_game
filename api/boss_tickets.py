"""
보스몹 입장권 관련 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from models.database import get_db
from models.models import BossTicket
from api.schemas import BossTicketCreate, BossTicketUpdate, BossTicketResponse

router = APIRouter(prefix="/api/boss-tickets", tags=["boss-tickets"])


@router.get("/{user_id}", response_model=BossTicketResponse)
def get_boss_tickets(user_id: str, db: Session = Depends(get_db)):
    """보스몹 입장권 조회"""
    ticket = db.query(BossTicket).filter(BossTicket.user_id == user_id).first()
    if not ticket:
        ticket = BossTicket(user_id=user_id, tickets=0)
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
    return ticket


@router.post("/{user_id}/add", response_model=BossTicketResponse)
def add_boss_ticket(
    user_id: str,
    amount: int = Query(1, gt=0, description="추가할 입장권 수량"),
    db: Session = Depends(get_db)
):
    """보스몹 입장권 추가"""
    ticket = db.query(BossTicket).filter(BossTicket.user_id == user_id).first()
    
    if ticket:
        ticket.tickets += amount
    else:
        ticket = BossTicket(user_id=user_id, tickets=amount)
        db.add(ticket)
    
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{user_id}/use", response_model=BossTicketResponse)
def use_boss_ticket(
    user_id: str,
    amount: int = Query(1, gt=0, description="사용할 입장권 수량"),
    db: Session = Depends(get_db)
):
    """보스몹 입장권 사용"""
    ticket = db.query(BossTicket).filter(BossTicket.user_id == user_id).first()
    
    if not ticket or ticket.tickets < amount:
        raise HTTPException(status_code=400, detail="입장권이 부족합니다")
    
    ticket.tickets -= amount
    db.commit()
    db.refresh(ticket)
    return ticket


@router.put("/{user_id}", response_model=BossTicketResponse)
def set_boss_tickets(
    user_id: str,
    ticket_update: BossTicketUpdate,
    db: Session = Depends(get_db)
):
    """보스몹 입장권 설정"""
    ticket = db.query(BossTicket).filter(BossTicket.user_id == user_id).first()
    
    if ticket:
        ticket.tickets = ticket_update.tickets
    else:
        ticket = BossTicket(user_id=user_id, tickets=ticket_update.tickets)
        db.add(ticket)
    
    db.commit()
    db.refresh(ticket)
    return ticket
