"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

from . import db
from sqlmodel import select

# Initialize database and seed initial activities on startup
db.init_db()
db.seed_initial_activities_if_needed()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return db.activities_as_dict()


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    with db.get_session() as session:
        # Find activity by name
        activity = session.exec(
            select(db.Activity).where(db.Activity.name == activity_name)
        ).first()
        if activity is None:
            raise HTTPException(status_code=404, detail="Activity not found")

        # Ensure user exists (create if missing)
        user = session.exec(select(db.User).where(db.User.email == email)).first()
        if user is None:
            user = db.User(email=email)
            session.add(user)
            session.commit()
            session.refresh(user)

        # Check if already signed up
        existing = session.exec(
            select(db.Participation).where(
                db.Participation.activity_id == activity.id,
                db.Participation.user_id == user.id,
            )
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Student is already signed up")

        # Check capacity
        participants = session.exec(
            select(db.Participation).where(db.Participation.activity_id == activity.id)
        ).all()
        if activity.max_participants and len(participants) >= activity.max_participants:
            raise HTTPException(status_code=400, detail="Activity is full")

        # Add participation
        p = db.Participation(activity_id=activity.id, user_id=user.id)
        session.add(p)
        session.commit()
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    with db.get_session() as session:
        activity = session.exec(
            select(db.Activity).where(db.Activity.name == activity_name)
        ).first()
        if activity is None:
            raise HTTPException(status_code=404, detail="Activity not found")

        user = session.exec(select(db.User).where(db.User.email == email)).first()
        if user is None:
            raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

        participation = session.exec(
            select(db.Participation).where(
                db.Participation.activity_id == activity.id,
                db.Participation.user_id == user.id,
            )
        ).first()
        if participation is None:
            raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

        session.delete(participation)
        session.commit()
    return {"message": f"Unregistered {email} from {activity_name}"}
