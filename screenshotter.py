import os
import re
import asyncio
from playwright.async_api import async_playwright
from tqdm import tqdm
from asyncio import Semaphore

# ✅ Hardcoded list of authenticated URLs to capture
urls_to_capture = [
    "https://course.ilc.tvo.org/content/enforced/22818537-MHF4U-EN-02-02-ON-(I-D-0922)/course_content/lessons/mhf4u_u1la1.html?ou=22818537&d2l_body_type=3",
    "https://course.ilc.tvo.org/content/enforced/22818537-MHF4U-EN-02-02-ON-(I-D-0922)/course_content/lessons/mhf4u_u1la2.html?ou=22818537&d2l_body_type=3",
    "https://course.ilc.tvo.org/content/enforced/22818537-MHF4U-EN-02-02-ON-(I-D-0922)/course_content/lessons/mhf4u_u1la3.html?ou=22818537&d2l_body_type=3",
    # Add more URLs here
]

# ✅ Login credentials (must be set via environment variables)
USERNAME = os.getenv("ILC_USERNAME")
PASSWORD = os.getenv("ILC_PASSWORD")

if not USERNAME or not PASSWORD:
    raise ValueError("ILC_USERNAME and ILC_PASSWORD environment variables must be set")
LOGIN_URL = "https://portal.ilc.tvo.org/PublicWelcome.aspx?cas=1&service=https%3a%2f%2fcourse.ilc.tvo.org%2fd2l%2fcustom%2fcas"  # Adjust if needed

# ✅ CAS login function targeting real field IDs and waiting for /home
async def login(page):
    # Use domcontentloaded instead of networkidle
    await page.goto(LOGIN_URL, wait_until="domcontentloaded")

    # Fill in login form fields using accurate selectors
    await page.fill('#ct100_ContentPlaceHolder1_tbLogin', USERNAME)
    await page.fill('#ct100_ContentPlaceHolder1_tbPassword', PASSWORD)
    await page.click('button[type="submit"]')

    # ✅ Wait for redirect to /home
    await page.wait_for_url("**/home", timeout=15000)
    await page.wait_for_load_state("networkidle")
    tqdm.write("Login successful and redirected to /home")

# ✅ Screenshot save directory
screenshot_directory = "/Users/amypark/DifferSnapperDev/MHF4U-screenshots"
if not os.path.exists(screenshot_directory):
    os.makedirs(screenshot_directory)

# ✅ Generate simple filenames like "1.png", "2.png", etc.
def create_filename_from_url(url, index):
    filename = f"{index+1}.png"
    return os.path.join(screenshot_directory, filename)

# Accept cookies on page
async def accept_cookies(page):
    try:
        await page.wait_for_selector('body > div.page-wrapper > div.set-all-components-to-display-none-and-use-this-div-to-create-a-symbol > div.fs-cc-banner_component > div.fs-cc-banner_container > div.fs-cc-banner_buttons-wrapper > a:nth-child(3)', timeout=5000)
        await page.click('body > div.page-wrapper > div.set-all-components-to-display-none-and-use-this-div-to-create-a-symbol > div.fs-cc-banner_component > div.fs-cc-banner_container > div.fs-cc-banner_buttons-wrapper > a:nth-child(3)')
        tqdm.write("Cookies accepted")
    except Exception:
        pass  # Silently continue if no cookies prompt

# Expand all drawers (e.g., collapsible panels or accordions)
async def expand_all_drawers(page):
    try:
        # General selector: any button with aria-expanded="false"
        drawer_buttons = await page.query_selector_all('button[aria-expanded="false"]')

        for btn in drawer_buttons:
            try:
                await btn.scroll_into_view_if_needed()
                await btn.click()
                await page.wait_for_timeout(300)  # slight delay between clicks
            except Exception as e:
                tqdm.write(f"Error clicking drawer button: {e}")

        tqdm.write(f"{len(drawer_buttons)} drawers expanded.")
    except Exception as e:
        tqdm.write(f"Error expanding drawers: {e}")

# Scroll and lazy-load content
async def scroll_and_wait(page, wait_time=3000):
    try:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        await page.wait_for_timeout(2000)
        await page.evaluate("window.scrollTo(0, 0);")
        await page.wait_for_timeout(wait_time)
    except Exception as e:
        tqdm.write(f"Scroll/wait error: {e}")

# ✅ Log in to the portal once
async def login(page):
    await page.goto(LOGIN_URL, wait_until="networkidle")
    await page.fill('input[name="userName"]', USERNAME)
    await page.fill('input[name="password"]', PASSWORD)
    await page.click('button[type="submit"]')  # Adjust if needed
    await page.wait_for_load_state("networkidle")
    tqdm.write("Login successful")

# Take one screenshot
async def capture_screenshots(context, urls, sem, index, url, pbar):
    async with sem:
        page = await context.new_page()
        try:
            await page.goto(url, wait_until='networkidle')
            await accept_cookies(page)

            # ✅ Expand drawers before scrolling
            await expand_all_drawers(page)

            await scroll_and_wait(page, wait_time=5000)
            screenshot_path = create_filename_from_url(url, index)
            await page.screenshot(path=screenshot_path, full_page=True)
        except Exception as e:
            tqdm.write(f"Error capturing {url}: {e}")
        pbar.update(1)
        await page.close()

# Run all screenshots using shared login session
async def run_screenshot_capture(urls, concurrent_tasks=5):
    sem = Semaphore(concurrent_tasks)
    tasks = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        # ✅ Log in once and reuse session
        page = await context.new_page()
        await login(page)
        await page.close()

        # ✅ Start screenshots
        with tqdm(total=len(urls), desc="Taking screenshots", unit="page", ncols=80) as pbar:
            for index, url in enumerate(urls):
                tasks.append(asyncio.create_task(capture_screenshots(context, urls, sem, index, url, pbar)))
            await asyncio.gather(*tasks)

        await browser.close()

# ✅ Main
if __name__ == "__main__":
    if urls_to_capture:
        tqdm.write(f"Capturing {len(urls_to_capture)} authenticated URLs.")
        asyncio.run(run_screenshot_capture(urls_to_capture, concurrent_tasks=5))
    else:
        tqdm.write("URL list is empty.")