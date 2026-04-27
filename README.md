# VibeCheckAI

VibeCheckAI is a wellness tracking application that uses a multimodal ML pipeline to analyze your daily selfies and provide emotional insights. It specifically helps detect patterns like Seasonal Affective Disorder (SAD) by tracking your "vibe trend" throughout the year.

---

## Getting Started

### 1. Prerequisites
- **Python 3.10+**
- **Node.js & npm** (for the Expo frontend)
- **Google Gemini API Key**: [Get one here](https://ai.google.dev/)

### 2. Backend Setup
1. **Create and Activate Virtual Environment**:
   ```bash
   # From the project root (VibeCheckAI/)
   python -m venv .venv
   # Windows
   .\.venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r vibechecker-ai/requirements.txt
   ```

3. **Environment Variables**:
   Create a `.env` file inside the `vibechecker-ai/` directory:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

### 3. Database Initialization & Seeding
All database commands should be run from the `vibechecker-ai/` directory.

1. **Initialize Database**:
   ```bash
   cd vibechecker-ai
   python -m database.init_db
   ```

2. **Seed Initial Test Data**:
   ```bash
   python -m database.seed_db
   ```

3. **(Optional) Seed Everyday Data**:
   If you have a directory of daily photos in `vibechecker-ai/Everyday/`, you can ingest them into the system:
   ```bash
   # 1. Start the backend server first (see step 4)
   # 2. Run the seed script:
   python seed_everyday.py
   
   # 3. Spread the dates (to make them look like 90 days of history):
   python spread_dates.py
   ```

### 4. Running the Project

#### **Start the Backend** (Flask)
```bash
# From vibechecker-ai/
python backend/flaskApp.py
```
The server will run on `http://localhost:5000`.

#### **Start the Frontend** (Expo)
```bash
# Open a new terminal
cd vibechecker-ai/frontend
npm install
npx expo start
```
Scan the QR code with **Expo Go** (iOS/Android) or press `w` for the web version.

---

## Features & Logic

### Vibe Score Scale
The app calculates a 0-100 "Vibe Score" based on seven detected emotions:
- **Happy**: 100
- **Surprise**: 70
- **Neutral**: 50
- **Fear**: 30
- **Sad**: 20
- **Angry**: 10
- **Disgust**: 5

### AI Analysis
The **Year Summary** feature uses Google Gemini (2.5 Flash) to analyze your data. It looks for:
- **SAD Risk**: Clusters of low scores during winter months (Nov-Feb).
- **Significant Gaps**: Sustained dips of 20+ points lasting 3+ days.
- **Trend Insights**: AI-generated context for your emotional journey.

---

## Project Structure

- `vibechecker-ai/backend/`: Flask server and API routes.
- `vibechecker-ai/frontend/`: Expo/React Native mobile application.
- `vibechecker-ai/database/`: SQLAlchemy models and SQLite database.
- `vibechecker-ai/ml/`: Multimodal emotion detection model and inference logic.
- `vibechecker-ai/cv/`: MediaPipe face landmark extraction.
- `vibechecker-ai/storage/`: Local image storage for uploaded selfies.

---

## Maintenance & Diagnostics
- `inspect_db.py`: Quick script to view the current database state.
- `seed_everyday.py`: Ingests bulk photos for testing.
- `spread_dates.py`: Distributes bulk-uploaded photos across a calendar to simulate long-term usage.
