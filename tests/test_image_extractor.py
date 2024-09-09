import unittest
from unittest.mock import patch, MagicMock
from src.extractor.image_extractor import ImageExtractor
from src.scraper.scrapingbee_client import ScrapingClient
import os
import hashlib
import json


# TODO: Update example.com URLs to a real URL

class TestImageExtractor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up the ScrapingClient and ImageExtractor before running tests."""
        cls.client = ScrapingClient()
        cls.image_extractor = ImageExtractor(
            client=cls.client, min_pixel_size=10000, base_folder="test_images")

    @patch('src.extractor.image_extractor.ImageExtractor.create_folder_for_url')
    def test_create_folder_for_url(self, mock_create_folder):
        """Test if the correct folder is created based on the URL."""
        test_url = "https://example.com"
        folder_name = self.image_extractor.create_folder_for_url(test_url)
        expected_folder = os.path.join(
            "test_images", hashlib.md5(test_url.encode()).hexdigest())
        self.assertEqual(folder_name, expected_folder)
        mock_create_folder.assert_called_once()

    @patch('src.extractor.image_extractor.requests.get')
    def test_download_image_success(self, mock_get):
        """Test downloading an image successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'image content'
        mock_response.headers = {'Content-Type': 'image/jpeg'}
        mock_get.return_value = mock_response

        with self.image_extractor.download_image("https://example.com/image.jpg") as (image_data, headers):
            self.assertIsNotNone(image_data)
            self.assertEqual(headers['Content-Type'], 'image/jpeg')

    @patch('src.extractor.image_extractor.requests.get')
    def test_download_image_failure(self, mock_get):
        """Test image download failure."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with self.image_extractor.download_image("https://example.com/image.jpg") as (image_data, headers):
            self.assertIsNone(image_data)

    def test_mime_type_detection(self):
        """Test the MIME type detection logic."""
        image_data = b'image content'
        headers = {'Content-Type': 'image/jpeg'}
        mime_type = self.image_extractor.get_mime_type(
            image_data, headers, "https://example.com/image.jpg")
        self.assertEqual(mime_type, 'image/jpeg')

        # Test fallback for unsupported MIME type
        headers = {'Content-Type': 'application/octet-stream'}
        mime_type = self.image_extractor.get_mime_type(
            image_data, headers, "https://example.com/image.jpg")
        # Falls back to guessing from extension
        self.assertEqual(mime_type, 'image/jpeg')

    @patch('src.extractor.image_extractor.Image.open')
    @patch('src.extractor.image_extractor.os.path.exists')
    def test_process_image(self, mock_exists, mock_open):
        """Test processing and saving of images."""
        mock_exists.return_value = True
        # Set the image size to a valid value
        mock_open.return_value.size = (500, 500)

        folder_path = "test_images"
        image_data = b'image content'
        mime_type = 'image/jpeg'
        image_url = 'https://example.com/image.jpg'

        image_path = self.image_extractor.process_image(
            image_data, mime_type, image_url, folder_path)
        self.assertTrue(image_path.endswith(".jpg"))

    @patch('src.extractor.image_extractor.ImageExtractor.handle_svg')
    def test_process_svg_image(self, mock_handle_svg):
        """Test SVG image processing."""
        image_data = b'<svg></svg>'
        mime_type = 'image/svg+xml'
        folder_path = "test_images"
        image_url = 'https://example.com/image.svg'

        self.image_extractor.process_image(
            image_data, mime_type, image_url, folder_path)
        mock_handle_svg.assert_called_once_with(
            image_data, image_url, folder_path)

    @patch('src.extractor.image_extractor.ImageExtractor.save_json')
    @patch('src.extractor.image_extractor.ImageExtractor.save_image')
    @patch('src.extractor.image_extractor.ImageExtractor.process_image')
    def test_extract_image_info_as_json(self, mock_process_image, mock_save_image, mock_save_json):
        """Test that valid image info is correctly saved to JSON."""
        mock_process_image.return_value = "test_images/image.jpg"
        mock_save_image.return_value = "test_images/image.jpg"
        image_url = "https://example.com/image.jpg"

        # Mock the client to return a list of image URLs
        self.client.get_images = MagicMock(return_value=[image_url])

        self.image_extractor.extract_image_info_as_json("https://example.com")

        mock_save_json.assert_called_once()
        mock_process_image.assert_called_once_with(
            b'image content', 'image/jpeg', image_url, 'test_images')

    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_create_folder_for_url_creates_directory(self, mock_makedirs, mock_exists):
        """Test that create_folder_for_url creates a directory if it doesn't exist."""
        mock_exists.return_value = False
        test_url = "https://example.com"
        folder_name = self.image_extractor.create_folder_for_url(test_url)

        expected_folder = os.path.join(
            "test_images", hashlib.md5(test_url.encode()).hexdigest())
        self.assertEqual(folder_name, expected_folder)
        mock_makedirs.assert_called_once_with(expected_folder)

    def test_save_json(self):
        """Test that JSON file is saved correctly."""
        folder_path = "test_images"
        image_info = {
            "image_url": "https://example.com/image.jpg",
            "file_name": "image.jpg",
            "mime_type": "image/jpeg",
            "path": "test_images/image.jpg"
        }

        json_name = image_info["file_name"].rsplit('.', 1)[0] + '.json'
        json_path = os.path.join(folder_path, json_name)

        # Save the JSON
        self.image_extractor.save_json(image_info, folder_path)

        # Check if the JSON file exists
        self.assertTrue(os.path.exists(json_path))

        # Load the JSON and verify its contents
        with open(json_path, 'r') as json_file:
            saved_data = json.load(json_file)
            self.assertEqual(saved_data, image_info)


if __name__ == '__main__':
    unittest.main()
