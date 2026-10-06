import os
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# Specify the default JSON data file, this can be overridden by a command-line argument
DATA_FILE = 'planets.json'  # Default file, change to use a different JSON file

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
        response = requests.get(url, timeout=300)  # 5-minute timeout for resolving page IDs
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
        url = f"https://en.wikipedia.org/w/api.php?action=parse&pageid={page_id}&prop=text&format=json"
    else:
        url = f"https://en.wikipedia.org/w/api.php?action=parse&page={title}&prop=text&format=json"
    
    try:
        response = requests.get(url, timeout=300)  # 5-minute timeout for fetching content
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data for {title} (page ID {page_id}): {e}")
        return None

# Function to organize content by headers and save as a JSON file
def save_content_as_json(title, page_content, folder_path):
    try:
        page_html = page_content['parse']['text']['*']
        soup = BeautifulSoup(page_html, 'html.parser')

        # Initialize content structure
        content = {}
        current_header = None

        # Loop through all elements in the HTML, extract headers and paragraphs
        for element in soup.find_all(True):  # Find all HTML tags
            # Look for headers (h2, h3, etc.)
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                current_header = element.get_text().strip()
                print(f"Found header: {current_header}")  # Debugging
                if current_header:
                    content[current_header] = []
            # Capture paragraphs and any text under the current header
            elif current_header and element.name == 'p' and element.get_text().strip():
                print(f"Adding paragraph to {current_header}: {element.get_text().strip()}")  # Debugging
                content[current_header].append(element.get_text().strip())

        # Check if content is empty (debugging)
        if not content:
            print(f"WARNING: No content extracted for {title}")

        # Prepare metadata and structure for the JSON file
        page_id = page_content['parse']['pageid']
        json_data = {
            "title": title,
            "page_id": page_id,
            "content": content,
            "metadata": {
                "captured_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "source": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
            }
        }

        # Save content as a JSON file
        json_file_path = os.path.join(folder_path, f"{title.replace(' ', '_')}.json")
        with open(json_file_path, 'w') as json_file:
            json.dump(json_data, json_file, indent=4)

        print(f"Content saved to JSON: {json_file_path}")
    
    except Exception as e:
        print(f"Error parsing or saving content for {title}: {e}")

# Function to take full-page screenshots for each page, organized by date
def capture_screenshots(playwright, title, page_data, root_folder):
    # Create subfolder for each title under the root folder
    topic_folder = os.path.join(root_folder, title.replace(' ', '_'))
    os.makedirs(topic_folder, exist_ok=True)  # Create the topic folder if it doesn't exist

    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Fetch the URL of the Wikipedia page
    page_url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
    page.goto(page_url)

    # Sanitize the title for use in filenames
    screenshot_filename = os.path.join(topic_folder, f"{title.replace(' ', '_')}.png")

    try:
        # Take the screenshot with increased timeout (300 seconds = 5 minutes)
        page.screenshot(path=screenshot_filename, full_page=True, timeout=300000)

        print(f"Full-page screenshot saved: {screenshot_filename}")

    except Exception as e:
        print(f"Error capturing screenshot for {title}: {e}")
    
    page.close()
    browser.close()

# Main function
def main(data_file=DATA_FILE):
    # Read pages from the JSON file
    pages = load_pages_from_json(data_file)

    # Get current date and generate folder name based on JSON file name and date
    current_date = datetime.now().strftime('%Y-%m-%d')
    root_folder_name = f"screenshots-{os.path.splitext(os.path.basename(data_file))[0]}-{current_date}"
    os.makedirs(root_folder_name, exist_ok=True)  # Create root folder for today's screenshots

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

                if page_content:
                    # Capture screenshot and metadata
                    capture_screenshots(playwright, title, page_content, root_folder_name)

                    # Save content to JSON
                    save_content_as_json(title, page_content, root_folder_name)

# Run the script
if __name__ == "__main__":
    main()