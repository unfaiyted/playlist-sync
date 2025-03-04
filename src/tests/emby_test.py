import unittest
from unittest.mock import patch, MagicMock
from src.clients.emby_client import Emby
from src.config import Config

class TestEmby(unittest.TestCase):

    def setUp(self):
        self.server_url = Config.EMBY_URL
        self.username = Config.EMBY_USERNAME
        self.api_key = Config.EMBY_API_KEY
        self.emby = Emby(self.server_url, self.username, self.api_key)
        self.emby.user = {"Id": Config.EMBY_USER_ID}
        self.emby.user_id = Config.EMBY_USER_ID

    @patch('src.clients.emby.Emby._get_request')
    def test_get_collections(self, mock_get_request):
        mock_response = {"Items": [{"Name": "Collection1"}, {"Name": "Collection2"}]}
        mock_get_request.return_value = mock_response
        collections = self.emby.get_collections()
        self.assertEqual(len(collections), 2)
        self.assertEqual(collections[0]["Name"], "Collection1")
        self.assertEqual(collections[1]["Name"], "Collection2")

    @patch('src.clients.emby.Emby._get_request')
    def test_get_collection_by_name(self, mock_get_request):
        mock_response = {"Items": [{"Name": "Collection1", "Type": "boxset"}, {"Name": "Collection2", "Type": "boxset"}]}
        mock_get_request.return_value = mock_response
        collection = self.emby.get_collection_by_name("Collection1")
        self.assertIsNotNone(collection)
        self.assertEqual(collection["Name"], "Collection1")

    @patch('src.clients.emby.Emby._post_request')
    def test_create_collection(self, mock_post_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"Name": "NewCollection", "Id": "newcollectionid"}
        mock_post_request.return_value = mock_response

        with patch('src.clients.emby.Emby.get_items_by_type') as mock_get_items_by_type:
            mock_get_items_by_type.return_value = [{"Id": "itemid"}]
            with patch('src.clients.emby.Emby.delete_item_from_collection') as mock_delete_item_from_collection:
                collection = self.emby.create_collection("NewCollection", "boxset")
                self.assertEqual(collection["Name"], "NewCollection")
                self.assertEqual(collection["Id"], "newcollectionid")
                mock_delete_item_from_collection.assert_called_once_with("newcollectionid", "itemid")

    @patch('src.clients.emby.Emby._post_request')
    def test_delete_collection(self, mock_post_request):
        self.emby.delete_collection("collectionid")
        mock_post_request.assert_called_once_with(f"{self.server_url}/emby/Items/collectionid/Delete?api_key={self.api_key}&X-Emby-Token={self.api_key}")

    # Add more test methods for other functions in the Emby class

if __name__ == '__main__':
    unittest.main()