# Image Description Generator with BLIP and Mistral Vision

## Version 0.3.0

- Added support for additional languages in translation.
- Improved description generation accuracy.
- Enhanced user interface for better usability.

This project is a Streamlit application that generates image descriptions using the BLIP model and Mistral Vision API. It allows users to input a folder of images, generate descriptions, translate them into different languages, and approve the descriptions.

## Features

- Generate image descriptions using BLIP (model="Salesforce/blip-image-captioning-base") and Mistral Vision (model="pixtral-12b-2409") API.
- Translate descriptions into multiple languages (currently supports English, Spanish, French, German, Italian, Japanese, and Chinese).
- Approve and cache descriptions for future use.
- Configure and generate output in a specified format.
- Caching mechanism to prevent redundant operations and optimize performance.
- Multithreading for caching and saving approved images.

## Technologies Used

- Streamlit for the user interface.
- BLIP model for image description generation.
- Mistral Vision API for image description generation.
- DeepL API for translation.
- Python for backend logic.

## Installation

1.  **Prerequisites:** Ensure you have Python 3.9 or higher installed.

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Variables:** Create a `.env` file in the project root directory and add your API keys:
    ```
    MISTRAL_API_KEY=your_mistral_api_key
    DEEPL_AUTH_KEY=your_deepl_api_key
    # Add other environment variables as needed
    ```

4.  **Project Structure:** The project is structured with the following key directories:
    - `src`: Contains the Python code for the application logic.
    - `tests`: Contains unit tests for the application.
    - `e2e_playwright`: Contains end-to-end tests using Playwright.
    - `images`: Contains the sample image files.

5.  **Running the Application:**
    ```bash
    streamlit run src/image_description.py
    ```

## Usage

The Streamlit application provides a user-friendly interface for uploading images, generating descriptions, and approving them. Detailed instructions on using the application will be available within the Streamlit app itself.

### Selecting Predefined Templates

1. In the Streamlit app, navigate to the "Output Format" section.
2. Select a predefined template from the dropdown menu. Available templates include JSON, YAML, and Plain Text.
3. Customize the selected template by editing the configuration string in the "Output Configuration" text area.

### Previewing and Downloading the Generated Output

1. After generating the output, a preview section will display the generated output before finalizing it.
2. Make adjustments to the configuration string and see the changes reflected in real-time.
3. Download the generated output in different formats (e.g., JSON, YAML, text) using the provided download options.

## Caching Mechanism and Optimizations

### Caching Expensive Operations

To improve performance, the application uses `st.experimental_memo` to cache expensive operations like model loading. This prevents the need to reload models every time the app reruns, significantly reducing the load time.

### Caching API Clients

The application uses `st.experimental_singleton` to cache API clients. This ensures that the API clients are only initialized once, reducing the overhead of creating new instances for each run.

### Optimized Image Handling

Images are resized and compressed before processing to reduce the amount of data being handled. This improves the performance of image processing tasks and reduces memory usage. Efficient image encoding and decoding techniques from `src/utils/image_utils.py` are utilized to minimize the overhead of handling large image files.

### Multithreading for Caching and Saving Approved Images

The application uses multithreading to handle the caching and saving of approved images. This is implemented in the `save_approved_images` method in `src/image_description.py`. By performing these tasks concurrently with other operations, the overall performance of the application is improved, especially when dealing with a large number of images.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.
