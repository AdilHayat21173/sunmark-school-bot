from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas, oauth2
from ..database import get_db

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

# 🔹 Get Current Logged-in User
@router.get("/me", response_model=schemas.UserOut)
def get_current_user(
    current_user: models.User = Depends(oauth2.get_current_user)
):
    return current_user


# 🔹 Get User by ID
@router.get("/{id}", response_model=schemas.UserOut)
def get_user(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    user = db.query(models.User).filter(models.User.id == id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


# 🔹 Get All Users (Optional - for admin or testing)
@router.get("/", response_model=list[schemas.UserOut])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    users = db.query(models.User).all()
    return users
