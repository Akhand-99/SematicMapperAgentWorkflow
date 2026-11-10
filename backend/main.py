from fastapi import FastAPI, Depends
from sqlmodel import Session
from database import get_session
from models.models import User

app = FastAPI(title="Semantic Mapper API")


@app.get("/health")
async def root():
    return {"message": "Healthy"}

@app.post("/test-db")
def test_database_connection(session: Session = Depends(get_session)):
    # 1. Create a dummy user in Python RAM
    dummy_user = User(username="Test_Mom", hashed_password="fake_password_123")

    # 2. Insert into DB
    session.add(dummy_user)
    session.commit()

    # 3. Fetch the newly generated UUID and timestamp back from Postgres
    session.refresh(dummy_user)

    # 4. Save the data to a dictionary to prove it worked
    proof = {
        "message": "Database connection successful! User inserted and deleted.",
        "inserted_user_id": dummy_user.id,
        "inserted_username": dummy_user.username,
        "created_at": dummy_user.created_at
    }

    # 5. Clean up
    session.delete(dummy_user)
    session.commit()

    return proof