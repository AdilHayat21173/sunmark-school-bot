from fastapi import FastAPI
from .database import engine
from . import models
from .routers import auth, chat
from fastapi.middleware.cors import CORSMiddleware
from .routers import users

app = FastAPI(title="Chatbot API")

models.Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)


app.include_router(users.router)

@app.get("/")
def root():
    return {"message": "Chatbot API Running"}
