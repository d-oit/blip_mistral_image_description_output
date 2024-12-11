import os
import time
from playwright.sync_api import sync_playwright

def test_image_description_generator():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("http://localhost:8501")

        try:
            # Wait for the Streamlit app to load
            page.wait_for_selector("div.stApp[data-test-script-state='notRunning'][data-test-connection-state='CONNECTED']", state="visible", timeout=10000)

            images_dir = os.path.abspath("./images")
            page.fill("input[type='text']", images_dir)
            page.press("input[type='text']", "Enter")

            # Check if images are loaded
            page.wait_for_selector("img", state="visible", timeout=30000)
            image_elements = page.locator("img")
            assert image_elements.count() > 0, "No images were loaded."

            # Use the parent div to select the option
            page.get_by_test_id("stSelectbox").locator("div").filter(has_text="English").nth(2).click()
            page.get_by_text("German").click()

             # Wait for the Streamlit app to load
            page.wait_for_selector("div.stApp[data-test-script-state='notRunning'][data-test-connection-state='CONNECTED']", state="visible", timeout=60000)

            page.locator("input[type='checkbox']").first.check()
            page.locator("button", has_text="Generate Output").click()
            page.wait_for_selector("div.stApp[data-test-script-state='notRunning'][data-test-connection-state='CONNECTED']", state="visible", timeout=60000)
            assert page.locator("code.language-text").count() > 0, "Output was not generated."

        except Exception as e:
            page.screenshot(path="error_screenshot.png")
            print(f"Error during test execution: {e}")
            raise

        finally:
            browser.close()
