import time
import io
import json
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import random
import os

OUTPUT_DIR = "output"  # Constant for main output directory

def ensure_directory_exists(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def setup_directories(username):
    # Create/Ensure main output directory exists
    ensure_directory_exists(OUTPUT_DIR)
    
    # Create user-specific directory within OUTPUT_DIR
    user_dir = os.path.join(OUTPUT_DIR, username)
    ensure_directory_exists(user_dir)
    
    # Create screenshots directory within user-specific directory
    screenshot_dir = os.path.join(user_dir, "screenshots")
    ensure_directory_exists(screenshot_dir)
    
    return screenshot_dir

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f"user-agent={user_agent}")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def set_cookies(driver):
    base_domain = "https://twitter.com"
    driver.get(base_domain)
    with open("cookies.json", "r") as file:
        cookies = json.load(file)
        for cookie in cookies:
            if 'sameSite' in cookie:
                del cookie['sameSite']
            driver.add_cookie(cookie)

def find_overlap(img1, img2):
    overlap_height = 0
    for y in range(img1.height):
        row_img1 = list(img1.crop((0, img1.height-y-1, img1.width, img1.height-y)).getdata())
        row_img2 = list(img2.crop((0, 0, img2.width, 1)).getdata())
        if row_img1 == row_img2:
            overlap_height = y + 1
            break  # Break the loop once the overlap is found
    print(f"Calculated overlap: {overlap_height} pixels")
    return overlap_height

def combine_images(image_files, output_filename):
    images = [Image.open(image_file) for image_file in image_files]
    
    total_width = max(img.width for img in images)
    total_height = sum(img.height for img in images)
    
    # Calculate the overlap for the first two images and assume it's consistent for all images
    if len(images) > 1:
        overlap = find_overlap(images[0], images[1])
    else:
        overlap = 0

    # Adjust the total height based on the calculated overlap
    total_height -= overlap * (len(images) - 1)

    stitched_image = Image.new("RGB", (total_width, total_height))
    
    y_offset = 0
    for i, img in enumerate(images):
        print(f"Pasting image {i} at y_offset: {y_offset}")  # Debug print
        stitched_image.paste(img, (0, y_offset))
        y_offset += img.height
        if i < len(images) - 1:
            y_offset -= overlap  # Use the consistent overlap value
    
    print(f"Final stitched image dimensions: {stitched_image.size}")  # Debug print
    stitched_image.save(output_filename)

def capture_timeline_screenshots(driver, url, username):
    def human_like_scrolling(driver):
        """Simulate human-like scrolling by scrolling in smaller chunks."""
        viewport_height = driver.execute_script("return window.innerHeight")
        scroll_increment = viewport_height * 0.8  # Scroll 80% of the viewport height for 20% overlap
        driver.execute_script(f"window.scrollBy(0, {scroll_increment});")
        time.sleep(random.uniform(0.2, 0.5))  # Short pauses between scrolls

    def hide_elements(driver, selectors):
        """Hide elements on the page using their CSS selectors."""
        for selector in selectors:
            try:
                element = driver.execute_script(f"return document.querySelector('{selector}');")
                if element:
                    driver.execute_script(f"document.querySelector('{selector}').style.display = 'none';")
            except Exception as e:
                print(f"Error hiding element with selector {selector}: {e}")

    def capture_and_crop_screenshot(driver, filename, x, y, width, height):
        def get_non_transparent_height(image):
            """Find the height of the image until it has content (non-transparent)."""
            for y_coord in reversed(range(image.height)):
                # Check the alpha value of the center pixel in the row
                _, _, _, alpha = image.getpixel((image.width // 2, y_coord))
                if alpha != 0:
                    return y_coord + 1
            return image.height

        screenshot = driver.get_screenshot_as_png()
        im = Image.open(io.BytesIO(screenshot))
        actual_height = get_non_transparent_height(im)
        cropped_im = im.crop((x, y, x + width, y + min(height, actual_height)))
        cropped_im.save(filename)

    screenshot_num = 1
    last_screenshot = None

    driver.get(url)
    time.sleep(2)

    problematic_selectors = ["#react-root > div > div > div.css-1dbjc4n.r-18u37iz.r-13qz1uu.r-417010 > main > div > div > div > div.css-1dbjc4n.r-kemksi.r-1kqtdi0.r-1ljd8xs.r-13l2t4g.r-1phboty.r-16y2uox.r-1jgb5lz.r-11wrixw.r-61z16t.r-1ye8kvj.r-13qz1uu.r-184en5c > div > div.css-1dbjc4n.r-aqfbo4.r-gtdqiz.r-1gn8etr.r-1g40b8q"]
    hide_elements(driver, problematic_selectors)
    
    #input("Press Enter to continue...")

    # Identify the timeline element ONCE at the beginning
    timeline_element = driver.find_element(By.CSS_SELECTOR, "#react-root > div > div > div.css-1dbjc4n.r-18u37iz.r-13qz1uu.r-417010 > main > div > div > div > div.css-1dbjc4n.r-kemksi.r-1kqtdi0.r-1ljd8xs.r-13l2t4g.r-1phboty.r-16y2uox.r-1jgb5lz.r-11wrixw.r-61z16t.r-1ye8kvj.r-13qz1uu.r-184en5c")
    timeline_location = timeline_element.location
    timeline_size = timeline_element.size
    timeline_actual_height = driver.execute_script("return arguments[0].scrollHeight;", timeline_element)

    screenshot_dir = setup_directories(username)  # Setting up directories

    while True:
        screenshot_path = os.path.join(screenshot_dir, f"timeline_screenshot_{screenshot_num}.png")
        capture_and_crop_screenshot(driver, screenshot_path, timeline_location['x'], timeline_location['y'], timeline_size['width'], timeline_actual_height)
        
        # Check if the current screenshot is the same as the previous one
        if last_screenshot:
            current_screenshot = Image.open(screenshot_path)
            if list(current_screenshot.getdata()) == list(last_screenshot.getdata()):
                # If the screenshots are identical, we've reached the end
                os.remove(screenshot_path)  # Remove the redundant screenshot
                break
            last_screenshot = current_screenshot
        else:
            last_screenshot = Image.open(screenshot_path)

        screenshot_num += 1

        human_like_scrolling(driver)
        time.sleep(2)

    # Combine screenshots
    image_files = [os.path.join(screenshot_dir, f"timeline_screenshot_{i}.png") for i in range(1, screenshot_num)]
    combined_image_path = os.path.join(screenshot_dir, "combined_timeline.png")
    combine_images(image_files, combined_image_path)

    print(f"Captured {screenshot_num - 1} screenshots.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Capture and stitch a user's Twitter timeline.")
    parser.add_argument("-u", "--username", type=str, default="", help="Twitter username to capture.")
    args = parser.parse_args()

    base_url = "https://twitter.com/"
    target_url = base_url + args.username

    driver = setup_driver()

    set_cookies(driver)
    capture_timeline_screenshots(driver, target_url, args.username)
    driver.quit()
