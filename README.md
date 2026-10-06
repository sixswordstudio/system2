# DifferSnapper

Automated web screenshot and content extraction toolkit built with Python and Playwright.

## Overview

A collection of Python automation tools for capturing full-page screenshots and extracting content from various web sources. Perfect for archiving, documentation, and content aggregation workflows.

## Tools

### 📸 DifferSnapper.py
Wikipedia page screenshot capture with metadata tracking
- Fetches pages by title or page ID
- Captures full-page screenshots
- Generates timestamped folders
- Tracks metadata in JSON format

### 📄 contentcatcher.py
Full content extraction and archival from Wikipedia
- Extracts structured content by headers
- Saves organized JSON output
- Includes screenshots alongside content
- Handles lazy-loaded elements

### 🔐 screenshotter.py
Authenticated screenshot capture for educational portals
- Handles login authentication via environment variables
- Cookie consent management
- Expands collapsible content automatically
- Parallel processing with concurrency control

### 🗺️ sitemapper.py
Bulk screenshot generation from XML sitemaps
- Parses sitemap.xml files
- Captures entire site documentation
- Handles Embedly thumbnails
- Smart filename generation

### 🖼️ imagegrabber-nauticalguide.py
Image extraction from documentation sites
- Filters URLs by path patterns
- Deduplicates images via hashing
- Organized sequential naming
- Retry mechanism for network errors

## Features

✨ **Parallel Processing**: Async/await architecture for efficient bulk operations  
🍪 **Smart Handling**: Automatic cookie consent and lazy-load content support  
📁 **Organized Output**: Timestamped folders with comprehensive metadata tracking  
📊 **Progress Tracking**: Visual progress bars via tqdm for long-running operations  
🔒 **Secure**: Environment variable based credential management

## Requirements

```bash
pip install playwright requests beautifulsoup4 tqdm
playwright install chromium
```

## Configuration

For authenticated tools, set environment variables:

```bash
export ILC_USERNAME="your_username"
export ILC_PASSWORD="your_password"
```

## Usage Examples

### Capture Wikipedia Screenshots
```bash
python DifferSnapper.py
```

### Extract Full Content
```bash
python contentcatcher.py
```

### Scrape from Sitemap
```bash
python sitemapper.py
```

## Security

- No hardcoded credentials
- Environment variable based authentication
- Comprehensive `.gitignore` excludes sensitive files

## License

Personal project - use at your own discretion.
