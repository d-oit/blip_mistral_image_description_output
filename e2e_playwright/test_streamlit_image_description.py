import os
from playwright.sync_api import sync_playwright

def test_streamlit_image_description():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Navigate to the Streamlit app
        page.goto('http://localhost:8501')
        page.wait_for_load_state('networkidle')

        # Wait for the folder path input to be present
        page.wait_for_selector('input[type="text"]')

        # Set the folder path
        folder_path = os.path.join(os.path.dirname(__file__), '..', 'images')
        page.fill('input[type="text"]', folder_path)
        page.press('input[type="text"]', 'Enter')
       
        # Wait for the image descriptions to be generated
        page.wait_for_selector('text=Title:')
        page.wait_for_selector('text=Description:')

        # Verify the image descriptions
        titles = page.query_selector_all('text=Title:')
        descriptions = page.query_selector_all('text=Description:')
        assert len(titles) > 0, "No titles were generated"
        assert len(descriptions) > 0, "No descriptions were generated"

        # Approve the descriptions
        approve_buttons = page.query_selector_all('input[type="checkbox"]')
        for button in approve_buttons:
            page.check('input[type="checkbox"]')

        # Generate output
        page.click('button:has-text("Generate Output")')

        # Verify the output
        output = page.query_selector('code')
        assert output is not None, "Output was not generated"

        browser.close()
