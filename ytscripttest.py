from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

def scrape_movies_from_shelf(shelf_url):
    options = Options()
    # Use your dedicated logged-in profile
    options.add_argument(r"--user-data-dir=C:\Users\kayle\AppData\Local\Google\Chrome\User Data")
    options.add_argument("--profile-directory=Profile 1")  # replace with your profile name
    # options.add_argument("--headless")  # disable headless while testing

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(shelf_url)

    # Scroll to load all movies
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Grab all movie titles
    movie_titles = set()
    movie_elements = driver.find_elements("css selector", "a#video-title")
    for element in movie_elements:
        title = element.get_attribute("title")
        if title:
            movie_titles.add(title)

    driver.quit()
    return list(movie_titles)


if __name__ == "__main__":
    shelf_url = "https://www.youtube.com/feed/storefront?bp=EgCSAQMI9gOiBQIoBQ%3D%3D"
    movies = scrape_movies_from_shelf(shelf_url)
    print("Free movies found:")
    for m in movies:
        print("-", m)
