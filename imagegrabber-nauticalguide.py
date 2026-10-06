import asyncio
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import os
from urllib.parse import urlparse
import hashlib

# Function to fetch and parse the sitemap
def fetch_sitemap(sitemap_url):
    response = requests.get(sitemap_url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'xml')
        urls = [loc.get_text() for loc in soup.find_all('loc')]
        return urls
    else:
        print(f"Failed to fetch sitemap. Status code: {response.status_code}")
        return []

# Function to filter URLs that contain '/docs/'
def filter_docs_urls(urls):
    return [url for url in urls if '/docs/' in url]

# Function to save images from relative URLs, with duplicate check based on hash
def save_image_from_url(image_url, base_url, output_folder, article_url, sequence_num, saved_hashes):
    # Construct the full URL for the relative image path
    full_image_url = base_url + image_url
    
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Parse the article URL to create a clean filename base
    parsed_url = urlparse(article_url)
    article_name = parsed_url.path.strip("/").replace("/", "-")  # Replace '/' with '-' for safe filenames

    # Generate a unique image filename with sequence number
    image_extension = os.path.splitext(image_url)[1]  # Get the file extension (e.g., .png, .jpg)
    image_name = f"{article_name}-{sequence_num}{image_extension}"

    try:
        img_data = requests.get(full_image_url).content
        
        # Compute a hash of the image data to avoid duplicates
        img_hash = hashlib.md5(img_data).hexdigest()
        if img_hash in saved_hashes:
            print(f"Skipped duplicate: {full_image_url}")
            return
        else:
            saved_hashes.add(img_hash)
        
        # Save the image
        with open(os.path.join(output_folder, image_name), 'wb') as handler:
            handler.write(img_data)
        print(f"Saved: {full_image_url} as {image_name}")
    except Exception as e:
        print(f"Failed to save {full_image_url}: {e}")

# Retry mechanism for network errors
async def goto_with_retry(page, url, retries=3):
    for attempt in range(retries):
        try:
            await page.goto(url)
            return True
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt + 1 == retries:
                print(f"Failed to load {url} after {retries} attempts.")
                return False
            await asyncio.sleep(2)  # Wait before retrying

# Function to extract images using Playwright
async def extract_images_from_url(page, url, base_url, output_folder, saved_hashes):
    if not await goto_with_retry(page, url):
        return  # Skip this URL if it fails after retries

    # Extract the page content
    page_content = await page.content()
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(page_content, 'html.parser')

    # Parse the URL to capture the article path
    parsed_url = urlparse(url)
    path_segments = parsed_url.path.strip("/").split("/")

    # The article will always be the last segment
    article = path_segments[-1] if len(path_segments) > 1 else None

    sequence_num = 1  # Initialize sequence number for naming the images

    # Extract and save images (only relative URLs, skip base64)
    for img in soup.find_all('img'):
        img_src = img.get('src')
        if img_src and not img_src.startswith("data:image"):  # Skip base64 images
            save_image_from_url(img_src, base_url, output_folder, url, sequence_num, saved_hashes)
            sequence_num += 1

# Function to scrape URLs and save images
async def scrape_docs_urls(docs_urls, base_url, output_folder):
    saved_hashes = set()  # To store hashes of saved images and avoid duplicates
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Loop through each /docs/ URL and extract images
        for url in docs_urls:
            print(f"Scraping URL: {url}")
            await extract_images_from_url(page, url, base_url, output_folder, saved_hashes)
        
        await browser.close()

# Main function to execute the script
def main():
    # Sitemap URL
    sitemap_url = "https://guide.nauticalcommerce.com/sitemap.xml"  # Replace with the actual sitemap URL
    
    # Fetch all URLs from the sitemap
    all_urls = fetch_sitemap(sitemap_url)
    
    # Filter URLs that contain '/docs/'
    docs_urls = filter_docs_urls(all_urls)
    
    # Base URL of the website
    base_url = "https://guide.nauticalcommerce.com"  # Replace with the base URL of the website
    
    # Output folder to save the images
    output_folder = "nauticalguide-images"
    
    # Scrape the filtered URLs and save images
    asyncio.run(scrape_docs_urls(docs_urls, base_url, output_folder))

if __name__ == "__main__":
    main()