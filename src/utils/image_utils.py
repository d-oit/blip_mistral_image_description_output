import base64
from PIL import Image

def encode_image(image_path):
    """Encode the image to base64."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: The file {image_path} was not found.")
    except Exception as e:
        raise Exception(f"Error: {e}")
