import unittest
import os
from src.utils.image_utils import encode_image
from src.utils.translation import translate_text
from unittest.mock import patch, MagicMock

class TestUtils(unittest.TestCase):
    def test_encode_image(self):
        # Test with a valid image path
        image_path = 'images/IMG_20241105_174257.jpg'
        if os.path.exists(image_path):
            encoded_image = encode_image(image_path)
            self.assertIsNotNone(encoded_image)
            self.assertIsInstance(encoded_image, str)
            self.assertGreater(len(encoded_image), 100)  # Check for a reasonable length
        else:
            print(f"Warning: Test image {image_path} not found. Skipping this test case.")

        # Test with an invalid image path
        image_path = 'invalid_image.jpg'
        with self.assertRaises(FileNotFoundError):
            encode_image(image_path)


    @patch('src.utils.translation.Translator')
    def test_translate_text(self, mock_translator_class):
        # Create a mock translator instance
        mock_translator = mock_translator_class.return_value

        # Test with valid input
        text = 'Hello, world!'
        mock_translation = MagicMock(text='Hallo, Welt!')
        mock_translator.translate_text.return_value = mock_translation
        translated_text = translate_text(text, 'de')
        print(f"Translated text: {translated_text}")  # Debugging line
        self.assertEqual(translated_text, 'Hallo, Welt!')



if __name__ == '__main__':
    unittest.main()
