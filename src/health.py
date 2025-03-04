# health.py
from config import Config
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests

def test_spotify_connection():
    try:
        spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=Config.SPOTIFY_CLIENT_ID,
            client_secret=Config.SPOTIFY_CLIENT_SECRET,
            redirect_uri=Config.SPOTIFY_REDIRECT_URI,
            scope=Config.SPOTIFY_SCOPE
        ))
        user = spotify.current_user()
        print("Spotify connection successful.")
        print(f"Logged in as: {user['display_name']} ({user['id']})")
    except Exception as e:
        print(f"Spotify connection failed: {str(e)}")

def test_emby_connection():
    try:
        headers = {
            "X-Emby-Token": Config.EMBY_API_KEY,
            "X-Emby-Client": Config.EMBY_CLIENT,
            "X-Emby-Device-Name": Config.EMBY_DEVICE,
            "X-Emby-Device-Id": Config.EMBY_DEVICE_ID,
            "X-Emby-Client-Version": Config.EMBY_VERSION
        }
        response = requests.get(f"{Config.EMBY_URL}/emby/System/Info", headers=headers)

        if response.status_code == 200:
            print("Emby connection successful.")
            data = response.json()
            print(f"Emby server version: {data['Version']}")
        else:
            print(f"Emby connection failed. Status code: {response.status_code}")
    except Exception as e:
        print(f"Emby connection failed: {str(e)}")


def get_emby_profiles():
    try:
        headers = {
            "X-Emby-Token": Config.EMBY_API_KEY,
            "X-Emby-Client": Config.EMBY_CLIENT,
            "X-Emby-Device-Name": Config.EMBY_DEVICE,
            "X-Emby-Device-Id": Config.EMBY_DEVICE_ID,
            "X-Emby-Client-Version": Config.EMBY_VERSION
        }
        response = requests.get(f"{Config.EMBY_URL}/emby/Users", headers=headers)

        if response.status_code == 200:
            profiles_data = response.json()
            print("Valid profiles:")
            for profile in profiles_data:
                print(f"- ID: {profile['Id']}, Name: {profile['Name']}")
        else:
            print(f"Failed to retrieve profiles. Status code: {response.status_code}")
    except Exception as e:
        print(f"Failed to retrieve profiles: {str(e)}")



if __name__ == "__main__":
    print("Testing Spotify connection...")
    test_spotify_connection()
    print()

    print("Testing Emby connection...")
    test_emby_connection()

    print("Retrieving Emby profiles...")
    get_emby_profiles()