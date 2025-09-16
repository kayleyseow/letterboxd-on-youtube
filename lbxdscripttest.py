from letterboxdpy.user import User
user = User("miseenkale")
# print(user)
# print(user.recent['watchlist'])
print("Number of movies on watchlist:", user.watchlist_length)

movies = user.get_watchlist_movies()
# print("Watchlist movies:", movies)

# Get the watchlist with optional filters (or all if no filters)
full_watchlist = user.get_watchlist() # extra filters we don't need
# print("Full watchlist:", full_watchlist)
# print("first ten watchlist items:", list(full_watchlist.items())[:10])

full_watchlist_ids = set(full_watchlist.keys())
movies_ids = set(movies.keys())

# Find IDs in full_watchlist but not in movies
diff_ids = full_watchlist_ids - movies_ids

# print(f"Full watchlist length: {len(full_watchlist)}")
# print(f"Movies length: {len(movies)}")
print(f"IDs in full_watchlist but not in movies: {diff_ids}")


# figure out why the text isn't matching
# need to write a webcrawler since the 