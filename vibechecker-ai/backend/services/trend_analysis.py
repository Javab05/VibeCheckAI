import os
import json
from datetime import datetime
from google import genai
from google.genai import types
from sqlalchemy.orm import Session
from database.models import EmotionResult, Checkin

from sqlalchemy import func

def analyze_trend(user_id: int, db: Session, year: int = None) -> dict:
    """
    Analyze the user's emotion trend using the last 30 records (or a specific year) and Google Gemini.
    """
    
    # Query records for the user by joining EmotionResult with Checkin
    query = (
        db.query(EmotionResult)
        .join(Checkin, EmotionResult.checkin_id == Checkin.checkin_id)
        .filter(Checkin.user_id == user_id, EmotionResult.is_latest == 1)
    )

    if year:
        # Filter by season_year in the Checkin table
        query = query.filter(Checkin.season_year == year)
        results = query.order_by(EmotionResult.processed_at.asc()).all()
    else:
        # Last 30 records
        results = (
            query.order_by(EmotionResult.processed_at.desc())
            .limit(30)
            .all()
        )
        # Reverse to chronological order for the last 30
        results.reverse()
    
    scores_analyzed = len(results)
    
    # Early return for insufficient data ONLY if year is not provided
    if year is None and scores_analyzed < 3:
        return {
            "trend_summary": "Not enough data yet. Keep checking in daily!",
            "trend_direction": "insufficient_data",
            "scores_analyzed": scores_analyzed
        }
    
    # If year is provided but 0 records, we still need to return 0 scores analyzed
    if scores_analyzed == 0:
        return {
            "trend_summary": "No data found for the selected period.",
            "trend_direction": "insufficient_data",
            "scores_analyzed": 0
        }
    
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
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "trend_summary": {"type": "STRING"},
            "trend_direction": {
                "type": "STRING", 
                "enum": ["improving", "declining", "stable", "insufficient_data"]
            }
        },
        "required": ["trend_summary", "trend_direction"]
    }

    client = genai.Client() 
    
    system_prompt = (
        "You are a supportive wellness analyst. Analyze the following user vibe scores (0-100). "
        "Identify any dips, divots, streaks, or the overall trend direction."
    )

    user_prompt = f"Here are my scores for the last {scores_analyzed} check-ins:\n\n{scores_context}"
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=512,
                temperature=0.7,
                response_mime_type="application/json",
                response_schema=response_schema,
            )
        )
    
        content = response.text.strip()
        data = json.loads(content)
    
        return {
            "trend_summary": data.get("trend_summary", "No summary provided."),
            "trend_direction": data.get("trend_direction", "stable"),
            "scores_analyzed": scores_analyzed
        }
    
    except Exception as e:
        print(f"Error calling Gemini API: {e}") # Log the actual error
        return {
            "trend_summary": f"We successfully processed your data, but encountered an error generating the summary: {str(e)[:100]}",
            "trend_direction": "stable",
            "scores_analyzed": scores_analyzed
        }