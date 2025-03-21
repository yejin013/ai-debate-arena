from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from db.database import get_db
from models.debate import Debate as DebateModel
from schemas.debate import DebateSchema, DebateCreate, DebateUpdate

router = APIRouter(prefix="/api/v1", tags=["debates"])


@router.get("/debates/", response_model=List[DebateSchema])
def read_debates(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """토론 목록 조회"""
    debates = db.query(DebateModel).offset(skip).limit(limit).all()
    return debates


@router.post("/debates/", response_model=DebateSchema)
def create_debate(debate: DebateCreate, db: Session = Depends(get_db)):
    """새로운 토론 생성"""
    db_debate = DebateModel(**debate.model_dump())
    db.add(db_debate)
    db.commit()
    db.refresh(db_debate)
    return db_debate


@router.get("/debates/{debate_id}", response_model=DebateSchema)
def read_debate(debate_id: int, db: Session = Depends(get_db)):
    """특정 토론 조회"""
    db_debate = db.query(DebateModel).filter(DebateModel.id == debate_id).first()
    if db_debate is None:
        raise HTTPException(status_code=404, detail="Debate not found")
    return db_debate


@router.put("/debates/{debate_id}", response_model=DebateSchema)
def update_debate(debate_id: int, debate: DebateUpdate, db: Session = Depends(get_db)):
    """토론 정보 업데이트"""
    db_debate = db.query(DebateModel).filter(DebateModel.id == debate_id).first()
    if db_debate is None:
        raise HTTPException(status_code=404, detail="Debate not found")

    update_data = debate.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_debate, key, value)

    db.commit()
    db.refresh(db_debate)
    return db_debate


@router.delete("/debates/{debate_id}")
def delete_debate(debate_id: int, db: Session = Depends(get_db)):
    """토론 삭제"""
    db_debate = db.query(DebateModel).filter(DebateModel.id == debate_id).first()
    if db_debate is None:
        raise HTTPException(status_code=404, detail="Debate not found")

    db.delete(db_debate)
    db.commit()
    return {"detail": "Debate successfully deleted"}
