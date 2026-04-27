import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add current directory to path so database can be found
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from database.models import User, Checkin, EmotionResult, Base

# SQLite path
DB_PATH = os.path.join(current_dir, "database", "vibechecker.db")
engine = create_engine(f"sqlite:///{DB_PATH}")
Session = sessionmaker(bind=engine)

def spread_dates():
    session = Session()
    try:
        # 1. Find the test user
        user = session.query(User).filter(User.email == "everyday@test.dev").first()
        if not user:
            print("User everyday@test.dev not found.")
            return

        print(f"Found user: {user.username} (ID: {user.user_id})")

        # 2. Get all checkins for this user, sorted by ID (original upload order)
        checkins = session.query(Checkin).filter(Checkin.user_id == user.user_id).order_by(Checkin.checkin_id.asc()).all()
        
        if not checkins:
            print("No checkins found for this user.")
            return

        print(f"Spreading {len(checkins)} checkins over the last {len(checkins)} days...")

        # 3. Calculate start date (X days ago)
        # We'll make the last checkin "today" and work backwards
        now = datetime.utcnow()
        
        for i, checkin in enumerate(reversed(checkins)):
            # Calculate the target date: today - i days
            target_date = now - timedelta(days=i)
            # Add some slight variation in time so they aren't all exactly the same HH:MM:SS
            target_date = target_date.replace(hour=12, minute=0, second=0, microsecond=0) + timedelta(minutes=i*2)
            
            new_iso_date = target_date.isoformat() + "Z"
            
            # Update Checkin
            checkin.captured_at = new_iso_date
            
            # Update associated EmotionResults processed_at
            # We'll just set it to the same date for consistency in this simulation
            results = session.query(EmotionResult).filter(EmotionResult.checkin_id == checkin.checkin_id).all()
            for res in results:
                res.processed_at = target_date

        session.commit()
        print("Successfully updated all check-in dates to be unique and spread daily.")

    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    spread_dates()
