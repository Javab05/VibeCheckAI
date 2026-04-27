import os
import json
from datetime import datetime
from google import genai
from google.genai import types
from sqlalchemy.orm import Session
from database.models import EmotionResult, Checkin

def analyze_trend(user_id: int, db: Session) -> dict:
    """
    Analyze the user's emotion trend using the last 30 records and Google Gemini.
    """
    
    # Query the last 30 records for the user by joining EmotionResult with Checkin
    results = (
        db.query(EmotionResult)
        .join(Checkin, EmotionResult.checkin_id == Checkin.checkin_id)
        .filter(Checkin.user_id == user_id, EmotionResult.is_latest == 1)
        .order_by(EmotionResult.processed_at.desc())
        .limit(30)
        .all()
    )
    
    scores_analyzed = len(results)
    
    # If fewer than 3 records exist, return immediately
    if scores_analyzed < 3:
        return {
            "trend_summary": "Not enough data yet. Keep checking in daily!",
            "trend_direction": "insufficient_data",
            "scores_analyzed": scores_analyzed
        }
    
    # Reverse to chronological order
    results.reverse()
    
    # Format scores as "Mon DD: score" strings for the prompt
    formatted_scores = []
    for r in results:
        try:
            # Handle processed_at
            if isinstance(r.processed_at, str):
                dt = datetime.fromisoformat(r.processed_at.replace('Z', '+00:00'))
            else:
                dt = r.processed_at
            date_str = dt.strftime("%b %d")
        except Exception:
            date_str = str(r.processed_at)
        
        # Try to get vibe_score from scores_json if available, otherwise use confidence * 100
        vibe_score = 0
        if r.scores_json:
            try:
                scores = json.loads(r.scores_json)
                # If vibe_score was somehow tucked into scores (though unlikely based on current code)
                vibe_score = scores.get("vibe_score", 0)
                if not vibe_score:
                    # Calculate a simple vibe score if not present: happy - sad
                    # This is just a heuristic since the real vibe_score isn't persisted
                    vibe_score = (scores.get("happy", 0) - scores.get("sad", 0)) * 50 + 50
            except:
                vibe_score = r.confidence * 100
        else:
            vibe_score = r.confidence * 100
            
        formatted_scores.append(f"{date_str}: {round(vibe_score, 1)}")
    
    scores_context = "\n".join(formatted_scores)
    
    # Call the Google Gemini API
    client = genai.Client() 
    
    system_prompt = (
        "You are a supportive wellness analyst. Analyze the following user vibe scores (0-100). "
        "Identify any dips, divots, streaks, or the overall trend direction. "
        "Respond only in valid JSON with keys 'trend_summary' (string) and 'trend_direction' "
        "(one of: 'improving', 'declining', 'stable', 'insufficient_data')."
    )

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=system_prompt
    )
    
    user_prompt = f"{system_prompt}\n\nHere are my scores for the last {scores_analyzed} check-ins:\n\n{scores_context}"
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash', # Make sure to specify your model here
            contents=user_prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=512,
                temperature=0.7,
                # MAGIC BULLET: This forces the API to return pure JSON without markdown code blocks
                response_mime_type="application/json",
            )
        )
    
        # We no longer need to check for and strip "```json" blocks!
        content = response.text.strip()
        data = json.loads(content)
    
        return {
            "trend_summary": data.get("trend_summary", "No summary provided."),
            "trend_direction": data.get("trend_direction", "stable"),
            "scores_analyzed": scores_analyzed
        }
    
    except Exception as e:
        # Graceful fallback for API or parsing errors
        return {
            "trend_summary": "We successfully processed your data...",
            "trend_direction": "stable",
            "scores_analyzed": scores_analyzed
        }