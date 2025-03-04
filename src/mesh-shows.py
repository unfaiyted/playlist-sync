from src.clients.emby_client import Emby, EmbyLibraryItemType

# Array of TV shows
shows = [
    {"id": "show1-id", "name": "First Show"},
    {"id": "show2-id", "name": "Second Show"},
    {"id": "show3-id", "name": "Third Show"}
]

def mesh_shows(emby_client):
    all_episodes = []
    for show in shows:
        seasons = emby_client.get_seasons(show["id"])
        for season in seasons:
            episodes = emby_client.get_episodes(show["id"], season["Id"])
            all_episodes.append(episodes)

    max_episodes = max(len(episodes) for episodes in all_episodes)

    playlist = emby_client.create_playlist("Meshed Shows", EmbyLibraryItemType.VIDEO.value)
    playlist_id = playlist["Id"]

    for i in range(max_episodes):
        for j, episodes in enumerate(all_episodes):
            if i < len(episodes):
                episode = episodes[i]
                emby_client.add_item_to_playlist(playlist_id, episode["Id"])
                print(f"Adding {shows[j]['name']} S{episode['ParentIndexNumber']:02}E{episode['IndexNumber']:02} to the playlist")

                # Balance the shows based on the number of episodes
                remaining_episodes = len(episodes) - (i + 1)
                other_remaining_episodes = [len(eps) - (i + 1) for eps in all_episodes[:j] + all_episodes[j+1:]]
                if remaining_episodes < min(other_remaining_episodes):
                    # Add additional episodes of the current show
                    extra_episodes = min(other_remaining_episodes) - remaining_episodes
                    for k in range(extra_episodes):
                        if i + k + 1 < len(episodes):
                            extra_episode = episodes[i + k + 1]
                            emby_client.add_item_to_playlist(playlist_id, extra_episode["Id"])
                            print(f"Adding {shows[j]['name']} S{extra_episode['ParentIndexNumber']:02}E{extra_episode['IndexNumber']:02} to the playlist")

    print("Playlist created successfully!")

def main():
    emby_client = Emby(EMBY_URL, EMBY_USERNAME, EMBY_API_KEY)
    mesh_shows(emby_client)

if __name__ == "__main__":
    main()