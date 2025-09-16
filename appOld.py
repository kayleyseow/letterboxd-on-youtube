import time
from flask import Flask, render_template, request, jsonify
from letterboxdpy.user import User
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

# NOTE: For deployment, this function should be run on a schedule
# (e.g., using a cron job) and the results stored in a database.
# For local testing, calling it directly is fine.
def scrape_youtube_free_movies():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://www.youtube.com/feed/storefront")

    # Scroll down to load more movies dynamically
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    movie_titles = set()
    try:
        # Find the specific shelf with "Free Primetime movies"
        free_movies_shelf = driver.find_element(By.XPATH, "//span[@id='title' and contains(text(), 'Free Primetime movies')]")
        
        # Navigate to the parent element to find the movie titles within that shelf
        shelf_container = free_movies_shelf.find_element(By.XPATH, "../../..")
        movie_elements = shelf_container.find_elements(By.CSS_SELECTOR, "span#video-title")
        
        for element in movie_elements:
            title = element.get_attribute("title")
            if title:
                movie_titles.add(title)
    except Exception as e:
        print(f"Error scraping YouTube: {e}")
    finally:
        driver.quit()
    return list(movie_titles)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/compare", methods=["POST"])
def compare_watchlists():
    data = request.get_json()
    print("data", data)
    username = data.get("username")
    print("username", username)
    
    if not username:
        return jsonify({"error": "Please provide a Letterboxd username."}), 400

    try:
        print("inside the try block")
        user = User(username)

        # Get the Letterboxd watchlist titles
        print("Number of movies on watchlist:", user.watchlist_length)

        user_watchlist = user.get_watchlist_movies()
        # print("watchlist created")
        # print("first five titles in watchlist:", list(user_watchlist.values())[:5])
        # print(len(user_watchlist))
        # watchlist_titles = {film['name'] for film in user_watchlist}
        watchlist_titles = {film['name'] for film in user_watchlist.values()}
        print("First ten titles in watchlist:", list(watchlist_titles)[:10])

        # Get the YouTube movie list
        youtube_free_titles = set(scrape_youtube_free_movies())
        print("done scraping youtube")

        # Find matching titles
        matches = list(watchlist_titles.intersection(youtube_free_titles))

        return jsonify({"username": username, "matches": matches})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)