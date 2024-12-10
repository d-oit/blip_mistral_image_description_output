import os
from dotenv import load_dotenv
from deepl import Translator

def translate_text(text, target_lang):
    """Translate text to the target language using DeepL API."""
    try:
        load_dotenv()
        translator = Translator(os.getenv("DEEPL_AUTH_KEY"))
        translation = translator.translate_text(text, target_lang=target_lang)
        return translation.text
    except Exception as e:
        raise Exception(f"Translation failed: {e}")
