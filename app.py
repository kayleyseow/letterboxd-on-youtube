import json
import re
import unicodedata
from flask import Flask, render_template, request, jsonify
from letterboxdpy.user import User

app = Flask(__name__)

def normalize_title(title):
    # Lowercase, remove punctuation, normalize unicode, replace & with 'and'
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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/compare", methods=["POST"])
def compare_watchlists():
    data = request.get_json()
    username = data.get("username")
    
    if not username:
        return jsonify({"error": "❌ Please enter a Letterboxd username before comparing."}), 400

    try:
        user = User(username)
        user_watchlist = user.get_watchlist()
        # print(username, "'s watchlist is", len(user_watchlist['data']), "movies long.")

        if not user_watchlist or "data" not in user_watchlist:
            return jsonify({
                "error": "⚠️ Username not found. Please enter a valid Letterboxd username."
            }), 404

        if len(user_watchlist["data"]) == 0:
            return jsonify({
                "empty_watchlist": True,
                "message": "📭 Your watchlist is empty. Please add movies to your watchlist on Letterboxd."
            }), 200

        # Build normalized watchlist
        watchlist = []
        for movie in user_watchlist['data'].values():
            name = movie['name']
            url = movie['url']
            match = re.search(r'\((\d{4})\)', name)
            year = int(match.group(1)) if match else None
            title_clean = re.sub(r'\s*\(\d{4}\)', '', name).strip()
            norm_title = normalize_title(title_clean)
            watchlist.append({'title': title_clean, 'norm_title': norm_title, 'year': year, 'url': url})

        print(f"Total movies processed: {len(watchlist)}")
        watchlist_sorted = sorted(watchlist, key=lambda m: m['year'] or 0, reverse=True)
        print(watchlist_sorted[:10])

        # Matching logic with year tolerance and ambiguous/near-miss handling
        matches = []
        near_misses = []
        ambiguous_matches = []
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


        # Debug print statements for the three lists
        print("\n--- MATCHES ---")
        for m in matches:
            print(f"Match: {m['yt']['title']} ({m['yt'].get('year')}) <-> {m['lb']['title']} ({m['lb']['year']})")
        print("\n--- AMBIGUOUS MATCHES ---")
        for am in ambiguous_matches:
            print(f"Ambiguous: {am['yt']['title']} ({am['yt'].get('year')}) <-> {am['lb']['title']} ({am['lb']['year']}) [{am['note']}]")
        print("\n--- NEAR MISSES ---")
        for nm in near_misses:
            print(f"Near miss: {nm['yt']['title']} ({nm['yt'].get('year')}) <-> {nm['lb']['title']} ({nm['lb']['year']}) [{nm['reason']}]")

        matches_out = [
            {
                "yt_title": m['yt']['title'],
                "yt_year": m['yt'].get('year'),
                "yt_href": m['yt']['href'],
                "lb_title": m['lb']['title'],
                "lb_year": m['lb']['year'],
                "lb_url": m['lb']['url']
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
                "lb_url": am['lb']['url'],
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
                "lb_url": nm['lb']['url'],
                "reason": nm['reason']
            }
            for nm in near_misses
        ]

        return jsonify({
            "username": username,
            "matches": matches_out,
            "ambiguous_matches": ambiguous_out,
            "near_misses": near_miss_out
        })

    except Exception as e:
        if "404" in str(e) or "not found" in str(e).lower():
            return jsonify({"error": "⚠️ Username not found. Please enter a valid Letterboxd username."}), 404
        else:
            return jsonify({"error": f"⚠️ Server error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
