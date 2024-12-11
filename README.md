# Image Description Generator with BLIP and Mistral Vision

This project is a Streamlit application that generates image descriptions using the BLIP model and Mistral Vision API. It allows users to input a folder of images, generate descriptions, translate them into different languages, and approve the descriptions.

## Features

- Generate image descriptions using BLIP and Mistral Vision API.
- Translate descriptions into multiple languages (currently supports English, Spanish, French, German, Italian, Japanese, and Chinese).
- Approve and cache descriptions for future use.
- Configure and generate output in a specified format.

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

The Streamlit application provides a user-friendly interface for uploading images, generating descriptions, and approving them.  Detailed instructions on using the application will be available within the Streamlit app itself.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.
