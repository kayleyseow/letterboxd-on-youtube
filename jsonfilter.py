import json

# Load the original JSON
with open('youtube_free_with_ads.json', 'r', encoding='utf-8') as f:
    movies = json.load(f)

# Sort by year descending, missing years go last
movies_sorted = sorted(movies, key=lambda m: m.get('year') or 0, reverse=True)

# Overwrite the JSON file with the sorted data
with open('youtube_free_with_ads.json', 'w', encoding='utf-8') as f:
    json.dump(movies_sorted, f, ensure_ascii=False, indent=2)

print("JSON file updated and sorted by year descending.")
