import streamlit as st
import os
from dotenv import load_dotenv
import base64
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
from mistralai import Mistral
import json

# Initialize BLIP model
@st.cache_resource
def load_blip_model():
    try:
        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        return processor, model
    except EnvironmentError as e:
        st.error(f"Error loading BLIP model: {e}")
        return None, None

processor, blip_model = load_blip_model()

# Function to encode image to base64
def encode_image(image_path):
    """Encode the image to base64."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        st.error(f"Error: The file {image_path} was not found.")
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# Function to describe image using BLIP and Mistral Vision API
def describe_image_with_mistral(image_path):
    try:
        # Step 1: Generate caption using BLIP
        if processor and blip_model:
            image = Image.open(image_path)
            inputs = processor(image, return_tensors="pt")
            out = blip_model.generate(**inputs)
            blip_caption = processor.decode(out[0], skip_special_tokens=True)
        else:
            blip_caption = "BLIP model not loaded. Please check for errors."

        st.write(f"BLIP Caption: {blip_caption}")  # Display BLIP caption

        # Step 2: Send the image to Mistral Vision API
        base64_image = encode_image(image_path)
        if not base64_image:
            return None, None

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"What's in this image?"
                    },
                    {
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{base64_image}"
                    }
                ]
            }
        ]

        # Call Mistral's chat API
        model = "pixtral-12b-2409"  # Specify Mistral model
        response = client.chat.complete(
            model=model,
            messages=messages
        )

        # Extract detailed description from the response
        detailed_description = response.choices[0].message.content
        return blip_caption.capitalize(), detailed_description
    except Exception as e:
        st.error(f"Error describing image with Mistral: {e}")
        return None, None

# Function to generate title and description
def generate_title_and_description(image_path):
    try:
        title, description = describe_image_with_mistral(image_path)
        if title and description:
            return title, description
        else:
            st.error("Error generating title and description.")
            return None, None
    except Exception as e:
        st.error(f"Error generating title and description: {e}")
        return None, None

# Function to load cached images
def load_cached_images():
    cache_file = 'approved_images_cache.json'
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return []
    return []


# Function to save approved images to cache
def save_approved_images(approved_images):
    cache_file = 'approved_images_cache.json'
    with open(cache_file, 'w') as file:
        json.dump(approved_images, file)

# Load cached images
cached_images = load_cached_images()

# Sidebar for configuration
st.sidebar.title("Configuration")
load_dotenv()
mistral_api_key = st.sidebar.text_input("Enter Mistral API Key:", value=os.getenv("MISTRAL_API_KEY", ""), type="password")
deepl_auth_key = st.sidebar.text_input("Enter DeepL Auth Key:", value=os.getenv("DEEPL_AUTH_KEY", ""), type="password")

# Initialize Mistral client
client = Mistral(api_key=mistral_api_key)

# Streamlit UI
st.title("Image Description Generator with BLIP and Mistral Vision")

# Folder selection
folder_path = st.text_input("Enter the path to the folder containing images:")

# Language selection for translation
languages = {
    'English': 'EN', 'Spanish': 'ES', 'French': 'FR', 'German': 'DE',
    'Italian': 'IT', 'Japanese': 'JA', 'Chinese': 'ZH'
}
target_lang = st.selectbox("Select language for translation:", list(languages.keys()))

# Config for setting approved to true as default
st.session_state.setdefault('approved', True)

if folder_path and os.path.isdir(folder_path):
    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]

    approved_images = []

    for image_file in image_files:
        image_path = os.path.join(folder_path, image_file)
        image = Image.open(image_path)

        st.image(image, caption=image_file, use_container_width=True)

        # Check if the image is already cached
        cache_key = f"{image_file}_{target_lang}"
        cached_image = next((img for img in cached_images if img['cache_key'] == cache_key), None)
        if cached_image:
            title = cached_image['title']
            description = cached_image['description']
        else:
            # Generate title and description
            title, description = generate_title_and_description(image_path)
            if title and description:
                cached_images.append({
                    "cache_key": cache_key,
                    "src": image_file,
                    "title": title,
                    "description": description
                })

        st.write("Title:", title)
        st.write("Description:", description)

        # Translate caption
        if target_lang != 'English':
            try:
                from deepl import Translator
                translator = Translator(deepl_auth_key)
                translated_title = translator.translate_text(title, target_lang=languages[target_lang])
                translated_description = translator.translate_text(description, target_lang=languages[target_lang])
                st.write(f"Translated Title ({target_lang}):", translated_title.text)
                st.write(f"Translated Description ({target_lang}):", translated_description.text)
            except Exception as e:
                st.error(f"Translation failed: {e}")

        # Approval mechanism
        if st.checkbox("Approve this description?", key=image_file, value=st.session_state.approved):
            st.success("Description approved!")
            approved_images.append({
                "cache_key": cache_key,
                "src": image_file,
                "title": translated_title.text if target_lang != 'English' else title,
                "description": translated_description.text if target_lang != 'English' else description
            })
        else:
            st.warning("Description not approved.")

        st.markdown("---")

    # Output format section
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
        for approved_image in approved_images:
            output_resources.append({
                "src": approved_image["src"],
                "title": approved_image["title"],
                "params": {
                    "description": approved_image["description"]
                }
            })

        output_text = "resources:\n" + "\n".join([
            f"  - src: \"{resource['src']}\"\n    title: \"{resource['title']}\"\n    params:\n      description: \"{resource['params']['description']}\""
            for resource in output_resources
        ])

        st.code(output_text, language="text")
            
    # Save approved images to cache
    save_approved_images(approved_images)

else:
    st.warning("Please enter a valid folder path.")

# Instructions
st.sidebar.header("Instructions")
st.sidebar.markdown("""
1. Enter the path to a folder containing images.
2. Select a target language for translation.
3. View the generated descriptions and translations.
4. Optionally approve each description.
5. Configure the output format and generate the output.
""")
