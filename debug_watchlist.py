from letterboxdpy.user import User
import re
import unicodedata
import json

user = User("miseenkale")
# print("Testing Number of movies on watchlist:", user.watchlist_length)


# Now get the movies
# movies_dict = user.get_watchlist_movies()
# print(f"Length of movies_dict: {len(movies_dict)}")
# print(f"Number of movies fetched: {len(movies_dict.get('data', {}))}")

# Fetch the full watchlist first
full_watchlist = user.get_watchlist()  # optionally: filters={'sort': 'dateAdded'}
# print(f"Length of full_watchlist: {len(full_watchlist)}")
# print(full_watchlist)
# print(f"Full watchlist keys: {full_watchlist.keys()}")

def normalize_title(title):
    # Lowercase, remove punctuation, normalize unicode, replace & with 'and'
    title = unicodedata.normalize('NFKD', title)
    title = title.lower().replace('&', 'and')
    title = re.sub(r'[^a-z0-9 ]', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title

# Build normalized watchlist
watchlist = []
for movie in full_watchlist['data'].values():
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

with open("youtube_free_with_ads.json", "r", encoding="utf-8") as f:
    youtube_movies = json.load(f)

for movie in youtube_movies:
    movie['norm_title'] = normalize_title(movie['title'])


# Matching logic with slug disambiguation
matches = []
near_misses = []
ambiguous_matches = []
for yt in youtube_movies:
    yt_norm_title = normalize_title(yt['title'])
    yt_year = yt.get('year')
    # Find all Letterboxd movies with matching normalized title and year (with ±1 year tolerance)
    lb_matches = [lb for lb in watchlist if lb['norm_title'] == yt_norm_title and lb['year'] is not None and yt_year is not None and abs(lb['year'] - yt_year) <= 1]
    if len(lb_matches) == 1:
        matches.append({'yt': yt, 'lb': lb_matches[0]})
    elif len(lb_matches) > 1:
        # Multiple matches, show all and include slug for disambiguation
        for lb in lb_matches:
            ambiguous_matches.append({'yt': yt, 'lb': lb, 'note': f"multiple matches, slug: {lb.get('slug', 'N/A')}"})
    else:
        # Near miss: missing year or no match
        for lb in watchlist:
            if yt_norm_title == lb['norm_title'] and (not yt_year or not lb['year']):
                near_misses.append({'yt': yt, 'lb': lb, 'reason': 'missing year'})

print("Matches found:")
for m in matches:
    print(f"Match: {m['yt']['title']} ({m['yt']['year']}) <-> {m['lb']['title']} ({m['lb']['year']})")

print("\nAmbiguous matches (multiple Letterboxd movies):")
for am in ambiguous_matches:
    print(f"Ambiguous: {am['yt']['title']} ({am['yt']['year']}) <-> {am['lb']['title']} ({am['lb']['year']}) [slug: {am['lb'].get('slug', 'N/A')}]")

print("\nNear misses:")
for nm in near_misses:
    print(f"Near miss: {nm['yt']['title']} ({nm['yt']['year']}) <-> {nm['lb']['title']} ({nm['lb']['year']}) [{nm['reason']}]")
