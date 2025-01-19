"""
This is a Python program designed to capture, process, and assemble large map images
from OpenStreetMap. Here's a summary of its main components and functionality:

1. Setup and Initialization:
   - Imports necessary libraries (Selenium, Pillow, etc.)
   - Defines functions for setting up the browser (use Chrome, not Firefox)
   - Creates directories for storing raw and processed images

2. Image Capture:
   - Opens OpenStreetMap in a browser at a specified zoom level
   - Navigates the map in a spiral pattern, taking screenshots at each position
   - Saves raw screenshots and crops them to remove UI elements

3. Image Processing:
   - Crops raw screenshots to remove dark UI elements
   - Saves cropped images with position information in the filename

4. Image Assembly:
   - Collects all cropped images from the directory
   - Calculates the size of the final assembled image
   - Places each cropped image in its correct position on a large canvas
   - Saves the final assembled map as a PNG file

5. Utility Functions:
   - Implements waiting mechanisms with visual feedback
   - Provides cleanup functionality to remove temporary files and close the browser

6. Main Execution:
   - Sets parameters like movement distance, number of steps, zoom level, etc.
   - Executes the entire process: browser setup, image capture, processing, and assembly
   - Handles the overall workflow and calls other functions as needed

The script is designed to create high-resolution, large-scale map images by stitching together multiple screenshots.
It's particularly useful for capturing detailed maps of specific areas that might not be easily downloadable
as a single image from OpenStreetMap.
"""

import os
import sys
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from PIL import Image

# image zero point is the top-left corner of the image
# to drag something left means that the new content is on the right
# https://realpython.com/image-processing-with-the-python-pillow-library/


def setup_browser():
    """Set up the Selenium WebDriver. Chromium seems better for this task."""
    # return selenium_firefox()
    return selenium_chromium()


def selenium_chromium():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver


def selenium_firefox():
    options = webdriver.FirefoxOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Firefox(options=options)
    driver.maximize_window()
    return driver


