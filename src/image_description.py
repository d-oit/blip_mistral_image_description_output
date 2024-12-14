#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import logging
import base64
import json
from io import BytesIO
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
import streamlit as st
from PIL import Image
from dotenv import load_dotenv
from transformers import BlipProcessor, BlipForConditionalGeneration
from mistralai import Mistral
from deepl import Translator

@dataclass
class AppConfig:
    """Configuration for the Image Description App."""
    mistral_api_key: str = ""
    deepl_auth_key: str = ""
    model_path: str = "Salesforce/blip-image-captioning-base"
    target_languages: Dict[str, str] = field(default_factory=lambda: {
        'English': 'EN', 'Spanish': 'ES', 'French': 'FR',
        'German': 'DE', 'Italian': 'IT', 'Japanese': 'JA', 'Chinese': 'ZH'
    })

class ImageDescriptionApp:
    """Main application class for generating image descriptions."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.setup_logging()
        self.processor, self.blip_model, self.mistral_client = self.load_models()
        self.load_approved_images()
        self.processed_images = []

    def setup_logging(self):
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler("image_description_app.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    @st.cache_resource
    def load_models(_self):
        """Load the models required for image description."""
        start_time = time.time()
        try:
            processor = BlipProcessor.from_pretrained(_self.config.model_path)
            model = BlipForConditionalGeneration.from_pretrained(
                _self.config.model_path
            )
            mistral_client = Mistral(api_key=_self.config.mistral_api_key)
            load_time = time.time() - start_time
            logging.info(
                "Models loaded successfully in %.4f seconds", load_time
            )
            return processor, model, mistral_client
        except Exception as e:
            logging.error("Model loading error: %s", e)
            return None, None, None

    def encode_image(self, image_path: str) -> Optional[str]:
        """Encode the image to base64."""
        try:
            with open(image_path, "rb") as image_file:
                image = Image.open(image_file)
                image = image.convert("RGB")
                buffered = BytesIO()
                image.save(buffered, format="JPEG")
                return base64.b64encode(buffered.getvalue()).decode("utf-8")
        except FileNotFoundError as e:
            self.logger.error(
                "Image encoding error for %s: %s", image_path, e
            )
            return None
        except Exception as e:
            self.logger.error(
                "Image encoding error for %s: %s", image_path, e
            )
            return None

    def describe_image(self, image_path: str, language: str) -> Dict[str, Any]:
        """Describe the image using BLIP and Mistral models."""
        start_time = time.time()
        processing_times = {}

        # Check if the description is already in the approved images cache
        for img in self.approved_images:
            if (img["filename"] == os.path.basename(image_path) and
                    img["language"] == language):
                return img

        try:
            # Image loading
            image_load_start = time.time()
            image = Image.open(image_path)
            processing_times['image_load'] = time.time() - image_load_start

            # BLIP caption generation
            blip_start = time.time()
            inputs = self.processor(image, return_tensors="pt")
            out = self.blip_model.generate(**inputs)

            try:
                blip_caption = self.processor.decode(
                    out[0], skip_special_tokens=True
                )
            except Exception as e:
                self.logger.error("Error decoding BLIP caption: %s", e)
                blip_caption = ''

            processing_times['blip_processing'] = time.time() - blip_start

            # Mistral Vision description
            mistral_start = time.time()
            base64_image = self.encode_image(image_path)
            if not base64_image:
                return {"filename": os.path.basename(image_path)}
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": st.session_state.image_prompt},
                        {"type": "image_url",
                         "image_url": f"data:image/jpeg;base64,{base64_image}"}
                    ]
                }
            ]

            response = self.mistral_client.chat.complete(
                model="pixtral-12b-2409",
                messages=messages
            )

            processing_times['mistral_processing'] = time.time() - mistral_start
            mistral_description = response.choices[0].message.content

            # Total processing time
            total_time = time.time() - start_time

            result = {
                "filename": os.path.basename(image_path),
                "language": language,
                "blip_caption": blip_caption.capitalize(),
                "mistral_description": mistral_description,
                "processing_times": processing_times,
                "total_processing_time": total_time
            }

            return result

        except FileNotFoundError as e:
            self.logger.error("Image description error: %s", e)
            return {"filename": os.path.basename(image_path)}
        except Exception as e:
            self.logger.error("Image description error: %s", e)
            return {"filename": os.path.basename(image_path)}

    def translate_text(self, text: str, target_language: str) -> Optional[str]:
        """Translate text to the target language using DeepL API."""
        start_time = time.time()
        try:
            translator = Translator(self.config.deepl_auth_key)
            translated_text = translator.translate_text(
                text, target_lang=target_language
            )
            translation_time = time.time() - start_time
            self.logger.info(
                "Translation to %s completed in %.4f seconds",
                target_language, translation_time
            )
            return translated_text.text
        except Exception as e:
            self.logger.error("Translation error: %s", e)
            return None

    def render_sidebar(self):
        """Render the sidebar for the Streamlit app."""
        if 'folder_path' not in st.session_state:
            st.session_state.folder_path = ""
        if 'target_lang' not in st.session_state:
            st.session_state.target_lang = list(
                self.config.target_languages.keys())[0]

        folder_path = st.sidebar.text_input(
            "Enter the path to the image folder:",
            value=st.session_state.folder_path
        )
        st.session_state.folder_path = folder_path

        target_lang = st.sidebar.selectbox(
            "Select translation language:",
            list(self.config.target_languages.keys()),
            index=list(self.config.target_languages.keys()).index(
                st.session_state.target_lang)
        )
        st.session_state.target_lang = target_lang

        if st.sidebar.button("▶️ Start"):
            st.session_state.started = True

        st.sidebar.header("🔑 API Configuration")
        self.config.mistral_api_key = st.sidebar.text_input(
            "Mistral API Key",
            value=self.config.mistral_api_key,
            type="password"
        )
        self.config.deepl_auth_key = st.sidebar.text_input(
            "DeepL Auth Key",
            value=self.config.deepl_auth_key,
            type="password"
        )

        st.sidebar.header("📝 Instructions")
        st.sidebar.markdown("""
        ### How to Use
        1. Enter API Keys
        2. Select Image Folder
        3. Choose Translation Language
        4. Generate Descriptions
        5. Export Results
        """)

    def load_approved_images(self):
        """Load approved images from the cache file."""
        cache_file = 'approved_images_cache.json'
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.approved_images = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                self.logger.warning(
                    "Error loading approved images: %s. Starting with an empty cache.",
                    e
                )
                self.approved_images = []
        else:
            self.approved_images = []

    def save_approved_images(self):
        """Save approved images to the cache file."""
        cache_file = 'approved_images_cache.json'
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.approved_images, f, indent=4)
            self.logger.info("Approved images saved to %s", cache_file)
        except Exception as e:
            self.logger.error("Error saving approved images: %s", e)

    def check_and_delete_cache(self):
        """Check if the prompt has changed and delete the cache file if it has."""
        cache_file = 'approved_images_cache.json'
        prompt_file = 'image_prompt.txt'

        # Check if the prompt file exists
        if os.path.exists(prompt_file):
            with open(prompt_file, 'r', encoding='utf-8') as f:
                saved_prompt = f.read().strip()

            # Compare the saved prompt with the current prompt
            if saved_prompt != st.session_state.image_prompt:
                # Prompt has changed, delete the cache file
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                    self.logger.info("Cache file deleted due to prompt change.")

                # Update the prompt file with the current prompt
                with open(prompt_file, 'w', encoding='utf-8') as f:
                    f.write(st.session_state.image_prompt)
        else:
            # Prompt file does not exist, create it with the current prompt
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(st.session_state.image_prompt)

    def run(self):
        """Run the Streamlit app."""
        # Render sidebar
        self.render_sidebar()

        if 'started' not in st.session_state:
            st.session_state.started = False
        
        

        if st.session_state.started:
            # Main app title
            st.title("🖼️ Image Description Generator")

            if 'image_prompt' not in st.session_state:
                st.session_state.image_prompt = (
                    "Describe the contents of this image in vivid detail, "
                    "as if a human observer is interpreting the scene. "
                    "Try to include the place where the image was created "
                    "and add it only if you are sure where it was created. "
                    "The person on the image is me. Maximum of 120 lively words."
                )
            image_prompt = st.text_area("Prompt:",
                                          value=st.session_state.image_prompt)
            st.session_state.image_prompt = image_prompt

            # Check and delete cache if prompt has changed
            self.check_and_delete_cache()

            # Process images
            if (st.session_state.folder_path and
                    os.path.isdir(st.session_state.folder_path)):
                image_files = [
                    f for f in os.listdir(st.session_state.folder_path)
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
                ]

                # Reset processed images
                self.processed_images = []

                for image_file in image_files:
                    full_path = os.path.join(
                        st.session_state.folder_path, image_file
                    )
                    try:
                        image = Image.open(full_path)

                        st.image(image, caption=image_file,
                                 use_container_width=True)

                        # Process image
                        description = self.describe_image(
                            full_path,
                            language=self.config.target_languages[
                                st.session_state.target_lang]
                        )

                        if description:
                            # Display original descriptions
                            st.write("BLIP Caption:",
                                     description['blip_caption'])
                            st.write("Mistral Description:",
                                     description['mistral_description'])

                            # Display processing times
                            if (description and
                                    'processing_times' in description):
                                if len(description['processing_times']) > 0:
                                    st.write("Processing Times:")
                                    for step, time_taken in description[
                                            'processing_times'].items():
                                        st.write(
                                            f"- {step.replace('_', ' ').title()}: {time_taken:.4f} seconds")
                                    st.write(
                                        f"Total Processing Time: {description['total_processing_time']:.4f} seconds")

                            # Translate if needed
                            if st.session_state.target_lang != 'English':
                                translated_caption = self.translate_text(
                                    description['blip_caption'],
                                    self.config.target_languages[
                                        st.session_state.target_lang]
                                )
                                translated_description = self.translate_text(
                                    description['mistral_description'],
                                    self.config.target_languages[
                                        st.session_state.target_lang]
                                )

                                st.write(
                                    f"Translated Caption ({st.session_state.target_lang}):",
                                    translated_caption
                                )
                                st.write(
                                    f"Translated Description ({st.session_state.target_lang}):",
                                    translated_description
                                )

                            # Store processed image info
                            processed_image_info = {
                                "filename": description['filename'],
                                "language": description['language'],
                                "blip_caption": description['blip_caption'],
                                "mistral_description": description[
                                    'mistral_description'],
                                "translated_caption": translated_caption if
                                st.session_state.target_lang != 'English' else None,
                                "translated_description": translated_description
                                if st.session_state.target_lang != 'English'
                                else None,
                            }
                            self.processed_images.append(processed_image_info)

                        # Approval mechanism
                        approved = st.checkbox(
                            f"Approve {image_file}?",
                            key=image_file,
                            value=True
                        )
                        if approved:
                            if processed_image_info not in self.approved_images:
                                self.approved_images.append(
                                    processed_image_info
                                )
                                self.save_approved_images()
                                st.success(f"{image_file} approved!")
                        else:
                            if processed_image_info in self.approved_images:
                                self.approved_images.remove(
                                    processed_image_info
                                )
                                self.save_approved_images()
                                st.warning(f"{image_file} not approved.")
                        st.markdown("---")

                    except FileNotFoundError as e:
                        self.logger.error(
                            "Error processing %s: %s", image_file, e
                        )
                        st.error(f"Error processing {image_file}: {e}")
                    except Exception as e:
                        self.logger.error(
                            "Error processing %s: %s", image_file, e
                        )
                        st.error(f"Error processing {image_file}: {e}")

                # Output Generation Section
                st.header("Output Format")
                st.write("Configure the output format below:")

                if 'outputConfigurationValue' not in st.session_state or not st.session_state.outputConfigurationValue:
                    st.session_state.outputConfigurationValue = ("""
                                    resources:
                                    - src: "{image_file}"
                                        title: "{output_title}"
                                        params:
                                        description: "{output_description}"
                                    """)

                st.session_state.outputConfigurationValue = st.text_area(
                    "Output Configuration",
                    value=st.session_state.outputConfigurationValue
                )

                if st.button("Generate Output"):
                    output_resources = []
                    seen_filenames = set()
                    selected_language_code = self.config.target_languages[
                        st.session_state.target_lang]
                    for img in self.approved_images:
                        if img['language'] == selected_language_code:
                            export_key = f"{img['filename']}_{img['language']}"
                            if export_key not in seen_filenames:
                                seen_filenames.add(export_key)

                                # Replace placeholders in the user-defined configuration string
                                config_value = st.session_state.outputConfigurationValue
                                config_value = config_value.replace("{image_file}", img["filename"])
                                config_value = config_value.replace("{output_title}", img["translated_caption"] if st.session_state.target_lang != 'English' else img["blip_caption"])
                                config_value = config_value.replace("{output_description}", img["translated_description"] if st.session_state.target_lang != 'English' else img["mistral_description"])

                                # Append the replaced configuration to the output list
                                output_resources.append(config_value)

                    st.code("".join(output_resources), language="text")

            else:
                st.warning("Please enter a valid folder path containing images.")

def main():
    """Set up and run the Streamlit app."""
    # Set page configuration
    st.set_page_config(
        page_title="Image Description Generator",
        page_icon="🖼️",
        layout="wide"
    )

    # Load environment variables
    load_dotenv()

    # Create configuration
    config = AppConfig(
        mistral_api_key=os.getenv("MISTRAL_API_KEY", ""),
        deepl_auth_key=os.getenv("DEEPL_AUTH_KEY", "")
    )

    # Run the app
    app = ImageDescriptionApp(config)
    app.run()

if __name__ == "__main__":
    main()
