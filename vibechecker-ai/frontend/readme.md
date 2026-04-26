# Setup Instructions

## 1. Verify Node.js Installation
Make sure Node.js is installed before testing the frontend.

Check your Node.js version in PowerShell:
node --version

If this prints a version number, Node.js is installed correctly.

---

## 2. Set Up and Activate the Python Virtual Environment
Open a terminal in your IDE. If (.venv) does not appear at the start of your terminal path, activate it manually.

If the .venv folder does NOT exist:
Make sure you are in the project root folder (vibechecker-ai/) and run:
python -m venv .venv

To activate .venv in the terminal:
.\.venv\Scripts\activate

---

## 3. Navigating the Project
Use this command to move into a folder:
cd folder_name

Note: All following commands must be run while .venv is active.

---

## 4. Install Backend Requirements
From the project root (vibechecker-ai/), run:
pip install -r requirements.txt

---

# Running the App

## 1. Initialize the Database
From the project root (vibechecker-ai/), run:
python -m database.init_db

Expected output:
Database created: vibechecker.db
Image storage:    storage/images/
Tables:
  - users
  - checkins
  - emotion_results
  - seasonal_summaries

You should now see a new file:
database/vibechecker.db

---

## 2. Start the Backend
From the project root, run:
python backend\flaskApp.py

Expected output:
* Serving Flask app 'flaskApp'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
 * Running on http://10.xxx.xx.xxx:5000
Press CTRL+C to quit

---

## 3. Start the Frontend (Expo)
Open a new terminal, then navigate to the frontend folder:
cd frontend

Start Expo:
npx expo start

If Node.js is installed correctly, Expo will launch and display a QR code.

Download the Expo Go app on Android or iOS and scan the QR code, or press "w" to open the web version.

---

# Notes
- Your backend and mobile device must be on the same WiFi network.
- Creating an account with an existing email will currently show a "can't connect to backend" error because duplicate-account logic is not yet implemented.
