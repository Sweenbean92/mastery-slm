# BBC Bitesize Web Crawler

This web crawler scrapes National 5 Mathematics content from BBC Bitesize and saves it to the `docs` folder.

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the crawler:

```bash
python webcrawler.py
```

The crawler will:
1. Start from BBC Bitesize National 5 Mathematics pages
2. Follow relevant links to find more content
3. Extract text content from each page
4. Save the content as text files in the `docs` folder

## Features

- **Rate Limiting**: Includes delays between requests to be respectful to BBC's servers
- **Error Handling**: Retries failed requests with exponential backoff
- **Content Extraction**: Intelligently extracts main content from pages
- **Duplicate Prevention**: Tracks visited URLs to avoid re-scraping
- **Safe Filenames**: Creates safe filenames from page titles

## Configuration

You can customize the crawler by modifying the `BBCBitesizeCrawler` class:

- `base_url`: Base URL for BBC Bitesize
- `output_dir`: Directory to save scraped content (default: "docs")
- `max_pages`: Maximum number of pages to crawl (default: 100)

## Important Notes

⚠️ **Please respect BBC's Terms of Service and robots.txt**

- The crawler includes rate limiting (1 second delay between requests)
- Always check robots.txt before crawling: https://www.bbc.co.uk/robots.txt
- Use responsibly and don't overload their servers
- This is for educational purposes only

## Output Format

Each scraped page is saved as a `.txt` file with:
- URL of the source page
- Page title
- Main content text

Files are saved in the `docs` folder with descriptive filenames based on the page title.

