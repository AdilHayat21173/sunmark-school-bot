from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, oauth2
from ..database import get_db
from src.graphs.graph import app

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/session")
def create_session(db: Session = Depends(get_db),
                   current_user: models.User = Depends(oauth2.get_current_user)):

    session = models.ChatSession(user_id=current_user.id)
    db.add(session)
    db.commit()
    db.refresh(session)

    return session

@router.get("/sessions")
def get_sessions(db: Session = Depends(get_db),
                 current_user: models.User = Depends(oauth2.get_current_user)):

    return db.query(models.ChatSession)\
        .filter(models.ChatSession.user_id == current_user.id)\
        .all()

@router.post("/{session_id}")
def chat(session_id: int,
         message: str,
         db: Session = Depends(get_db),
         current_user: models.User = Depends(oauth2.get_current_user)):

    session = db.query(models.ChatSession)\
        .filter(models.ChatSession.id == session_id,
                models.ChatSession.user_id == current_user.id)\
        .first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db.add(models.Message(session_id=session_id, role="user", content=message))
    db.commit()

    final_state = app.invoke({"question": message})
    response = final_state["generation"]

    db.add(models.Message(session_id=session_id, role="assistant", content=response))
    db.commit()

    return {"response": response}

@router.get("/{session_id}/messages")
def get_messages(session_id: int,
                 db: Session = Depends(get_db),
                 current_user: models.User = Depends(oauth2.get_current_user)):

    return db.query(models.Message)\
        .join(models.ChatSession)\
        .filter(models.ChatSession.id == session_id,
                models.ChatSession.user_id == current_user.id)\
        .all()
