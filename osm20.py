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

# - image zero point is the top-left corner of the image
#   https://realpython.com/image-processing-with-the-python-pillow-library/
# - to drag something left means that the new content is on the right
#   to drag it right results in content on the left
#   for up and down & down and up it's the very same


def setup_browser():
    """
    Set up the Selenium WebDriver.
    Chromium seems better for this task.
    """
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
    os.makedirs(base_dir, exist_ok=True)
    raw_dir = os.path.join(base_dir, "raw_screenshots")
    cropped_dir = os.path.join(base_dir, "cropped_images")
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(cropped_dir, exist_ok=True)
    return base_dir, raw_dir, cropped_dir


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
    The setup_browser() function is defined elsewhere and returns a configured WebDriver instance.
    """
    print("Setting up browser...")
    driver = setup_browser()

    # Open the map
    map_url = f"https://www.openstreetmap.org/relation/22259#map={zoom_level}/47.496930/19.050561"
    print("Opening map in browser...")
    driver.get(map_url)
    print("Content loaded...")
    return driver


def take_screenshot(driver, filename):
    """
    Take a screenshot of the current browser window and save it to a file.

    This function uses the Selenium WebDriver to capture a screenshot of the
    current state of the browser window and saves it to the specified file.

    Parameters:
    driver (selenium.webdriver.remote.webdriver.WebDriver): The Selenium WebDriver
        instance controlling the browser.
    filename (str): The path and name of the file where the screenshot will be saved.
        The file extension should typically be '.png'.

    Returns:
    None

    Side effects:
    - Saves a screenshot file to the specified location.
    - Prints a confirmation message to the console.
    """
    driver.save_screenshot(filename)
    print(f"Saved screenshot: {filename}")


def crop_image(filename, cropped_dir, dark):
    """
    Crop the darker UI elements from the screenshot and save the result.

    This function opens an image file, crops it to remove dark UI elements
    from the edges, and saves the cropped image to a specified directory.

    Parameters:
    filename (str): The path to the image file to be cropped.
    cropped_dir (str): The directory where the cropped image will be saved.
    dark (dict): A dictionary containing the pixel values for cropping.
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
        cropped_img = img.crop((dark["left"], dark["top"], width - dark["right"], height - dark["bottom"]))
        cropped_filename = os.path.join(cropped_dir, os.path.basename(filename))
        cropped_img.save(cropped_filename)
        width, height = cropped_img.size
        print(f"Cropped and saved image: {cropped_filename} area: {width}x{height}px")

    return width, height


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


def move_mouse_to_center_of_viewport(action, driver):
    """
    Move the mouse cursor to the center of the browser viewport.

    This function calculates the center coordinates of the viewport and moves
    the mouse cursor to that position. It's typically used before performing
    drag operations to ensure consistent starting positions.

    Parameters:
    action (ActionChains): The Selenium ActionChains object used for performing
                           mouse actions.
    driver (WebDriver): The Selenium WebDriver instance controlling the browser.

    Returns:
    tuple: A tuple containing four integers:
        - center_x (int): The x-coordinate of the viewport's center.
        - center_y (int): The y-coordinate of the viewport's center.
        - viewport_height (int): The height of the viewport in pixels.
        - viewport_width (int): The width of the viewport in pixels.
    """
    viewport_height, viewport_width = retrieve_viewport_size(driver)
    # Move mouse to the center of the viewport usually before dragging
    center_x = viewport_width // 2
    center_y = viewport_height // 2
    move_mouse_to(action, center_x, center_y)
    return center_x, center_y, viewport_height, viewport_width


def move_mouse_to(action, center_x, center_y):
    action.w3c_actions.pointer_action.move_to_location(center_x, center_y)


def pan_with_mouse(action, center_x, center_y, dx, dy, movement_pixels, viewport_height, viewport_width, pan_wait_seconds, direction_text):
    """
    Pan the map using mouse actions within the browser viewport.

    This function calculates the end position for a pan movement, performs the pan action
    using Selenium's ActionChains, and waits for the map to load after panning.

    Parameters:
        action (ActionChains): Selenium ActionChains object for performing mouse actions.
        center_x (int): X-coordinate of the center of the viewport.
        center_y (int): Y-coordinate of the center of the viewport.
        dx (int): Horizontal direction of movement (-1 for left, 1 for right, 0 for no horizontal movement).
        dy (int): Vertical direction of movement (-1 for up, 1 for down, 0 for no vertical movement).
        movement_pixels (int): Number of pixels to move in the specified direction.
        viewport_height (int): Height of the browser viewport in pixels.
        viewport_width (int): Width of the browser viewport in pixels.
        pan_wait_seconds (int): Number of seconds to wait after panning for the map to load.
        direction_text (str): Textual description of the panning direction for logging purposes.

    Side effects:
    - Prints debugging information about the panning action.
    - Performs mouse actions in the browser to pan the map.
    - Waits for a specified time after panning.
    """
    # Drag the map
    end_x = center_x + (dx * movement_pixels)
    end_y = center_y + (dy * movement_pixels)
    # Clamp end positions within the viewport
    end_x = max(0, min(viewport_width, end_x))
    end_y = max(0, min(viewport_height, end_y))
    # Prepare where to go
    move_mouse_x = end_x - center_x
    move_mouse_y = end_y - center_y
    print(f"Calculating next image ------------------------------------------------------------------------")
    print(
        f"For next vales for {direction_text} ({dx}, {dy}) direction mouse move x: {move_mouse_x}, y: {move_mouse_y}, end_x: {end_x}, end_y: {end_y}")
    # Drag with mouse button held down
    action.click_and_hold().perform()
    action.move_by_offset(move_mouse_x, move_mouse_y).release().perform()
    print(f"Patience while browser loads images, ", end="", flush=True)
    wait(pan_wait_seconds)  # seconds, Wait for the map to load


