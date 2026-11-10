import uuid
from sqlmodel import Field, SQLModel, Column, DateTime, text, String
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel


# 1. The Strict Pydantic Schema (Can evolve in the future)
class RadarChartData(BaseModel):
    logical_or_structural: int = 0
    episodic_or_nostalgic: int = 0
    abstract_or_metaphorical: int = 0
    literal_or_direct: int = 0
    chaos_or_drift: int = 0

# ==========================================
# ENUMS FOR STRICT TYPING
# ==========================================
class JuryTag(str, Enum):
    VALID_BRIDGE = "Valid_Bridge"
    ANECDOTAL_REACH = "Anecdotal_Reach"
    CLUMSY_BACKPEDAL = "Clumsy_Backpedal"
    CHAOS_SPAM = "Chaos_Spam"

class ConfidenceLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class ReviewStatus(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"

# ==========================================
# DATABASE SCHEMAS
# ==========================================
class User(SQLModel, table=True):
    # Field() allows you to pass specific database constraints.
    # default_factory automatically generates a UUID when a new user is created.
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # A standard column requiring a string. We index it for faster lookups.
    username: str = Field(unique=True, index=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    # JSONB column for the culminated user-level radar chart
    attribute_radar_chart: Optional[RadarChartData] = Field(default=None, sa_column=Column(JSONB, nullable=True)) # This for the user, so all the games level attribute charts culminate into this user level chart. JSONB having few fixed attributes and score out of 100 on all the attributes. This can be rendered in FE as a radar chart.
    # Strictly enforces 'timestamp with time zone' in PostgreSQL
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), 
            nullable=False, 
            # Sets DEFAULT now() at the database level
            server_default=text("now()") 
        ),
        # Generates a timezone-aware UTC datetime if created in Python code
        default_factory=lambda: datetime.now(timezone.utc)
    )

class GameHistory(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Foreign Keys
    game_mode_id: int = Field(foreign_key="gamemode.id", index=True) # We will have another Game Mode Table, this is FK to that. 
    user_id: uuid.UUID  = Field(foreign_key="user.id", index=True) # FK to user table PK 

    # JSONB Payloads
    record: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSONB)) # JSONB Column of this shape [{start_word: "<string>", user_words: [<string>, <string>,....,<string>]}, {<same as the prev>}] for free form and forced linear, and maybe different jsob structure for semantic wormhole. Also not worrying about normalization as this is a game history record and therefore there will be no insertion, updation, deletion anomalies, correct me if I am wrong in making this decision please Gemini or my LLM Guide. Also the parenthesis code comment style justifications will be part of the <string> of the user_words and that is fine now since our local LLM will see it and understand.
    attribute_radar_chart: RadarChartData = Field(default_factory=RadarChartData, sa_column=Column(JSONB)) # JSONB having few fixed attributes and score out of 100 on all the attributes. This can be rendered in FE as a radar chart.

    karma_profile: str = Field(nullable=False) # It won't be called Karma profile in the FE. Also only if user was being too chaotic or backpedaling or being too random, only then we make it a roast, otherwise it will be a friendly personality analysis.
    game_finished_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), 
            nullable=False, 
            # Sets DEFAULT now() at the database level
            server_default=text("now()") 
        ),
        # Generates a timezone-aware UTC datetime if created in Python code
        default_factory=lambda: datetime.now(timezone.utc)
    ) # This is actually when the game session was inserted into this table, roughly it will be when the game was finished by the user.

class GameMode(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str = Field(nullable=False, unique=True) # It will be non nullable and only these values are allowed = ["Simple Free-Form (No HITL, no brain graph, no skeptic, no justifications, no silent judge)", "Free-Form", "Forced Chain", "Forced Radial", "Semantic Wormhole", "Humanities-Sciences Cross Wiring wormhole"]

class AdminReviewQueue(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # user_id: uuid.UUID # FK to user table PK, dropping as this violates 3NF, could cause problems. Insertion bug, not anomaly could cause data inconsistency, like Game history saying game 999 belongs to Alice, but Admin tablr saying game 999 belongs to Bob

    # Foreign Key to track which game session caused the dispute
    game_history_id: uuid.UUID = Field(foreign_key="gamehistory.id", index=True) # FK to GameHistory table PK, this is just kept to track which session caused this entry, of course using this we can go to GameHistory Table and get the user, but because I may have to store per user verified_bridges, I am storing the user_id directly here. Tell me if this is good DB design. Also even if it is good, are we breaking 3NF? good design if you think app level integrity is guaranteed
    # disputed_pair: list # JSONB type of the form [<string1>, <string2>] Always just 2 words or phrases, this array is always of length 2 items and the items are strings
    
    source_word: str = Field(nullable=False)
    target_word: str = Field(nullable=False)
    user_justification: str = Field(nullable=False)

    # Enums enforced at the SQLAlchemy level as Strings
    jury_tag: JuryTag = Field(sa_column=Column(String, nullable=False)) # Strictly restricted to "Valid_Bridge" or "Anecdotal_Reach", "Clumsy_Backpedal", "Chaos_Spam". Not sure about what enums are, and should we be using that data type instead of str?
    confidence_level: ConfidenceLevel = Field(sa_column=Column(String, nullable=False)) # Strictly restricted to "High", "Medium", "Low". It is a gauge of how convincing the user's justification is. Same question I have regarding enums here too.
    status: ReviewStatus = Field(sa_column=Column(String, nullable=False)) # Either "Pending", "Approved" or "Rejected". If rejected it just does not appear in the admin dashboard. 
    is_global_approval: Optional[bool] = Field(default=None) # Nullable, if approves status then this column should either be True or False. If true, it is a global verified bridge that applies to all users. If False, then this bridge appears only to this user. 
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), 
            nullable=False, 
            # Sets DEFAULT now() at the database level
            server_default=text("now()") 
        ),
        # Generates a timezone-aware UTC datetime if created in Python code
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))) # Whenever admin makes updates. Only the latest update timestamp will be recorded, in case they make multiple updates.

class VerifiedBridges(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    source_word: str = Field(index=True, nullable=False)
    target_word: str = Field(index=True, nullable=False)
    is_global: bool = Field(default=False, nullable=False)
    # Nullable FK. If is_global is False, this binds the bridge to a specific user
    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id", index=True) # Nullable. If is_gloabl is False, then this will have a user_id, FK to User Table PK, otherwise it will be Null
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), 
            nullable=False, 
            # Sets DEFAULT now() at the database level
            server_default=text("now()") 
        ),
        # Generates a timezone-aware UTC datetime if created in Python code
        default_factory=lambda: datetime.now(timezone.utc)
    )
