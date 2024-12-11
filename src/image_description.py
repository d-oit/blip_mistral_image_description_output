import os
import time
import logging
import base64
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field

import streamlit as st
import torch
from PIL import Image
from dotenv import load_dotenv

@dataclass
class AppConfig:
    mistral_api_key: str = ""
    deepl_auth_key: str = ""
    model_path: str = "Salesforce/blip-image-captioning-base"
    target_languages: Dict[str, str] = field(default_factory=lambda: {
        'English': 'EN', 'Spanish': 'ES', 'French': 'FR',
        'German': 'DE', 'Italian': 'IT', 'Japanese': 'JA', 'Chinese': 'ZH'
    })

class ImageDescriptionApp:
    def __init__(self, config: AppConfig):
        self.config = config
        self.setup_logging()
        self.processor, self.blip_model, self.mistral_client = self.load_models()
        self.load_approved_images()

    def setup_logging(self):
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
        start_time = time.time()
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration
            from mistralai import Mistral

            processor = BlipProcessor.from_pretrained(_self.config.model_path)
            model = BlipForConditionalGeneration.from_pretrained(_self.config.model_path)

            mistral_client = Mistral(api_key=_self.config.mistral_api_key)

            load_time = time.time() - start_time
            logging.info(f"Models loaded successfully in {load_time:.4f} seconds")

            return processor, model, mistral_client
        except Exception as e:
            logging.error(f"Model loading error: {e}")
            return None, None, None

    def encode_image(self, image_path: str) -> Optional[str]:
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            self.logger.error(f"Image encoding error for {image_path}: {e}")
            return None

    def describe_image(self, image_path: str, language: str) -> Dict[str, Any]:
        start_time = time.time()
        processing_times = {}

        # Check if the description is already in the approved images cache
        for img in self.approved_images:
            if img["filename"] == os.path.basename(image_path) and img["language"] == language:
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
            blip_caption = self.processor.decode(out[0], skip_special_tokens=True)
            processing_times['blip_processing'] = time.time() - blip_start

            # Mistral Vision description
            mistral_start = time.time()
            base64_image = self.encode_image(image_path)
            if not base64_image:
                return {"filename": os.path.basename(image_path)} # Return filename even if encoding fails

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What's in this image?"},
                        {"type": "image_url", "image_url": f"data:image/jpeg;base64,{base64_image}"}
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

        except Exception as e:
            self.logger.error(f"Image description error: {e}")
            return {"filename": os.path.basename(image_path)} # Return filename even if description fails

    def translate_text(self, text: str, target_language: str) -> Optional[str]:
        start_time = time.time()
        try:
            from deepl import Translator
            translator = Translator(self.config.deepl_auth_key)
            translated_text = translator.translate_text(text, target_lang=target_language)
            translation_time = time.time() - start_time
            self.logger.info(f"Translation to {target_language} completed in {translation_time:.4f} seconds")
            return translated_text.text
        except Exception as e:
            self.logger.error(f"Translation error: {e}")
            return None

    def render_sidebar(self):
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
        cache_file = 'approved_images_cache.json'
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    self.approved_images = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                self.logger.warning(f"Error loading approved images: {e}. Starting with an empty cache.")
                self.approved_images = []
        else:
            self.approved_images = []

    def save_approved_images(self):
        cache_file = 'approved_images_cache.json'
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.approved_images, f, indent=4)
            self.logger.info(f"Approved images saved to {cache_file}")
        except Exception as e:
            self.logger.error(f"Error saving approved images: {e}")

    def run(self):
        # Render sidebar
        self.render_sidebar()

        # Main app title
        st.title("🖼️ Image Description Generator")

        # Folder and language selection
        if 'folder_path' not in st.session_state:
            st.session_state.folder_path = ""
        folder_path = st.text_input("Enter the path to the image folder:", value=st.session_state.folder_path)
        st.session_state.folder_path = folder_path

        if 'target_lang' not in st.session_state:
            st.session_state.target_lang = list(self.config.target_languages.keys())[0]
        target_lang = st.selectbox(
            "Select translation language:",
            list(self.config.target_languages.keys()),
            index=list(self.config.target_languages.keys()).index(st.session_state.target_lang)
        )
        st.session_state.target_lang = target_lang

        # Process images
        if folder_path and os.path.isdir(folder_path):
            image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]

            # Reset processed images
            self.processed_images = []

            for image_file in image_files:
                full_path = os.path.join(folder_path, image_file)
                try:
                    image = Image.open(full_path)

                    st.image(image, caption=image_file, use_container_width=True)

                    # Process image
                    description = self.describe_image(full_path, language=self.config.target_languages[target_lang])

                    if description:
                        # Display original descriptions
                        st.write("BLIP Caption:", description['blip_caption'])
                        st.write("Mistral Description:", description['mistral_description'])

                        # Display processing times
                        if description and 'processing_times' in description:
                            if len(description['processing_times']) > 0:
                                st.write("Processing Times:")
                                for step, time_taken in description['processing_times'].items():
                                    st.write(f"- {step.replace('_', ' ').title()}: {time_taken:.4f} seconds")
                                st.write(f"Total Processing Time: {description['total_processing_time']:.4f} seconds")

                        # Translate if needed
                        if target_lang != 'English':
                            translated_caption = self.translate_text(
                                description['blip_caption'],
                                self.config.target_languages[target_lang]
                            )
                            translated_description = self.translate_text(
                                description['mistral_description'],
                                self.config.target_languages[target_lang]
                            )

                            st.write(f"Translated Caption ({target_lang}):", translated_caption)
                            st.write(f"Translated Description ({target_lang}):", translated_description)

                        # Store processed image info
                        processed_image_info = {
                            "filename": description['filename'],
                            "language": description['language'],  # Include the language key
                            "blip_caption": description['blip_caption'],
                            "mistral_description": description['mistral_description'],
                            "translated_caption": translated_caption if target_lang != 'English' else None,
                            "translated_description": translated_description if target_lang != 'English' else None,
                        }
                        self.processed_images.append(processed_image_info)

                    # Approval mechanism
                    approved = st.checkbox(f"Approve {image_file}?", key=image_file, value=True)
                    if approved:
                        if processed_image_info not in self.approved_images:
                            self.approved_images.append(processed_image_info)
                            self.save_approved_images()
                            st.success(f"{image_file} approved!")
                    else:
                        if processed_image_info in self.approved_images:
                            self.approved_images.remove(processed_image_info)
                            self.save_approved_images()
                            st.warning(f"{image_file} not approved.")
                    st.markdown("---")

                except Exception as e:
                    self.logger.error(f"Error processing {image_file}: {e}")
                    st.error(f"Error processing {image_file}: {e}")

            # Output Generation Section
            st.header("Output Format")
            st.write("Configure the output format below:")

            output_config = st.text_area("Output Configuration", value="""
                            resources:
                            - src: "{image_file}"
                                title: "{output_title}"
                                params:
                                description: "{output_description}"
                            """)

            if st.button("Generate Output"):
                output_resources = []
                seen_filenames = set()
                selected_language_code = self.config.target_languages[target_lang]
                for img in self.approved_images:
                    if img['language'] == selected_language_code:
                        export_key = f"{img['filename']}_{img['language']}"
                        if export_key not in seen_filenames:
                            output_resources.append({
                                "src": img["filename"],
                                "title": img["translated_caption"] if target_lang != 'English' else img["blip_caption"],
                                "params": {
                                    "description": img["translated_description"] if target_lang != 'English' else img["mistral_description"]
                                }
                            })
                            seen_filenames.add(export_key)

                output_text = "resources:\n" + "\n".join([
                    f"  - src: \"{resource['src']}\"\n    title: \"{resource['title']}\"\n    params:\n      description: \"{resource['params']['description']}\""
                    for resource in output_resources
                ])

                st.code(output_text, language="text")

        else:
            st.warning("Please enter a valid folder path containing images.")

def main():
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
