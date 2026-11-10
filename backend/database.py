import os
from dotenv import load_dotenv
from sqlmodel import create_engine, Session

load_dotenv()
DATABASE_URL = os.environ["DATABASE_URL"]

# 1. Create the Engine
# echo=True is an amazing learning tool: it will print the raw SQL 
# commands directly into your terminal whenever a database action occurs.
engine = create_engine(DATABASE_URL, echo=True)

# 2. The Dependency Injection function
def get_session():
    """
    FastAPI will call this function every time a route needs database access.
    The 'yield' keyword pauses this function, hands the session to the route, 
    and then automatically closes the session when the route finishes.
    """
    with Session(engine) as session:
        yield session