def create_directories():
    """
    Create necessary directories for storing screenshots and outputs.

    This function creates a base directory with a timestamp and two subdirectories
    within it: one for raw screenshots and another for cropped images. The
    directories are created with unique names based on the current timestamp to
    avoid overwriting previous outputs.

    Returns:
    tuple: A tuple containing three strings:
        - base_dir (str): Path to the base directory for all outputs.
        - raw_dir (str): Path to the directory for storing raw screenshots.
        - cropped_dir (str): Path to the directory for storing cropped images.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_dir = f"map_output_{timestamp}"
    # base_dir = "map_output_20250118_235849"
    os.makedirs(base_dir, exist_ok=True)
    raw_dir = os.path.join(base_dir, "raw_screenshots")
    cropped_dir = os.path.join(base_dir, "cropped_images")
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(cropped_dir, exist_ok=True)
    return base_dir, raw_dir, cropped_dir


def take_screenshot(driver, filename):
    """Take a screenshot and save it to the specified filename."""
    driver.save_screenshot(filename)
    print(f"Saved screenshot: {filename}")


def crop_image(filename, cropped_dir, black):
    """
    Crop the darker UI elements from the screenshot and save the result.

    This function opens an image file, crops it to remove dark UI elements
    from the edges, and saves the cropped image to a specified directory.

    Parameters:
    filename (str): The path to the image file to be cropped.
    cropped_dir (str): The directory where the cropped image will be saved.
    black (dict): A dictionary containing the pixel values for cropping.
                  Expected keys are 'left', 'top', 'right', and 'bottom',
                  representing the number of pixels to crop from each edge.

    Returns:
    tuple: A tuple containing two integers (width, height) representing
           the dimensions of the cropped image in pixels.

    The function prints a message with the saved filename and dimensions
    of the cropped image.
    """
    with Image.open(filename) as img:
        width, height = img.size

        # Assuming arbitrary dark parts are 100 pixels from each edge
        cropped_img = img.crop((black["left"], black["top"], width - black["right"], height - black["bottom"]))
        cropped_filename = os.path.join(cropped_dir, os.path.basename(filename))
        cropped_img.save(cropped_filename)
        width, height = cropped_img.size
        print(f"Cropped and saved image: {cropped_filename} area: {width}x{height}px")

    return width, height


def assemble_image_details(
        cropped_dir, output_base_filename, movement_pixels, black, cropped_image_size, zoom_level, steps,
    ):
    """
    Assemble cropped images into a single large image using Pillow's paste function.

    This function collects cropped images from a specified directory, calculates their positions,
    and assembles them into a single large image. The assembled image is then saved to a file.

    Parameters:
    cropped_dir (str): The directory containing the cropped image files.
    output_base_filename (str): The base filename for the output assembled image.
    movement_pixels (int): The number of pixels moved between each image capture.
    black (dict): A dictionary containing pixel values for cropping (not used in this function).
    cropped_image_size (tuple): A tuple (width, height) representing the size of each cropped image.
    number_of_steps (int): The number of steps taken in each direction during image capture.

    Returns:
    None

    Side effects:
    - Prints progress information to the console.
    - Saves the assembled image to a file.
    - Prints the file size of the saved image.
    """
    images = []
    positions = []

    # Collect filenames and positions from the overlap directory
    print("Collect filenames and positions from the cropped directory")
    cropped_files = sorted(os.listdir(cropped_dir))
    print(f"Found {len(cropped_files)} images in the cropped directory.")
    for filename in cropped_files:
        if filename.endswith(".png"):
            filepath = os.path.join(cropped_dir, filename)
            try:
                parts = filename.replace(".png", "").split("_")
                x, y = int(parts[2]), int(parts[3])
                position = (x, y)
                # images.append(Image.open(filepath))
                images.append(filepath)
                positions.append(position)
                # print(f"Found for assembly: {filename} at {position}")
            except ValueError:
                print(f"Skipping invalid filename format during assembly: {filename}")
                continue

    if not positions:
        print("No valid images found for assembly. Exiting.")
        return

    # assembled_image_size_x, assembled_image_size_y = 0, 0
    # assembled_image_size_x += movement_pixels * (number_of_steps ** 2) + 16000  # the last constant is just a buffer, will see if we need it
    # assembled_image_size_y += movement_pixels * (number_of_steps ** 2) + 16000  # the last constant is just a buffer, will see if we need it
    width, height = cropped_image_size
    assembled_image_size_x = width + (movement_pixels * steps * 2)
    assembled_image_size_y = height + (movement_pixels * steps * 2)

    # this is hypothetical, overlaps are calculated redudant this way
    print(f"creating empty assembled image: {assembled_image_size_x}x{assembled_image_size_y} pixel png.")
    assembled_image = Image.new('RGBA', (assembled_image_size_x, assembled_image_size_y))
    print("assembly image size in memory in bytes: ", sys.getsizeof(assembled_image.tobytes()))

    center_x = assembled_image_size_x // 2
    center_y = assembled_image_size_y // 2
    x_offset = center_x
    y_offset = center_y

    # process cropped images
    i = 0
    for img, pos in zip(images, positions):
        print("......................................")
        print(f"assembly at pos {pos} with offset: x:{x_offset} y:{y_offset} on {img}")
        image = Image.open(img)
        width, height = image.size
        x, y = int(pos[0]), int(pos[1])
        prev_offset_x = x_offset
        prev_offset_y = y_offset
        x_offset = center_x - (x * movement_pixels) - (height // 2)
        y_offset = center_y - (y * movement_pixels) - (width // 2)
        # print(f"prev offset: x:{prev_offset_x} y:{prev_offset_y}")
        # print(f"curr offset: x:{x_offset} y:{y_offset}")
        # print(f"difference:  x:{x_offset - prev_offset_x}, y:{y_offset - prev_offset_y}")
        assembled_image.paste(image, (x_offset, y_offset))
        print(f"Image pozition: ({x},{y}) size {width}x{height}px pasted into assembled map.")
        # partial results for debug:
        i += 1
        # output_filename = f"{output_base_filename}_#{i}__{x}_{y}.png"
        # print(f"Start saving assembled map as file: {output_filename}")
        # assembled_image.save(output_filename)

    print("___________________________________________")
    width, height = assembled_image.size
    output_filename = f"{output_base_filename}_steps{steps}_zoom{zoom_level}_{width}x{height}px.png"
    assembled_image.save(output_filename)
    print(f"Assembled map saved as {output_filename}")
    file_stats = os.stat(output_filename)
    print(f'File Size is {round(file_stats.st_size / (1024 * 1024), 2)} MegaBytes')


def cleanup(driver,  raw_dir, cropped_dir):
    print("Cleaning up...")
    driver.quit()
    os.listdir(cropped_dir)
    for filename in os.listdir(cropped_dir):
        if filename.endswith(".png"):
            os.remove(os.path.join(cropped_dir, filename))
    for filename in os.listdir(raw_dir):
        if filename.endswith(".png"):
            os.remove(os.path.join(raw_dir, filename))
    try:
        os.rmdir(cropped_dir)
        os.rmdir(raw_dir)
    except OSError as e:
         print(f"Failed to remove sub directories: {repr(e)}")
    print("Process completed.")


def assemble_big_map(base_dir, cropped_dir, dark, movement_pixels, steps, zoom_level, cropped_image_size, title):
    """Just a wrapper for the image assembler function. No reason why, it just happened."""
    print("Assembling the big map...")
    underscored_title = title.replace(" ", "_")
    output_base_filename = os.path.join(base_dir, f"map_{underscored_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    assemble_image_details(
        cropped_dir, output_base_filename, movement_pixels, dark, cropped_image_size, zoom_level,
        steps
    )


def open_browser(zoom_level=17):
    """
    Initialize and open a browser with OpenStreetMap at a specified zoom level.

    This function sets up a browser using Selenium WebDriver, navigates to OpenStreetMap
    with a predefined location (Budapest, Hungary), and sets the map to the specified zoom level.

    Parameters:
    zoom_level (int, optional): The zoom level for the map. Defaults to 17.
                                Higher values zoom in closer, lower values zoom out.

    Returns:
    WebDriver: A Selenium WebDriver instance with the map loaded and ready for interaction.

    Note:
    The function assumes that the setup_browser() function is defined elsewhere
    and returns a configured WebDriver instance.
    """
    print("Setting up browser...")
    driver = setup_browser()

    # Open the map
    map_url = f"https://www.openstreetmap.org/relation/22259#map={zoom_level}/47.496930/19.050561"
    print("Opening map in browser...")
    driver.get(map_url)
    print("Content loaded...")
    return driver

def wait(seconds):
    """
    Pause execution for a specified number of seconds while displaying a visual progress indicator.

    This function prints a waiting message followed by a series of dots, one for each second of the wait time.
    It provides a visual indication of the passage of time during the wait period.

    Parameters:
    seconds (int): The number of seconds to wait.

    Side effects:
    Prints a waiting message and a series of dots to the console, with one dot printed each second.
    """
    print(f"waiting {seconds} seconds.", end="", flush=True)
    for _ in range(seconds):
        print(".", end="", flush=True)
        time.sleep(1)
    print()

def fetch_map(cropped_dir, dark, driver, movement_pixels, raw_dir, steps, scroll_wait_seconds=6):
    """
    Capture screenshots of a map by navigating through it in a spiral pattern using mouse dragging.

    This function moves through the map, takes screenshots at each position, crops them,
    and saves both raw and cropped versions. It uses Selenium WebDriver to control the browser.

    Parameters:
    cropped_dir (str): Directory path to save cropped screenshots.
    dark (dict): Dictionary containing pixel values for cropping dark UI elements.
    driver (WebDriver): Selenium WebDriver instance controlling the browser.
    movement_pixels (int): Number of pixels to move in each direction during navigation.
    raw_dir (str): Directory path to save raw screenshots.
    steps (int): Number of "circles" to walk around the map center.
    scroll_wait_seconds (int, optional): Time to wait for the map to load after each scroll. Defaults to 6.

    Returns:
    tuple: Dimensions (width, height) of the last cropped image.

    The function performs the following steps:
    1. Initializes variables for navigation and viewport dimensions.
    2. Iterates through the specified number of steps in a spiral pattern.
    3. At each position, takes a screenshot, saves it, and crops it.
    4. Moves the map view using mouse drag actions.
    5. Waits for the specified time after each move to allow the map to load.
    """
    # loadtime for a draged page in seconds to wait between map subparts requests
    sleep_time = scroll_wait_seconds
    print(f"Walking through the map...")
    print( "==========================")
    action = ActionChains(driver)
    directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # (dx, dy) directions: up, right, down, left
    x, y = 0, 0
    viewport_width = driver.execute_script("return window.innerWidth;")
    viewport_height = driver.execute_script("return window.innerHeight;")
    # Move mouse to the center of the viewport before dragging
    center_x = viewport_width // 2
    center_y = viewport_height // 2
    action.w3c_actions.pointer_action.move_to_location(center_x, center_y)
    i = 0
    all_steps = range(1, steps + 1)
    for step in all_steps:
        for dx, dy in directions:
            for sub_step in range(step):
                # save screenshot of the current position of the map
                print(f"In substep {sub_step} of step {step} of {all_steps} steps taking screenshot #{i} for position ({x}, {y}) then croping...")
                screenshot_filename = os.path.join(raw_dir, f"screenshot_#{i}_{x}_{y}.png")
                take_screenshot(driver, screenshot_filename)
                cropped_image_size = crop_image(screenshot_filename, cropped_dir, dark)

                # Move mouse to the center of the viewport before dragging
                viewport_width = driver.execute_script("return window.innerWidth;")
                viewport_height = driver.execute_script("return window.innerHeight;")
                center_x = viewport_width // 2
                center_y = viewport_height // 2
                action.w3c_actions.pointer_action.move_to_location(center_x, center_y)

                # Drag the map
                end_x = center_x + (dx * movement_pixels)
                end_y = center_y + (dy * movement_pixels)

                # Clamp end positions within the viewport
                end_x = max(0, min(viewport_width, end_x))
                end_y = max(0, min(viewport_height, end_y))

                move_mouse_x = end_x - center_x
                move_mouse_y = end_y - center_y
                print(f"Calculating next image --------------------------------------------------------------")
                print(f"For next vales with ({dx}, {dy}) direction mouse move x: {move_mouse_x}, y: {move_mouse_y}, end_x: {end_x}, end_y: {end_y}")

                # drag with mouse button held down
                action.click_and_hold().perform()
                action.move_by_offset(move_mouse_x, move_mouse_y).release().perform()

                # set next iteration's values
                x += dx
                y += dy
                i += 1
                print(f"Patience while browser loads images, ", end="", flush=True)
                wait(sleep_time)  # seconds, Wait for the map to load

    return cropped_image_size


def main():
    """
    Main function to execute the entire process of capturing, processing, and assembling map screenshots.

    This function sets up the necessary parameters, initializes the browser, captures map screenshots,
    processes them, and finally assembles them into a large map image.

    The function performs the following steps:
    1. Sets up parameters for map navigation and image processing.
    2. Creates necessary directories for storing raw and processed images.
    3. Opens a browser and navigates to the map.
    4. Captures screenshots of the map, moving in a spiral pattern.
    5. Processes and crops the captured screenshots.
    6. Assembles the cropped images into a large map.
    7. Cleans up resources.
    """
    title = "Pest Megye"  # Title for the assembled map image
    movement_pixels = 800  # Adjust drag distance of mouse
    steps = 30  # number of "circles" we walk around the map centre
    zoom_level = 15  # Adjust map zoom level upto 19
    scroll_wait_seconds = 6  # seconds, Wait for the map to load after each scroll
    base_dir, raw_dir, cropped_dir = create_directories()
    dark_top, dark_bottom = 110, 110
    dark_left, dark_right = 400, 400
    dark = {'top': dark_top, 'bottom': dark_bottom, 'left': dark_left, 'right': dark_right}
    print(f"Movement is {movement_pixels}, steps are {steps}, zoom level is {zoom_level}.")

    # workflow starts here
    driver = open_browser(zoom_level=zoom_level)
    cropped_image_size = fetch_map(cropped_dir, dark, driver, movement_pixels, raw_dir, steps, scroll_wait_seconds)
    assemble_big_map(base_dir, cropped_dir, dark, movement_pixels, steps, zoom_level, cropped_image_size, title)
    cleanup(driver, raw_dir, cropped_dir)

if __name__ == "__main__":
    main()
