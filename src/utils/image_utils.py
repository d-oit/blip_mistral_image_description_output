"""
Utility functions for image processing.
"""

import base64
from PIL import Image

def encode_image(image_path: str) -> str:
    """Encode the image to base64."""
    try:
        with open(image_path, "rb") as image_file:
            image = Image.open(image_file)
            image.thumbnail((800, 800))
            buffered = BytesIO()
            image.save(buffered, format="JPEG")
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Error: The file {image_path} was not found.") from exc
    except Exception as e:
        raise Exception(f"Error: {e}") from e