def retrieve_viewport_size(driver):
    viewport_width = driver.execute_script("return window.innerWidth;")
    viewport_height = driver.execute_script("return window.innerHeight;")
    return viewport_height, viewport_width


def fetch_map(cropped_dir, dark, driver, movement_pixels, raw_dir, steps, pan_wait_seconds):
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
    # loadtime for a dragged page in seconds to wait between map subparts' requests
    print(f"Walking through the map...")
    print("==========================")
    action = ActionChains(driver)
    seen_positions = set()
    directions = dict(up=(0, -1), right=(1, 0), down=(0, 1), left=(-1, 0))  # (dx, dy) directions:
    name_of_directions = {v: k for k, v in directions.items()}
    x, y = 0, 0

    # to keep the center in the middle, we move in the opposite directions half the distance of a step
    for _ in range(steps):
        dx, dy = directions['down']
        center_x, center_y, viewport_height, viewport_width = move_mouse_to_center_of_viewport(action, driver)
        direction_name = name_of_directions[(dx, dy)]
        pan_with_mouse(action, center_x, center_y, dx, dy, movement_pixels // 2, viewport_height, viewport_width, pan_wait_seconds, direction_name)
        dx, dy = directions['right']
        direction_name = name_of_directions[(dx, dy)]
        center_x, center_y, viewport_height, viewport_width = move_mouse_to_center_of_viewport(action, driver)
        pan_with_mouse(action, center_x, center_y, dx, dy, movement_pixels // 2, viewport_height, viewport_width, pan_wait_seconds, direction_name)


    all_steps = range(1, steps + 1)
    for step in all_steps:
        for dx, dy in directions.values():
            for sub_step in range(step):
                if (x, y) not in seen_positions:
                    # save screenshot of the current position of the map
                    print(f"In substep {sub_step} of step {steps + 1} of {all_steps} steps, taking screenshot for position ({x}, {y}) then cropping...")
                    screenshot_filename = os.path.join(raw_dir, f"screenshot_{x}_{y}.png")
                    take_screenshot(driver, screenshot_filename)
                    cropped_image_size = crop_image(screenshot_filename, cropped_dir, dark)
                else:
                    print(f"Skipping screenshot for position ({x}, {y}) as it has already been taken.")

                # Move mouse to the center of the viewport before dragging
                center_x, center_y, viewport_height, viewport_width = move_mouse_to_center_of_viewport(action, driver)

                # Pan with mouse and update positions cache
                direction_name = name_of_directions[(dx, dy)]
                pan_with_mouse(action, center_x, center_y, dx, dy, movement_pixels, viewport_height, viewport_width, pan_wait_seconds, direction_name)
                seen_positions.add((x, y))

                # Set next iteration's values
                x += dx
                y += dy


    return cropped_image_size


def assemble_big_map(base_dir, cropped_dir, movement_pixels, steps, zoom_level, cropped_image_size, title):
    """
    Assemble a large map from cropped images and save it to a file.

    This function serves as a wrapper for the image assembler function. It prepares
    the output filename and calls the detailed assembly function.

    Parameters:
    base_dir (str): The base directory where the assembled map will be saved.
    cropped_dir (str): The directory containing the cropped image files.
    movement_pixels (int): The number of pixels moved between each image capture.
    steps (int): The number of steps taken in each direction during image capture.
    zoom_level (int): The zoom level of the map used during capture.
    cropped_image_size (tuple): A tuple (width, height) representing the size of each cropped image.
    title (str): The title of the map, used in the output filename.

    Side effects:
    - Prints a status message to the console.
    - Calls the assemble_image_details function to create and save the assembled map.
    """
    print("Assembling the big map...")
    underscored_title = title.replace(" ", "_")
    now_text = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_base_filename = os.path.join(base_dir, f"map_{underscored_title}_{now_text}")
    assemble_image_details(
        cropped_dir, output_base_filename, movement_pixels, cropped_image_size, zoom_level, steps
    )


def assemble_image_details(
        cropped_dir, output_base_filename, movement_pixels, cropped_image_size, zoom_level, steps,
    ):
    """
    Assemble cropped images into a single large image using Pillow's paste function.

    This function collects cropped images from a specified directory, calculates their positions,
    and assembles them into a single large image. The assembled image is then saved to a file.

    Parameters:
    cropped_dir (str): The directory containing the cropped image files.
    output_base_filename (str): The base filename for the output assembled image.
    movement_pixels (int): The number of pixels moved between each image capture.
    cropped_image_size (tuple): A tuple (width, height) representing the size of each cropped image.
    zoom_level (int): The zoom level of the map used during capture.
    steps (int): The number of steps taken in each direction during image capture.

    Returns:
    None

    Side effects:
    - Prints progress information to the console.
    - Saves the assembled image to a file.
    - Prints the file size of the saved image.
    """
    images = []
    positions = []

    # Collect filenames and positions from the cropped directory
    print("Collect filenames and positions from the cropped directory")
    cropped_files = sorted(os.listdir(cropped_dir))
    print(f"Found {len(cropped_files)} images in the cropped directory.")
    for filename in cropped_files:
        if filename.endswith(".png"):
            filepath = os.path.join(cropped_dir, filename)
            try:
                parts = filename.replace(".png", "").split("_")
                x, y = int(parts[1]), int(parts[2])
                position = (x, y)
                images.append(filepath)
                positions.append(position)
            except ValueError:
                print(f"Skipping invalid filename format during assembly: {filename}")
                continue

    if not positions:
        print("No valid images found for assembly. Exiting.")
        return

    # size of the big picture, needs still refinement
    width, height = cropped_image_size
    assembled_image_size_x = width + (movement_pixels * steps * 2) + 6000
    assembled_image_size_y = height + (movement_pixels * steps * 2) + 6000

    # this will hold all the images
    print(f"creating empty assembled image: {assembled_image_size_x}x{assembled_image_size_y} pixel png.")
    assembled_image = Image.new('RGBA', (assembled_image_size_x, assembled_image_size_y))
    print("assembly image size in memory in bytes: ", sys.getsizeof(assembled_image.tobytes()))

    # the very middle point of the assembled image
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

        #          center     coordinates             cropped's center     against 'spiral' path displacement
        x_offset = center_x - (x * movement_pixels) - (width // 2)        # + ((steps // 4) * movement_pixels)
        y_offset = center_y - (y * movement_pixels) - (height // 2)         # - ((steps // 4) * movement_pixels)
        assembled_image.paste(image, (x_offset, y_offset))
        print(f"Image position: ({x},{y}) size {width}x{height}px pasted into assembled map.")

    # save the result
    print("___________________________________________")
    width, height = assembled_image.size
    output_filename = f"{output_base_filename}_steps{steps}_zoom{zoom_level}_{width}x{height}px.png"
    assembled_image.save(output_filename)
    print(f"Assembled map saved as {output_filename}")
    file_stats = os.stat(output_filename)
    print(f'File size is {round(file_stats.st_size / (1024 * 1024), 2)} MegaBytes')


def cleanup(driver, raw_dir, cropped_dir):
    """
    Clean up resources and temporary files after the map capture process.

    This function performs the following cleanup tasks:
    1. Closes the Selenium WebDriver.
    2. Removes all PNG files from the cropped images directory.
    3. Removes all PNG files from the raw screenshots directory.
    4. Attempts to remove the cropped and raw directories.

    Parameters:
    driver (selenium.webdriver.remote.webdriver.WebDriver): The Selenium WebDriver instance to be closed.
    raw_dir (str): Path to the directory containing raw screenshots.
    cropped_dir (str): Path to the directory containing cropped images.

    Side effects:
    - Closes the browser controlled by the WebDriver.
    - Deletes files and attempts to remove directories.
    - Prints status messages to the console.
    """
    print("Cleaning up...")
    driver.quit()
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
         print(f"Failed to remove sub directories {cropped_dir} and/or {raw_dir} since {repr(e)}")
    print("Process completed.")


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
    steps = 13  # number of "circles" we walk around the map centre
    zoom_level = 13  # Adjust map zoom level upto 19
    pan_wait_seconds = 5  # seconds, Wait for the map to load after each panning
    base_dir, raw_dir, cropped_dir = create_directories()
    dark_top, dark_bottom = 110, 110
    dark_left, dark_right = 400, 100
    dark = {'top': dark_top, 'bottom': dark_bottom, 'left': dark_left, 'right': dark_right}
    start_time = time.time()
    print(f"Movement is {movement_pixels}px, steps are {steps}, zoom level is {zoom_level}.")

    # workflow starts here
    driver = open_browser(zoom_level=zoom_level)
    cropped_image_size = fetch_map(cropped_dir, dark, driver, movement_pixels, raw_dir, steps, pan_wait_seconds)
    assemble_big_map(base_dir, cropped_dir, movement_pixels, steps, zoom_level, cropped_image_size, title)
    cleanup(driver, raw_dir, cropped_dir)

    # script running time
    print(f"Total execution time was: {((time.time() - start_time) / 60):.2f} minutes.")

if __name__ == "__main__":
    main()
