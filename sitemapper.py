# Plug an XML sitemap URL into the first line of code. 
# Playwright will take a screenshot of every URL in the sitemap and save to the specified folder. 
import os
import re
import asyncio
import requests
from xml.etree import ElementTree as ET
from playwright.async_api import async_playwright
from tqdm import tqdm
from asyncio import Semaphore

# Correct URL of the website's sitemap
sitemap_url = 'https://guide.nauticalcommerce.com/sitemap.xml'

# Directory where screenshots will be saved
screenshot_directory = "/Users/amypark/DifferSnapperDev/nauticalcommerce-docs-screenshots"

# Create the directory if it doesn't exist
if not os.path.exists(screenshot_directory):
    os.makedirs(screenshot_directory)

# Function to fetch and parse the sitemap
def get_urls_from_sitemap(sitemap_url):
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()  # Raise an exception for any HTTP errors
        
        # Parse the XML content
        sitemap = ET.fromstring(response.content)
        namespaces = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        # Extract all URLs from the sitemap
        urls = [url.find('sitemap:loc', namespaces).text for url in sitemap.findall('sitemap:url', namespaces)]
        return urls
    
    except requests.exceptions.RequestException as e:
        tqdm.write(f"Error fetching sitemap: {e}")
        return []

# Function to generate filenames in the format "1-subdomain-page.png"
def create_filename_from_url(url, index):
    # Extract the subdomain or page path for easier identification
    clean_url = re.sub(r'[^A-Za-z0-9]', '-', url)  # Replace non-alphanumeric characters with dashes
    
    # Limit the file name to first few words after domain for clarity
    url_parts = url.split('/')
    domain_part = url_parts[2]  # domain part (e.g., www.nauticalcommerce.com)
    path_part = '-'.join(url_parts[3:5]) if len(url_parts) > 3 else "home"  # first two parts of the path or 'home'

    # Format the filename as "index-domain-part-path-part.png"
    filename = f"{index+1}-{domain_part}-{path_part}.png"
    return os.path.join(screenshot_directory, filename)

# Function to accept cookies on every page
async def accept_cookies(page):
    try:
        # Try to click the cookie banner if it exists
        await page.wait_for_selector('body > div.page-wrapper > div.set-all-components-to-display-none-and-use-this-div-to-create-a-symbol > div.fs-cc-banner_component > div.fs-cc-banner_container > div.fs-cc-banner_buttons-wrapper > a:nth-child(3)', timeout=5000)
        await page.click('body > div.page-wrapper > div.set-all-components-to-display-none-and-use-this-div-to-create-a-symbol > div.fs-cc-banner_component > div.fs-cc-banner_container > div.fs-cc-banner_buttons-wrapper > a:nth-child(3)')
        tqdm.write("Cookies accepted")
    except Exception as e:
        tqdm.write(f"No cookies to accept on this page or an error occurred: {e}")

# Function to ensure Embedly iframe thumbnails are fully loaded
async def ensure_embedly_thumbnails(page):
    try:
        # Find all iframes containing 'embedly' in the src attribute
        embedly_iframes = await page.query_selector_all('iframe[src*="embedly"]')

        # If any embedly iframes exist, wait for them to load their content
        for iframe in embedly_iframes:
            # Scroll to the iframe to ensure it is in view
            await iframe.scroll_into_view_if_needed()

            # Wait for the iframe content to fully load by checking for an image inside the iframe
            await iframe.evaluate("""
                (iframe) => {
                    const contentWindow = iframe.contentWindow || iframe.contentDocument;
                    if (contentWindow && contentWindow.document) {
                        const images = contentWindow.document.querySelectorAll('img');
                        return Array.from(images).some(img => img.complete && img.naturalWidth > 0);
                    }
                    return false;
                }
            """)
    
    except Exception as e:
        tqdm.write(f"Error ensuring Embedly thumbnail loaded: {e}")

# Function to scroll and ensure lazy-loaded content
async def scroll_and_wait(page, wait_time=3000):
    try:
        # Scroll to the bottom of the page to trigger lazy loading
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        await page.wait_for_timeout(2000)  # Reduce this time to 2s for faster scrolling

        # Scroll back to the top of the page
        await page.evaluate("window.scrollTo(0, 0);")

        # Check for lazy-loaded content (reduce the default wait time)
        await page.wait_for_timeout(wait_time)

        # Ensure Embedly thumbnails are fully loaded
        await ensure_embedly_thumbnails(page)

    except Exception as e:
        tqdm.write(f"Error during scrolling or waiting: {e}")

# Async function to capture screenshots in parallel
async def capture_screenshots(context, urls, sem, index, url, pbar):
    async with sem:  # Semaphore to limit concurrent pages
        page = await context.new_page()  # Use the same context to retain cookies
        try:
            await page.goto(url, wait_until='networkidle')

            # Accept cookies on every page
            await accept_cookies(page)

            # Scroll and wait for lazy-loaded content
            await scroll_and_wait(page, wait_time=5000)

            # Generate filename and save screenshot
            screenshot_path = create_filename_from_url(url, index)
            await page.screenshot(path=screenshot_path, full_page=True)

        except Exception as e:
            tqdm.write(f"Error capturing {url}: {e}")

        # Update the progress bar only when each task completes
        pbar.update(1)

        await page.close()

# Function to handle parallel execution of screenshot captures
async def run_screenshot_capture(urls, concurrent_tasks=5):
    sem = Semaphore(concurrent_tasks)  # Limit concurrency to 5 pages at a time
    tasks = []

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()  # Shared context to retain cookies between pages

        with tqdm(total=len(urls), desc="Taking screenshots", unit="page", ncols=80) as pbar:
            for index, url in enumerate(urls):
                tasks.append(asyncio.create_task(capture_screenshots(context, urls, sem, index, url, pbar)))

            await asyncio.gather(*tasks)
        await browser.close()

if __name__ == "__main__":
    sitemap_urls = get_urls_from_sitemap(sitemap_url)
    
    if sitemap_urls:
        tqdm.write(f"Found {len(sitemap_urls)} URLs.")
        asyncio.run(run_screenshot_capture(sitemap_urls, concurrent_tasks=5))  # Run in parallel (5 pages at a time)
    else:
        tqdm.write("No URLs found or error retrieving sitemap.")