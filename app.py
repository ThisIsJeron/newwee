# app.py - The main Flask application
import os
import random
import threading
import time
import requests
from flask import Flask, send_file, request, redirect, url_for, render_template
from werkzeug.utils import safe_join

app = Flask(__name__)

MEDIA_FOLDER = "media"
SUBREDDIT_URL = "https://www.reddit.com/r/guineapigs/top.json?sort=top&t=week"
INTERVAL_SECONDS = 3600  # e.g., check Reddit every hour

# In-memory ratings store: {filename: integer_score}
# Positive means net upvotes, negative means net downvotes.
RATINGS = {}

def scrape_reddit_images():
    """
    Fetch top posts of the week from r/guineapigs, check for image URLs,
    and store them in MEDIA_FOLDER if they are new.
    """
    headers = {"User-Agent": "randomPhotoScraper/1.0"}
    try:
        response = requests.get(SUBREDDIT_URL, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        for child in data["data"]["children"]:
            post_data = child["data"]
            image_url = post_data.get("url_overridden_by_dest", "")
            post_id = post_data.get("id", "")

            if image_url.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                _, file_ext = os.path.splitext(image_url)
                filename = f"{post_id}{file_ext}"
                file_path = os.path.join(MEDIA_FOLDER, filename)

                if not os.path.exists(file_path):
                    print(f"Downloading new image: {image_url}")
                    img_data = requests.get(image_url, timeout=10).content
                    with open(file_path, "wb") as file:
                        file.write(img_data)
    except Exception as e:
        print(f"Error while scraping Reddit: {e}")

def start_background_scraper():
    """
    Starts a background thread that periodically calls scrape_reddit_images().
    """
    def scrape_loop():
        while True:
            scrape_reddit_images()
            time.sleep(INTERVAL_SECONDS)

    thread = threading.Thread(target=scrape_loop, daemon=True)
    thread.start()

@app.route("/")
def show_photo():
    """
    Displays a web page with a random photo and Up/Down/Next buttons.
    """
    # Ensure media folder
    if not os.path.isdir(MEDIA_FOLDER):
        os.makedirs(MEDIA_FOLDER, exist_ok=True)

    files = [
        f for f in os.listdir(MEDIA_FOLDER)
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".gif"))
    ]
    if not files:
        return "No images found in the 'media' directory."

    chosen_file = random.choice(files)

    # Initialize the rating if we haven't seen this file yet
    if chosen_file not in RATINGS:
        RATINGS[chosen_file] = 0

    rating_value = RATINGS[chosen_file]

    # Render HTML with the chosen_file
    return render_template(
        "index.html", 
        chosen_file=chosen_file, 
        rating_value=rating_value
    )

@app.route("/media/<filename>")
def serve_image(filename):
    """
    Serves the file from the MEDIA_FOLDER. 
    """
    filepath = safe_join(MEDIA_FOLDER, filename)
    return send_file(filepath, mimetype="image/jpeg")

@app.route("/rate/<filename>/<direction>")
def rate_photo(filename, direction):
    """
    Adjusts the rating for a photo. "direction" can be "up" or "down".
    Redirects back to the home page (which shows a new random image).
    """
    if filename in RATINGS:
        if direction == "up":
            RATINGS[filename] += 1
        elif direction == "down":
            RATINGS[filename] -= 1
    return redirect(url_for("show_photo"))

if __name__ == "__main__":
    if not os.path.isdir(MEDIA_FOLDER):
        os.makedirs(MEDIA_FOLDER, exist_ok=True)

    start_background_scraper()
    app.run(host="0.0.0.0", port=5000)