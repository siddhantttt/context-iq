from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, SQLModel, create_engine, Session

class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    mime_type: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Chunk(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    doc_id: int = Field(foreign_key="document.id")
    text: str

# Connection string for SQLite database
DATABASE_URL = "sqlite:///quick_rag.db"
engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session 