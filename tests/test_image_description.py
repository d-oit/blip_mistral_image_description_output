import unittest
import os
import json
from src.image_description import describe_image_with_mistral, generate_title_and_description, load_blip_model, load_cached_images, save_approved_images
from unittest.mock import patch, MagicMock

class TestImageDescription(unittest.TestCase):
    def test_describe_image_with_mistral(self):
        # Test with a valid image path
        image_path = 'images/IMG_20241105_174257.jpg'
        if os.path.exists(image_path):
            title, description = describe_image_with_mistral(image_path)
            self.assertIsNotNone(description)
            self.assertIsInstance(description, str)
            self.assertGreater(len(description), 0)
        else:
            print(f"Warning: Test image {image_path} not found. Skipping this test case.")

        # Test with an invalid image path
        image_path = 'invalid_image.jpg'
        title, description = describe_image_with_mistral(image_path)
        self.assertIsNone(title)
        self.assertIsNone(description)

        # Test with Mistral API error (using mocking)
        with patch('src.image_description.client.chat.complete') as mock_chat_complete:
            mock_chat_complete.side_effect = Exception("Mistral API error")
            title, description = describe_image_with_mistral(image_path)
            self.assertIsNone(title)
            self.assertIsNone(description)

    def test_generate_title_and_description(self):
        # Test with a valid image path
        image_path = 'images/IMG_20241105_174257.jpg'
        if os.path.exists(image_path):
            title, description = generate_title_and_description(image_path)
            self.assertIsNotNone(title)
            self.assertIsInstance(title, str)
            self.assertGreater(len(title), 0)
            self.assertIsNotNone(description)
            self.assertIsInstance(description, str)
            self.assertGreater(len(description), 0)
        else:
            print(f"Warning: Test image {image_path} not found. Skipping this test case.")

        # Test with an invalid image path
        image_path = 'invalid_image.jpg'
        title, description = generate_title_and_description(image_path)
        self.assertIsNone(title)
        self.assertIsNone(description)

    def test_load_blip_model(self):
        processor, model = load_blip_model()
        self.assertIsNotNone(model)
        self.assertTrue(hasattr(model, 'generate'))

    def test_load_cached_images(self):
        cached_images = load_cached_images()
        self.assertIsInstance(cached_images, list)

    def test_save_approved_images(self):
        approved_images = [{'cache_key': 'test1', 'src': 'image1', 'title': 'Title 1', 'description': 'Description 1'}, {'cache_key': 'test2', 'src': 'image2', 'title': 'Title 2', 'description': 'Description 2'}]
        save_approved_images(approved_images)
        cache_file = 'approved_images_cache.json'
        try:
            with open(cache_file, 'r') as f:
                loaded_images = json.load(f)
                self.assertEqual(loaded_images, approved_images)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.fail(f"Error loading or parsing JSON file: {e}")
        finally:
            if os.path.exists(cache_file):
                os.remove(cache_file)

if __name__ == '__main__':
    unittest.main()

