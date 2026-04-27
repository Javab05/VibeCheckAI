
import os
import sys

# Add the project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from database.models import get_db, Checkin, EmotionResult
from sqlalchemy import func

db = get_db()
user_id = 3

print(f"--- Diagnostic for User ID: {user_id} ---")

# Check Checkins
checkins = db.query(Checkin).filter(Checkin.user_id == user_id).all()
print(f"Total check-ins for user 3: {len(checkins)}")
if checkins:
    print(f"Sample Checkin captured_at: {checkins[0].captured_at}")
    print(f"Sample Checkin created_at: {checkins[0].created_at}")

# Check EmotionResults
results = (
    db.query(EmotionResult)
    .join(Checkin, EmotionResult.checkin_id == Checkin.checkin_id)
    .filter(Checkin.user_id == user_id)
    .all()
)
print(f"Total emotion results for user 3: {len(results)}")
if results:
    print(f"Sample EmotionResult processed_at: {results[0].processed_at}")
    print(f"Sample EmotionResult is_latest: {results[0].is_latest}")

# Check Year Filter specifically
year = '2026'
year_results = (
    db.query(EmotionResult)
    .join(Checkin, EmotionResult.checkin_id == Checkin.checkin_id)
    .filter(Checkin.user_id == user_id, EmotionResult.is_latest == 1)
    .filter(func.strftime('%Y', EmotionResult.processed_at) == year)
    .all()
)
print(f"Emotion results for year {year}: {len(year_results)}")

db.close()
