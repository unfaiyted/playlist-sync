from src.clients.emby_client import EmbyClient
from src.config import Config
from src.utils.string_utils import StringUtils

emby = EmbyClient(Config.EMBY_URL, Config.EMBY_USERNAME, Config.EMBY_PASSWORD)

tv_shows = ["The Office (US)", "Bob's Burgers", "Parks and Recreation"]

starting_episodes = {
    "The Office (US)": "S01E01",  # Start from Season 2, Episode 3 of The Office ()
    "Bob's Burgers": "S01E01",
    "Parks and Recreations": "S01E01"
}

# Toggle variable to control marking episodes as unwatched
mark_as_unwatched = True

# Create a new playlist
playlist_name = "Bob's Office Park - Mix"
playlist_type = "shows"
playlist = emby.create_playlist(playlist_name, playlist_type)

# Get all the episodes for all of the TV shows in the array
all_episodes = {}
for show_name in tv_shows:
    show = emby.search(show_name, "Series")[0]  # Assuming the first search result is the desired show
    seasons = emby.get_seasons(show["Id"])

    all_episodes[show_name] = []
    for season in seasons:
        episodes = emby.get_episodes(show["Id"], season["Id"])
        all_episodes[show_name].extend(episodes)

# Sort the episodes of each show by season and episode number
for show_name in all_episodes:
    all_episodes[show_name].sort(key=lambda x: (x["ParentIndexNumber"], x["IndexNumber"]))

# Find the maximum number of episodes among all shows
max_episodes = max(len(episodes) for episodes in all_episodes.values())

# Initialize episode counters for each show
episode_counters = {}
for show_name in tv_shows:
    start_episode_string = starting_episodes.get(show_name, "S01E01")
    start_season, start_episode = StringUtils.get_episode_info(start_episode_string)

    episode_counter = 0
    for episode in all_episodes[show_name]:
        if episode["ParentIndexNumber"] > start_season or (
                episode["ParentIndexNumber"] == start_season and episode["IndexNumber"] >= start_episode
        ):
            break
        episode_counter += 1

    episode_counters[show_name] = episode_counter

# Initialize a set to keep track of added episode IDs
added_episode_ids = set()

# Loop over the episodes and add them sequentially
for i in range(max_episodes):
    for show_name in tv_shows:
        if episode_counters[show_name] < len(all_episodes[show_name]):
            episode = all_episodes[show_name][episode_counters[show_name]]
            episode_id = episode["Id"]

            if episode_id not in added_episode_ids:
                emby.add_item_to_playlist(playlist["Id"], episode_id)
                print(f"Added episode: {show_name} - S{episode['ParentIndexNumber']:02}E{episode['IndexNumber']:02}")

                if mark_as_unwatched:
                    emby.mark_as_unwatched(episode_id)
                    print(f"Marked as unwatched: {show_name} - S{episode['ParentIndexNumber']:02}E{episode['IndexNumber']:02}")

                added_episode_ids.add(episode_id)
            else:
                print(
                    f"Skipped duplicate episode: {show_name} - S{episode['ParentIndexNumber']:02}E{episode['IndexNumber']:02}")

            episode_counters[show_name] += 1
        else:
            print(f"No more episodes for {show_name}")

print("Playlist creation completed.")
