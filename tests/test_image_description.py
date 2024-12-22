import unittest
import os
import json
from src.image_description import ImageDescriptionApp, AppConfig
from unittest.mock import patch, MagicMock
import streamlit as st
from streamlit.testing import TestRunner

class TestImageDescription(unittest.TestCase):
    def setUp(self):
        self.config = AppConfig(
            mistral_api_key="test_mistral_api_key",
            deepl_auth_key="test_deepl_auth_key"
        )
        self.app = ImageDescriptionApp(self.config)

    def test_describe_image(self):
        # Test with a valid image path
        image_path = 'images/IMG_20241105_174257.jpg'
        if os.path.exists(image_path):
            description = self.app.describe_image(image_path, 'EN')
            self.assertIsNotNone(description)
            self.assertIsInstance(description, dict)
            self.assertIn('blip_caption', description)
            self.assertIn('mistral_description', description)
        else:
            print(f"Warning: Test image {image_path} not found. Skipping this test case.")

        # Test with an invalid image path
        image_path = 'invalid_image.jpg'
        description = self.app.describe_image(image_path, 'EN')
        self.assertIsInstance(description, dict)
        self.assertEqual(description['filename'], 'invalid_image.jpg')

    def test_translate_text(self):
        # Test with valid input
        text = 'Hello, world!'
        translated_text = self.app.translate_text(text, 'DE')
        self.assertIsNotNone(translated_text)
        self.assertIsInstance(translated_text, str)

    def test_load_models(self):
        processor, model, mistral_client = self.app.load_models()
        self.assertIsNotNone(processor)
        self.assertIsNotNone(model)
        self.assertIsNotNone(mistral_client)

    def test_load_approved_images(self):
        self.app.load_approved_images()
        self.assertIsInstance(self.app.approved_images, list)

    def test_save_approved_images(self):
        approved_images = [{'filename': 'test1.jpg', 'language': 'EN', 'blip_caption': 'Test Caption 1', 'mistral_description': 'Test Description 1'}, {'filename': 'test2.jpg', 'language': 'EN', 'blip_caption': 'Test Caption 2', 'mistral_description': 'Test Description 2'}]
        self.app.approved_images = approved_images
        self.app.save_approved_images()
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

    def test_predefined_templates_dropdown(self):
        runner = TestRunner()
        with runner.create_app("src.image_description") as app:
            app.run()
            dropdown = app.get_widget("Select a predefined template:")
            self.assertIsNotNone(dropdown)
            self.assertIn("JSON", dropdown.options)
            self.assertIn("YAML", dropdown.options)
            self.assertIn("Plain Text", dropdown.options)

    def test_output_preview_section(self):
        runner = TestRunner()
        with runner.create_app("src.image_description") as app:
            app.run()
            preview_section = app.get_widget("Output Preview")
            self.assertIsNotNone(preview_section)
            self.assertIn("Preview the generated output below:", preview_section.text)

    def test_download_options(self):
        runner = TestRunner()
        with runner.create_app("src.image_description") as app:
            app.run()
            download_json_button = app.get_widget("Download as JSON")
            download_yaml_button = app.get_widget("Download as YAML")
            download_text_button = app.get_widget("Download as Text")
            self.assertIsNotNone(download_json_button)
            self.assertIsNotNone(download_yaml_button)
            self.assertIsNotNone(download_text_button)

if __name__ == '__main__':
    unittest.main()
