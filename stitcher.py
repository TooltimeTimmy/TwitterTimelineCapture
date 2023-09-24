import time
import io
import json
import argparse
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from PIL import Image
import random

# Constants
OUTPUT_DIR = "output"  # Main output directory


def ensure_directory_exists(dir_path):
    """Ensure the directory exists. If not, create it."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def setup_directories(username):
    """Setup the directory structure for output."""
    ensure_directory_exists(OUTPUT_DIR)  # Ensure main output directory exists
    user_dir = os.path.join(OUTPUT_DIR, username)  # User-specific directory
    ensure_directory_exists(user_dir)
    screenshot_dir = os.path.join(
        user_dir, "screenshots"
    )  # Screenshots directory for the user
    ensure_directory_exists(screenshot_dir)
    return screenshot_dir


def setup_driver():
    """Setup the Chrome driver."""
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    chrome_options.add_argument(f"user-agent={user_agent}")
    return webdriver.Chrome(options=chrome_options)


def set_cookies(driver):
    """Set cookies from a saved file."""
    base_domain = "https://twitter.com"
    driver.get(base_domain)
    with open("cookies.json", "r") as file:
        cookies = json.load(file)
        for cookie in cookies:
            if "sameSite" in cookie:
                del cookie["sameSite"]
            driver.add_cookie(cookie)


def find_overlap(img1, img2):
    overlap_height = 0
    for y in range(img1.height):
        row_img1 = list(
            img1.crop((0, img1.height - y - 1, img1.width, img1.height - y)).getdata()
        )
        row_img2 = list(img2.crop((0, 0, img2.width, 1)).getdata())
        if row_img1 == row_img2:
            overlap_height = y + 1
            break  # Break the loop once the overlap is found
    print(f"Calculated overlap: {overlap_height} pixels")
    return overlap_height


def are_bottom_portions_same(img1, img2, height_to_compare=100):
    """Compare the bottom portions of two images."""
    bottom_img1 = img1.crop(
        (0, img1.height - height_to_compare, img1.width, img1.height)
    )
    bottom_img2 = img2.crop(
        (0, img2.height - height_to_compare, img2.width, img2.height)
    )
    return list(bottom_img1.getdata()) == list(bottom_img2.getdata())


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

    # Before saving, crop out the bottom blackspace
    cropped_image = crop_bottom_blackspace(stitched_image)

    print(
        f"Final stitched image dimensions (after cropping): {cropped_image.size}"
    )  # Debug print
    cropped_image.save(output_filename)


def is_blackspace_row(image, y, threshold=10):
    """Check if a row in an image is black or nearly black."""
    pixels = image.load()
    black_pixels_count = sum(
        1 for x in range(image.width) if sum(pixels[x, y]) / 3 < threshold
    )
    return (
        black_pixels_count > image.width * 0.95
    )  # Over 95% of the pixels are black or nearly black


def crop_bottom_blackspace(image):
    """Crops the bottom blackspace of an image."""
    for y in reversed(range(image.height)):
        if not is_blackspace_row(image, y):
            return image.crop((0, 0, image.width, y + 1))
    return image  # Return original image if no blackspace found


def capture_timeline_screenshots(driver, url, username):
    """Capture screenshots of the Twitter timeline and combine them."""

    def human_like_scrolling(driver):
        """Simulate human-like scrolling by scrolling in smaller chunks."""
        viewport_height = driver.execute_script("return window.innerHeight")
        scroll_increment = (
            viewport_height * 0.8
        )  # Scroll 80% of the viewport height for 20% overlap
        driver.execute_script(f"window.scrollBy(0, {scroll_increment});")
        time.sleep(random.uniform(0.2, 0.5))  # Short pauses between scrolls

    def hide_elements(driver, selectors):
        """Hide elements on the page using their CSS selectors."""
        for selector in selectors:
            try:
                element = driver.execute_script(
                    f"return document.querySelector('{selector}');"
                )
                if element:
                    driver.execute_script(
                        f"document.querySelector('{selector}').style.display = 'none';"
                    )
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

    problematic_selectors = [
        "#react-root > div > div > div.css-1dbjc4n.r-18u37iz.r-13qz1uu.r-417010 > main > div > div > div > div.css-1dbjc4n.r-kemksi.r-1kqtdi0.r-1ljd8xs.r-13l2t4g.r-1phboty.r-16y2uox.r-1jgb5lz.r-11wrixw.r-61z16t.r-1ye8kvj.r-13qz1uu.r-184en5c > div > div.css-1dbjc4n.r-aqfbo4.r-gtdqiz.r-1gn8etr.r-1g40b8q"
    ]
    hide_elements(driver, problematic_selectors)

    # input("Press Enter to continue...")

    # Identify the timeline element ONCE at the beginning
    timeline_element = driver.find_element(
        By.CSS_SELECTOR,
        "#react-root > div > div > div.css-1dbjc4n.r-18u37iz.r-13qz1uu.r-417010 > main > div > div > div > div.css-1dbjc4n.r-kemksi.r-1kqtdi0.r-1ljd8xs.r-13l2t4g.r-1phboty.r-16y2uox.r-1jgb5lz.r-11wrixw.r-61z16t.r-1ye8kvj.r-13qz1uu.r-184en5c",
    )
    timeline_location = timeline_element.location
    timeline_size = timeline_element.size
    timeline_actual_height = driver.execute_script(
        "return arguments[0].scrollHeight;", timeline_element
    )

    screenshot_dir = setup_directories(username)  # Setting up directories

    while True:
        screenshot_path = os.path.join(
            screenshot_dir, f"timeline_screenshot_{screenshot_num}.png"
        )
        capture_and_crop_screenshot(
            driver,
            screenshot_path,
            timeline_location["x"],
            timeline_location["y"],
            timeline_size["width"],
            timeline_actual_height,
        )

        # Check if the bottom portion of the current screenshot is the same as the previous one
        if last_screenshot:
            current_screenshot = Image.open(screenshot_path)
            if are_bottom_portions_same(current_screenshot, last_screenshot):
                # If the bottom portions match, we've reached the end
                os.remove(screenshot_path)  # Remove the redundant screenshot
                break
            last_screenshot = current_screenshot
        else:
            last_screenshot = Image.open(screenshot_path)

        screenshot_num += 1

        human_like_scrolling(driver)
        time.sleep(2)

    # Combine screenshots
    image_files = [
        os.path.join(screenshot_dir, f"timeline_screenshot_{i}.png")
        for i in range(1, screenshot_num)
    ]
    combined_image_path = os.path.join(screenshot_dir, "combined_timeline.png")
    combine_images(image_files, combined_image_path)

    print(f"Captured {screenshot_num - 1} screenshots.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Capture and stitch a user's Twitter timeline."
    )
    parser.add_argument(
        "-u", "--username", type=str, default="", help="Twitter username to capture."
    )
    args = parser.parse_args()

    base_url = "https://twitter.com/"
    target_url = base_url + args.username

    driver = setup_driver()
    set_cookies(driver)
    capture_timeline_screenshots(driver, target_url, args.username)
    driver.quit()
