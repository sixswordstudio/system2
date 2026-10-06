import os
import json
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

# Specify the default JSON data file, this can be overridden by a command-line argument
DATA_FILE = 'pages.json'  # Change this to use different JSON files

# Path to the metadata JSON file where screenshot metadata will be stored
METADATA_FILE = 'metadata.json'

# Function to read page titles and IDs from a JSON file
def load_pages_from_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        pages = data.get('pages', [])
    return pages

# Function to resolve the page ID based on title, if it's missing
def resolve_page_id(title):
    url = f"https://en.wikipedia.org/w/api.php?action=query&titles={title}&format=json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        pages = data.get('query', {}).get('pages', {})
        page_id = list(pages.keys())[0]  # Get the first page ID from the result
        if page_id == '-1':
            print(f"Page '{title}' not found.")
            return None
        return page_id
    except requests.RequestException as e:
        print(f"Error resolving page ID for {title}: {e}")
        return None

# Function to fetch page content by page ID or title
def fetch_page_by_id_or_title(title, page_id=None):
    if page_id:
        url = f"https://en.wikipedia.org/w/api.php?action=query&pageids={page_id}&prop=info|extracts&exintro&format=json"
    else:
        url = f"https://en.wikipedia.org/w/api.php?action=query&titles={title}&prop=info|extracts&exintro&format=json"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data for {title} (page ID {page_id}): {e}")
        return None

# Function to take full-page screenshots for each page, organized by date
def capture_screenshots(playwright, title, page_data, root_folder):
    # Create subfolder for each title under the root folder
    topic_folder = os.path.join(root_folder, title.replace(' ', '_'))
    os.makedirs(topic_folder, exist_ok=True)  # Create the topic folder if it doesn't exist

    # Prepare metadata for the screenshot
    topic_metadata = []

    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Fetch the URL of the Wikipedia page
    page_url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
    page.goto(page_url)

    # Sanitize the title for use in filenames
    sanitized_title = title.replace(" ", "_").replace("/", "_")

    # Generate the screenshot filename
    screenshot_filename = os.path.join(topic_folder, f"{sanitized_title}.png")

    try:
        # Take the screenshot with increased timeout (60 seconds)
        page.screenshot(path=screenshot_filename, full_page=True, timeout=60000)

        # Add metadata for the screenshot
        metadata_entry = {
            "title": title,
            "url": page_url,
            "screenshot_filename": screenshot_filename,
            "captured_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "folder": root_folder
        }
        topic_metadata.append(metadata_entry)

        print(f"Full-page screenshot saved: {screenshot_filename}")

    except Exception as e:
        print(f"Error capturing screenshot for {title}: {e}")
    
    page.close()
    browser.close()

    return topic_metadata

# Function to load existing metadata from the metadata file, if it exists and is valid
def load_existing_metadata():
    if os.path.exists(METADATA_FILE):
        # Check if the file is empty
        if os.path.getsize(METADATA_FILE) > 0:
            with open(METADATA_FILE, 'r') as file:
                try:
                    return json.load(file)
                except json.JSONDecodeError:
                    print("Warning: metadata.json is corrupted or empty. Starting fresh.")
                    return []
        else:
            print("Warning: metadata.json is empty. Starting fresh.")
            return []
    return []

# Function to save metadata to the JSON file
def save_metadata(new_metadata):
    # Load the existing metadata
    existing_metadata = load_existing_metadata()

    # Append the new metadata
    existing_metadata.extend(new_metadata)

    # Save the updated metadata back to the file
    with open(METADATA_FILE, 'w') as file:
        json.dump(existing_metadata, file, indent=4)

    print(f"Metadata saved to {METADATA_FILE}")

# Main function
def main(data_file=DATA_FILE):
    # Read pages from the JSON file
    pages = load_pages_from_json(data_file)

    # Get current date and generate folder name based on JSON file name and date
    current_date = datetime.now().strftime('%Y-%m-%d')
    root_folder_name = f"screenshots-{os.path.splitext(os.path.basename(data_file))[0]}-{current_date}"
    os.makedirs(root_folder_name, exist_ok=True)  # Create root folder for today's screenshots

    # Prepare a list to hold all metadata from this run
    all_metadata = []

    with sync_playwright() as playwright:
        for page_data in pages:
            title = page_data['title']
            page_id = page_data.get('page_id')

            # Resolve page ID if not provided
            if not page_id:
                print(f"Resolving page ID for: {title}")
                page_id = resolve_page_id(title)
                if page_id:
                    page_data['page_id'] = page_id  # Update the page_id in case you want to save it later

            # Fetch page metadata and content
            if page_id:
                print(f"Fetching content for page: {title}")
                page_content = fetch_page_by_id_or_title(title, page_id)

                # Capture screenshot and metadata
                if page_content:
                    topic_metadata = capture_screenshots(playwright, title, page_content, root_folder_name)
                    all_metadata.extend(topic_metadata)

    # Save all metadata to the JSON file
    save_metadata(all_metadata)

# Run the script
if __name__ == "__main__":
    main()