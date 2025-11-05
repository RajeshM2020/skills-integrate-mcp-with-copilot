from typing import Optional, List, Dict
from sqlmodel import SQLModel, Field, Session, create_engine, select
from pathlib import Path


class Activity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    schedule: Optional[str] = None
    max_participants: int = 0


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str


class Participation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    activity_id: int = Field(foreign_key="activity.id")
    user_id: int = Field(foreign_key="user.id")


# DB file next to the app
DB_PATH = Path(__file__).parent.parent / "data" / "activities.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

# Create engine
engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    """Create database tables."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)


def seed_initial_activities_if_needed() -> None:
    """Seed the database with some initial activities if empty.

    This keeps the first-run behaviour predictable and mirrors the
    previous in-memory data.
    """
    initial = [
        {
            "name": "Chess Club",
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
        },
        {
            "name": "Programming Class",
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
        },
        {
            "name": "Gym Class",
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
        },
        {
            "name": "Soccer Team",
            "description": "Join the school soccer team and compete in matches",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 22,
        },
        {
            "name": "Basketball Team",
            "description": "Practice and play basketball with the school team",
            "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 15,
        },
        {
            "name": "Art Club",
            "description": "Explore your creativity through painting and drawing",
            "schedule": "Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 15,
        },
        {
            "name": "Drama Club",
            "description": "Act, direct, and produce plays and performances",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 20,
        },
        {
            "name": "Math Club",
            "description": "Solve challenging problems and participate in math competitions",
            "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
            "max_participants": 10,
        },
        {
            "name": "Debate Team",
            "description": "Develop public speaking and argumentation skills",
            "schedule": "Fridays, 4:00 PM - 5:30 PM",
            "max_participants": 12,
        },
    ]

    with get_session() as session:
        count = session.exec(select(Activity)).first()
        # If no Activity rows exist, add initial set
        if count is None:
            for a in initial:
                activity = Activity(**a)
                session.add(activity)
            session.commit()


def activities_as_dict() -> Dict[str, dict]:
    """Return activities shaped like the old in-memory dict for compatibility."""
    out: Dict[str, dict] = {}
    with get_session() as session:
        activities = session.exec(select(Activity)).all()
        for activity in activities:
            # collect participants emails
            parts = (
                session.exec(
                    select(User.email)
                    .join(Participation, Participation.user_id == User.id)
                    .where(Participation.activity_id == activity.id)
                ).all()
            )
            out[activity.name] = {
                "description": activity.description,
                "schedule": activity.schedule,
                "max_participants": activity.max_participants,
                "participants": parts,
            }
    return out
