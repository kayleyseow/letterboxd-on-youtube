import os
import json
import re
import unicodedata
from flask import Flask, render_template, request, jsonify
from letterboxdpy.user import User
from flask_cors import CORS

app = Flask(__name__)

CORS(app, resources={
    r"/compare": {"origins": "https://www.letterboxd-on-youtube.kayleyseow.com"},
    r"/ping": {"origins": "https://www.letterboxd-on-youtube.kayleyseow.com"}
})
# CORS(app)

# Lowercase, remove punctuation, normalize unicode, replace & with 'and'
def normalize_title(title):
    title = unicodedata.normalize('NFKD', title)
    title = title.lower().replace('&', 'and')
    title = re.sub(r'[^a-z0-9 ]', '', title) 
    title = re.sub(r'\s+', ' ', title).strip()
    return title

# Load YouTube free-with-ads JSON once at app start
with open("youtube_free_with_ads.json", "r", encoding="utf-8") as f:
    youtube_movies = json.load(f)
for movie in youtube_movies:
    movie['norm_title'] = normalize_title(movie['title'])

# Function to build normalized list from Letterboxd movies
def build_normalized_list(lb_movies):
    print("inside normalized list")
    out = []
    for movie in lb_movies:
        name = movie.get('name', '')
        url = movie.get('url', '')

        # Extract year if "(YYYY)" is present in the title
        match = re.search(r'\((\d{4})\)', name)
        year = int(match.group(1)) if match else None

        # Clean the title (remove year suffix)
        title_clean = re.sub(r'\s*\(\d{4}\)', '', name).strip()
        norm_title = normalize_title(title_clean)

        out.append({
            'title': title_clean,
            'norm_title': norm_title,
            'year': year,
            'url': url
        })

    print(f"Total movies processed: {len(out)}")
    out_sorted = sorted(out, key=lambda m: m['year'] or 0, reverse=True)
    print(out_sorted[:10])  # keep your debug print
    return out_sorted

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ping", methods=["GET"])
def ping():
    return {"ping": "pong"}

