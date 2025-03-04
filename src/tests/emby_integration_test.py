import unittest
from unittest.mock import patch
from io import BytesIO
import requests

from src.clients.emby_client import EmbyClient
from src.config import Config


class TestEmbyIntegration(unittest.TestCase):

    def setUp(self):
        self.server_url = Config.EMBY_URL
        self.username = Config.EMBY_USERNAME
        self.api_key = Config.EMBY_API_KEY
        self.password = Config.EMBY_PASSWORD
        self.emby = EmbyClient(self.server_url, self.username, self.password)

        self.test_playlist_name = "Test Playlist"
        self.test_playlist = self.emby.create_playlist(self.test_playlist_name, "Audio")
        self.test_playlist_id = self.test_playlist["Id"]

    def tearDown(self):
        # Clean up by deleting the test playlist
        self.emby.delete_playlist(self.test_playlist_id)
        # Delete all playlists that have the name Test Playlist
        playlists = self.emby.get_playlists()
        for playlist in playlists:
            if playlist["Name"] == "Test Playlist":
                self.emby.delete_playlist(playlist["Id"])

    def test_get_collections(self):
        collections = self.emby.get_collections()
        self.assertIsInstance(collections, list)
        # Assert that the collections have the expected properties
        for collection in collections:
            self.assertIn("Name", collection)
            self.assertIn("Id", collection)

    def test_add_and_remove_items_from_collection(self):
        # Get the ID of the first item in the movies library
        movies_library = next((library for library in self.emby.get_libraries() if library["Name"] == "Movies"), None)
        if movies_library is None:
            self.skipTest("Movies library not found")

        movies, _ = self.emby.get_items_from_library(movies_library["Name"])
        if not movies:
            self.skipTest("No movies found in the library")

        item_id = movies[0]["Id"]

        # Create a new collection
        collection_name = "Test Collection"
        collection_type = "movies"
        collection = self.emby.create_collection(collection_name, collection_type)
        self.assertEqual(collection["Name"], collection_name)
        self.assertIsNotNone(collection["Id"])

        # Add the item to the collection
        self.emby.add_item_to_collection(collection["Id"], item_id)

        # Verify that the item is added to the collection
        collection_items, _ = self.emby.get_collection_items(collection["Id"])
        self.assertIn(item_id, [item["Id"] for item in collection_items])

        # Delete the item from the collection
        self.emby.delete_item_from_collection(collection["Id"], item_id)

        # Verify that the item is deleted from the collection
        collection_items, _ = self.emby.get_collection_items(collection["Id"])
        self.assertNotIn(item_id, [item["Id"] for item in collection_items])

    def test_create_collection(self):
        # Create a new collection
        collection_name = "Test Collection"
        collection_type = "Movie"
        collection = self.emby.create_collection(collection_name, collection_type)
        self.assertEqual(collection["Name"], collection_name)
        self.assertIsNotNone(collection["Id"])

        # Delete the collection
        self.emby.delete_collection(collection["Id"])

        # Verify that the collection is deleted
        collections = self.emby.get_collections()
        self.assertNotIn(collection["Id"], [c["Id"] for c in collections])

    # Add more integration tests for other methods

    def test_create_and_delete_playlist(self):
        # Get the ID of the first item in the movies library
        movies_library = next((library for library in self.emby.get_libraries() if library["Name"] == "Movies"), None)
        if movies_library is None:
            self.skipTest("Movies library not found")

        movies, _ = self.emby.get_items_from_library(movies_library["Name"])
        if not movies:
            self.skipTest("No movies found in the library")

        item_id = movies[0]["Id"]

        # Create a new playlist
        playlist_name = "Test Playlist"
        playlist_type = "movies"
        playlist = self.emby.create_playlist(playlist_name, playlist_type)
        self.assertEqual(playlist["Name"], playlist_name)
        self.assertIsNotNone(playlist["Id"])

        # Add the item to the playlist
        self.emby.add_item_to_playlist(playlist["Id"], item_id)

        # Verify that the item is added to the playlist
        playlist_items, _ = self.emby.get_list_items(playlist["Id"])
        self.assertIn(item_id, [item["Id"] for item in playlist_items])

        # Delete the item from the playlist
        self.emby.delete_item_from_playlist(playlist["Id"], item_id)

        # Verify that the item is deleted from the playlist
        playlist_items, _ = self.emby.get_list_items(playlist["Id"])
        self.assertNotIn([item_id], [item["Id"] for item in playlist_items])

        # Delete the playlist
        self.emby.delete_playlist(playlist["Id"])

        # Verify that the playlist is deleted
        playlists = self.emby.get_playlists()
        self.assertNotIn(playlist["Id"], [p["Id"] for p in playlists])

    def test_search_for_track_existing(self):
        # Test searching for a track that exists in the Emby library
        track_name = "Away from the Sun"
        artist_name = "3 Doors Down"
        search_results = self.emby.search_for_track(track_name, artist_name)
        print(search_results)
        self.assertIsNotNone(search_results)
        self.assertGreater(len(search_results), 0)
        print(len(search_results))
        has_match = False
        for track in search_results:
            if track["Name"].lower() == track_name.lower():
                for artist in track["Artists"]:
                    if artist.lower() == artist_name.lower():
                        has_match = True
        self.assertTrue(has_match)

    def test_search_for_track_nonexistent(self):
        # Test searching for a track that doesn't exist in the Emby library
        track_name = "Nonexistent Track"
        artist_name = "Nonexistent Artist"
        search_results = self.emby.search_for_track(track_name, artist_name)
        self.assertIsNotNone(search_results)
        self.assertEqual(len(search_results), 0)

    # def test_search_for_track_partial_match(self):
    #     # Test searching for a track with partial track name and artist name
    #     track_name = "away from"
    #     artist_name = "3 doors"
    #     search_results = self.emby.search_for_track(track_name, artist_name)
    #     self.assertIsNotNone(search_results)
    #     self.assertGreater(len(search_results), 0)
    #     for track in search_results:
    #         self.assertIn(track_name.lower(), track["Name"].lower())
    #         self.assertIn(artist_name.lower(), [artist["Name"].lower() for artist in track["Artists"]])

    def test_search_for_track_empty_query(self):
        # Test searching for a track with empty track name and artist name
        track_name = ""
        artist_name = ""
        search_results = self.emby.search_for_track(track_name, artist_name)
        self.assertIsNotNone(search_results)
        # Depending on your Emby server, empty search query may return all tracks or no tracks
        # Adjust the assertion based on your expected behavior
        # self.assertGreater(len(search_results), 0)
        # self.assertEqual(len(search_results), 0)

    def test_search_for_track_special_characters(self):
        # Test searching for a track with special characters in track name and artist name
        track_name = "Track with !@#$%^&*()"
        artist_name = "Artist with !@#$%^&*()"
        search_results = self.emby.search_for_track(track_name, artist_name)
        self.assertIsNotNone(search_results)
        # Depending on your Emby server, special characters may affect the search results
        # Adjust the assertions based on your expected behavior
        # self.assertGreater(len(search_results), 0)
        # self.assertEqual(len(search_results), 0)

    def test_upload_playlist_cover_image(self):
        image_data = BytesIO(b'test image data')
        res = self.emby.upload_image_data(self.test_playlist_id, image_data.getvalue(), 'Primary')
        print(res, res.status_code)
        # Verify that the playlist cover image was uploaded successfully
        playlist_details = self.emby.get_list(self.test_playlist_id)
        print(playlist_details)
        self.assertTrue(playlist_details["ImageTags"].get("Primary"))

if __name__ == '__main__':
    unittest.main()
