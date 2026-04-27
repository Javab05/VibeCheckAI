import unittest
from unittest.mock import MagicMock, patch
import json
import os
import sys

# Add the vibechecker-ai directory to the path so 'backend' and 'database' can be found
# regardless of where this script is called from.
current_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(current_dir) == 'vibechecker-ai':
    sys.path.insert(0, current_dir)
else:
    # If called from within tests/
    parent_dir = os.path.dirname(current_dir)
    if os.path.basename(parent_dir) == 'vibechecker-ai':
        sys.path.insert(0, parent_dir)

from backend.services.trend_analysis import analyze_trend
from backend.routes.trend import trend_routes
from database.models import EmotionResult, Checkin
from flask import Flask
from sqlalchemy.orm import Session

class TestTrendService(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.user_id = 1

    def test_insufficient_data(self):
        # Setup: fewer than 3 records
        mock_query = self.db.query.return_value
        mock_join = mock_query.join.return_value
        mock_filter = mock_join.filter.return_value
        mock_order_by = mock_filter.order_by.return_value
        mock_limit = mock_order_by.limit.return_value
        
        mock_limit.all.return_value = [
            EmotionResult(result_id=1, checkin_id=1, confidence=0.8, scores_json=json.dumps({"happy": 0.8, "sad": 0.1}), processed_at="2026-04-20T10:00:00Z"),
            EmotionResult(result_id=2, checkin_id=2, confidence=0.7, scores_json=json.dumps({"happy": 0.7, "sad": 0.2}), processed_at="2026-04-21T10:00:00Z"),
        ]
        
        result = analyze_trend(self.user_id, self.db)
        
        self.assertEqual(result["trend_direction"], "insufficient_data")
        self.assertEqual(result["scores_analyzed"], 2)
        self.assertIn("Not enough data", result["trend_summary"])

    # We patch the exact location where genai is imported in your service file
    @patch("backend.services.trend_analysis.genai.Client")
    def test_analyze_trend_success(self, mock_client_class):
        # Setup: 3 records
        mock_query = self.db.query.return_value
        mock_join = mock_query.join.return_value
        mock_filter = mock_join.filter.return_value
        mock_order_by = mock_filter.order_by.return_value
        mock_limit = mock_order_by.limit.return_value
        
        mock_limit.all.return_value = [
            EmotionResult(result_id=3, checkin_id=3, confidence=0.9, scores_json=json.dumps({"happy": 0.9, "sad": 0.05}), processed_at="2026-04-22T10:00:00Z"),
            EmotionResult(result_id=2, checkin_id=2, confidence=0.7, scores_json=json.dumps({"happy": 0.7, "sad": 0.2}), processed_at="2026-04-21T10:00:00Z"),
            EmotionResult(result_id=1, checkin_id=1, confidence=0.8, scores_json=json.dumps({"happy": 0.8, "sad": 0.1}), processed_at="2026-04-20T10:00:00Z"),
        ]
        
        # Mock Gemini response for the new SDK
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "trend_summary": "Your mood is improving steadily!",
            "trend_direction": "improving"
        })
        
        # Map the mock response to the new `client.models.generate_content` structure
        mock_client_instance.models.generate_content.return_value = mock_response

        # Execute
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
            result = analyze_trend(self.user_id, self.db)
        
        # Verify
        self.assertEqual(result["trend_direction"], "improving")
        self.assertEqual(result["scores_analyzed"], 3)
        self.assertEqual(result["trend_summary"], "Your mood is improving steadily!")
        
        # Verify Gemini was called
        self.assertTrue(mock_client_instance.models.generate_content.called)

class TestTrendRoute(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(trend_routes, url_prefix="/trend")
        self.client = self.app.test_client()

    @patch("backend.routes.trend.analyze_trend")
    @patch("backend.routes.trend.get_db")
    def test_get_trend_route_success(self, mock_get_db, mock_analyze_trend):
        # Mock DB
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = mock_db
        
        # Mock Service
        mock_analyze_trend.return_value = {
            "trend_summary": "Stable vibes.",
            "trend_direction": "stable",
            "scores_analyzed": 5
        }
        
        resp = self.client.get("/trend/1")
        
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["trend_direction"], "stable")
        self.assertEqual(data["scores_analyzed"], 5)
        mock_db.close.assert_called_once()

    @patch("backend.routes.trend.analyze_trend")
    @patch("backend.routes.trend.get_db")
    def test_get_trend_route_not_found(self, mock_get_db, mock_analyze_trend):
        mock_get_db.return_value = MagicMock(spec=Session)
        
        # Mock Service returning 0 scores
        mock_analyze_trend.return_value = {
            "trend_summary": "No data.",
            "trend_direction": "insufficient_data",
            "scores_analyzed": 0
        }
        
        resp = self.client.get("/trend/1")
        
        self.assertEqual(resp.status_code, 404)
        self.assertIn("No vibe scores found", resp.get_json()["error"])

if __name__ == "__main__":
    unittest.main()