@app.route("/compare", methods=["POST"])
def compare_watchlists():
    data = request.get_json()
    username = data.get("username")
    
    if not username:
        return jsonify({"error": "❌ Please enter a Letterboxd username before comparing."}), 400

    try:
        # Fetch Letterboxd watchlist
        user_instance = User(username)
        user_watchlist = user_instance.get_watchlist()

        print(len(user_watchlist.get("data", [])), "watchlist length")

        if not user_watchlist or "data" not in user_watchlist:
            return jsonify({
                "error": "⚠️ Username not found. Please enter a valid Letterboxd username."
            }), 404

        # Build normalized watchlist
        watchlist = build_normalized_list(user_watchlist["data"].values())

        # Fetch already watched films
        user_films = user_instance.get_films()
        if not user_films or "movies" not in user_films:
            watched = []
        else:
            watched = build_normalized_list(user_films.get("movies", {}).values())

        # Matching logic with year tolerance and ambiguous/near-miss handling
        matches = []
        near_misses = []
        ambiguous_matches = []

        watched_matches = []
        watched_ambiguous = []
        watched_near_misses = []

        for yt in youtube_movies:
            yt_norm_title = yt['norm_title']
            yt_year = yt.get('year')
            lb_matches = [lb for lb in watchlist if lb['norm_title'] == yt_norm_title and lb['year'] is not None and yt_year is not None and abs(lb['year'] - yt_year) <= 1]
            if len(lb_matches) == 1:
                matches.append({'yt': yt, 'lb': lb_matches[0]})
            elif len(lb_matches) > 1:
                for lb in lb_matches:
                    ambiguous_matches.append({'yt': yt, 'lb': lb, 'note': f"multiple matches"})
            else:
                for lb in watchlist:
                    if yt_norm_title == lb['norm_title'] and (not yt_year or not lb['year']):
                        near_misses.append({'yt': yt, 'lb': lb, 'reason': 'missing year'})
            
            watched_lb_matches = [
                lb for lb in watched
                if lb['norm_title'] == yt_norm_title
                and lb['year'] is not None
                and yt_year is not None
                and abs(lb['year'] - yt_year) <= 1
            ]
            if len(watched_lb_matches) == 1:
                watched_matches.append({'yt': yt, 'lb': watched_lb_matches[0]})
            elif len(watched_lb_matches) > 1:
                for lb in watched_lb_matches:
                    watched_ambiguous.append({'yt': yt, 'lb': lb, 'note': 'multiple matches'})
            else:
                for lb in watched:
                    if lb['norm_title'] == yt_norm_title and (not yt_year or not lb['year']):
                        watched_near_misses.append({'yt': yt, 'lb': lb, 'reason': 'missing year'})


        # DEBUGGING
        # print("\n--- MATCHES ---")
        # for m in matches:
        #     print(f"Match: {m['yt']['title']} ({m['yt'].get('year')}) <-> {m['lb']['title']} ({m['lb']['year']})")
        # print("\n--- AMBIGUOUS MATCHES ---")
        # for am in ambiguous_matches:
        #     print(f"Ambiguous: {am['yt']['title']} ({am['yt'].get('year')}) <-> {am['lb']['title']} ({am['lb']['year']}) [{am['note']}]")
        # print("\n--- NEAR MISSES ---")
        # for nm in near_misses:
        #     print(f"Near miss: {nm['yt']['title']} ({nm['yt'].get('year')}) <-> {nm['lb']['title']} ({nm['lb']['year']}) [{nm['reason']}]")

        # print("\n--- WATCHEDMATCHES ---")
        # for m in watched_matches:
        #     print(f"Match: {m['yt']['title']} ({m['yt'].get('year')}) <-> {m['lb']['title']} ({m['lb']['year']})")
        # print("\n--- WATCHED AMBIGUOUS MATCHES ---")
        # for am in watched_ambiguous:
        #     print(f"Ambiguous: {am['yt']['title']} ({am['yt'].get('year')}) <-> {am['lb']['title']} ({am['lb']['year']}) [{am['note']}]")
        # print("\n--- WATCHED NEAR MISSES ---")
        # for nm in watched_near_misses:
        #     print(f"Near miss: {nm['yt']['title']} ({nm['yt'].get('year')}) <-> {nm['lb']['title']} ({nm['lb']['year']}) [{nm['reason']}]")

        matches_out = [
            {
                "yt_title": m['yt']['title'],
                "yt_year": m['yt'].get('year'),
                "yt_href": m['yt']['href'],
                "lb_title": m['lb']['title'],
                "lb_year": m['lb']['year'],
                "lb_url": m['lb'].get('url', None)
            }
            for m in matches
        ]
        ambiguous_out = [
            {
                "yt_title": am['yt']['title'],
                "yt_year": am['yt'].get('year'),
                "yt_href": am['yt']['href'],
                "lb_title": am['lb']['title'],
                "lb_year": am['lb']['year'],
                "lb_url": am['lb'].get('url', None),
                "note": am['note']
            }
            for am in ambiguous_matches
        ]
        near_miss_out = [
            {
                "yt_title": nm['yt']['title'],
                "yt_year": nm['yt'].get('year'),
                "yt_href": nm['yt']['href'],
                "lb_title": nm['lb']['title'],
                "lb_year": nm['lb']['year'],
                "lb_url": nm['lb'].get('url', None),
                "reason": nm['reason']
            }
            for nm in near_misses
        ]
        watched_matches_out = [
            {
                "yt_title": m['yt']['title'],
                "yt_year": m['yt'].get('year'),
                "yt_href": m['yt']['href'],
                "lb_title": m['lb']['title'],
                "lb_year": m['lb']['year'],
                "lb_url": m['lb']['url']
            }
            for m in watched_matches
        ]
        watched_ambiguous_out = [
            {
                "yt_title": am['yt']['title'],
                "yt_year": am['yt'].get('year'),
                "yt_href": am['yt']['href'],
                "lb_title": am['lb']['title'],
                "lb_year": am['lb']['year'],
                "lb_url": am['lb']['url'],
                "note": am['note']
            }
            for am in watched_ambiguous
        ]
        watched_near_miss_out = [
            {
                "yt_title": nm['yt']['title'],
                "yt_year": nm['yt'].get('year'),
                "yt_href": nm['yt']['href'],
                "lb_title": nm['lb']['title'],
                "lb_year": nm['lb']['year'],
                "lb_url": nm['lb']['url'],
                "reason": nm['reason']
            }
            for nm in watched_near_misses
        ]

        return jsonify({
            "username": username,
            "watchlist": {
                "matches": matches_out,
                "ambiguous_matches": ambiguous_out,
                "near_misses": near_miss_out
            },
            "watched": {
                "matches": watched_matches_out,
                "ambiguous_matches": watched_ambiguous_out,
                "near_misses": watched_near_miss_out
            }
        })

    except Exception as e:
        if "404" in str(e) or "not found" in str(e).lower():
            return jsonify({"error": "⚠️ Username not found. Please enter a valid Letterboxd username."}), 404
        else:
            return jsonify({"error": f"⚠️ Server error: {str(e)}"}), 500

if __name__ == "__main__":
    # app.run(debug=True) # uncomment for local testing
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
