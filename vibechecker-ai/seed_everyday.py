import os
import glob
import requests
import time

BASE_URL = "http://localhost:5000"
USER_EMAIL = "everyday@test.dev"
USER_PASSWORD = "password"
USER_NAME = "Everyday User"
IMAGE_DIR = os.path.join(os.path.dirname(__file__), "Everyday")

def setup_user():
    """Ensure the test user exists and return their user_id."""
    print(f"Checking for user: {USER_EMAIL}...")
    
    # 1. Try to login
    login_data = {"email": USER_EMAIL, "password": USER_PASSWORD}
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            user_id = response.json().get("user_id")
            print(f"User found. ID: {user_id}")
            return user_id
        
        # 2. If login fails (user not found), register
        if response.status_code == 404:
            print("User not found. Registering...")
            reg_data = {
                "username": USER_NAME,
                "email": USER_EMAIL,
                "password": USER_PASSWORD
            }
            reg_response = requests.post(f"{BASE_URL}/auth/register", json=reg_data)
            if reg_response.status_code == 201:
                user_id = reg_response.json().get("user_id")
                print(f"User registered successfully. ID: {user_id}")
                return user_id
            else:
                print(f"Failed to register: {reg_response.text}")
        else:
            print(f"Login failed with status {response.status_code}: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the backend. Is the Flask server running on port 5000?")
        return None
    
    return None

def process_images(user_id):
    """Find all images in the Everyday directory and upload them."""
    # Common image extensions
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp']
    image_paths = []
    for ext in extensions:
        # Recursive search for all images in Everyday/**
        image_paths.extend(glob.glob(os.path.join(IMAGE_DIR, "**", ext), recursive=True))
    
    if not image_paths:
        print(f"No images found in {IMAGE_DIR}")
        return

    print(f"Found {len(image_paths)} images. Starting upload...")
    
    success_count = 0
    fail_count = 0
    
    for i, img_path in enumerate(image_paths):
        filename = os.path.basename(img_path)
        print(f"[{i+1}/{len(image_paths)}] Processing {filename}...", end="\r")
        
        try:
            with open(img_path, 'rb') as f:
                files = {'image': (filename, f, 'image/jpeg')}
                data = {'user_id': user_id}
                
                response = requests.post(f"{BASE_URL}/checkin/upload", files=files, data=data)
                
                if response.status_code == 200:
                    success_count += 1
                else:
                    print(f"\nFailed to process {filename}: {response.json().get('error', response.text)}")
                    fail_count += 1
                    
        except Exception as e:
            print(f"\nError processing {filename}: {e}")
            fail_count += 1
            
        # Optional: slight delay to not overwhelm the inference server
        time.sleep(0.1)

    print(f"\nFinished processing.")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")

if __name__ == "__main__":
    uid = setup_user()
    if uid:
        process_images(uid)
    else:
        print("Setup failed. Please ensure the Flask server is running and the database is accessible.")
