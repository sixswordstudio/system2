import asyncio
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import json
from urllib.parse import urlparse

# Function to fetch and parse the sitemap
def fetch_sitemap(sitemap_url):
    response = requests.get(sitemap_url)
    
    if response.status_code == 200:
        # Use the correct XML parser
        soup = BeautifulSoup(response.content, 'xml')
        urls = [loc.get_text() for loc in soup.find_all('loc')]
        return urls
    else:
        print(f"Failed to fetch sitemap. Status code: {response.status_code}")
        return []

# Function to filter URLs that contain '/docs/'
def filter_docs_urls(urls):
    return [url for url in urls if '/docs/' in url]

# Function to extract headers, paragraphs, images, and metadata using Playwright
async def extract_content_from_url(page, url):
    await page.goto(url)
    await page.wait_for_load_state('networkidle')  # Wait for the page to fully load
    
    # Extract the page content
    page_content = await page.content()
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(page_content, 'html.parser')

    # Parse the URL to capture the hierarchy
    parsed_url = urlparse(url)
    path_segments = parsed_url.path.strip("/").split("/")

    # Dynamically assign hierarchy based on the URL segments
    hierarchy = {
        'knowledge_base': path_segments[0] if len(path_segments) > 0 else None,
        'category': path_segments[1] if len(path_segments) > 1 else None,
        'section': path_segments[2] if len(path_segments) > 2 else None,
        'subsection': path_segments[3] if len(path_segments) > 3 else None,
        'article': path_segments[4] if len(path_segments) > 4 else None,
    }

    # Prepare metadata and content structure
    content_data = {
        'url': url,
        'title': soup.title.string.strip() if soup.title else 'No Title',
        'hierarchy': hierarchy,
        'headers': [],
        'paragraphs': [],
        'images': []
    }

    # Extract headers and paragraphs
    for header in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        content_data['headers'].append(header.get_text(strip=True))
    
    for paragraph in soup.find_all('p'):
        content_data['paragraphs'].append(paragraph.get_text(strip=True))

    # Extract images and their links
    for img in soup.find_all('img'):
        img_src = img.get('src')
        if img_src:
            content_data['images'].append(img_src)
    
    return content_data

# Function to scrape URLs and save content to a JSON file
async def scrape_docs_urls(docs_urls, output_json):
    extracted_content = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Loop through each /docs/ URL and extract content
        for url in docs_urls:
            print(f"Scraping URL: {url}")
            content = await extract_content_from_url(page, url)
            if content:
                extracted_content.append(content)
        
        await browser.close()
    
    # Save the extracted content to a JSON file
    with open(output_json, 'w') as json_file:
        json.dump(extracted_content, json_file, indent=4)

    print(f"Extracted content saved to {output_json}")

# Main function to execute the script
def main():
    # Sitemap URL
    sitemap_url = "https://guide.nauticalcommerce.com/sitemap.xml"  # Replace with the actual sitemap URL
    
    # Fetch all URLs from the sitemap
    all_urls = fetch_sitemap(sitemap_url)
    
    # Filter URLs that contain '/docs/'
    docs_urls = filter_docs_urls(all_urls)
    
    # Output JSON file
    output_json = "extracted_docs_content.json"
    
    # Scrape the filtered URLs and save content to JSON
    asyncio.run(scrape_docs_urls(docs_urls, output_json))

if __name__ == "__main__":
    main()