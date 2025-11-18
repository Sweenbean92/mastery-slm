import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import re
from pathlib import Path

class BBCBitesizeCrawler:
    def __init__(self, base_url="https://www.bbc.co.uk/bitesize", output_dir="docs"):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.visited_urls = set()
        self.scraped_count = 0
        
    def fetch_page(self, url, retries=3):
        """Fetch a page with retry logic and rate limiting"""
        if url in self.visited_urls:
            return None
            
        for attempt in range(retries):
            try:
                time.sleep(1)  # Rate limiting - be respectful
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                self.visited_urls.add(url)
                return response.text
            except requests.RequestException as e:
                print(f"Error fetching {url} (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return None
        return None
    
    def clean_text(self, text):
        """Clean and normalize text content"""
        if not text:
            return ""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = text.strip()
        return text
    
    def extract_content(self, html, url):
        """Extract main content from a BBC Bitesize page"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        # Remove common navigation and UI elements
        for elem in soup.find_all(['nav', 'header', 'footer', 'aside', 'button', 'form']):
            elem.decompose()
        
        # Try to find main content area - BBC Bitesize uses various structures
        content = []
        title = ""
        
        # Try to find title - BBC Bitesize often uses h1 or specific title classes
        title_elem = (
            soup.find('h1', class_=re.compile(r'title|heading', re.I)) or
            soup.find('h1') or
            soup.find('title')
        )
        if title_elem:
            title = self.clean_text(title_elem.get_text())
            # Remove "BBC Bitesize" prefix if present
            title = re.sub(r'^\s*BBC\s+Bitesize\s*[-–—]\s*', '', title, flags=re.I)
        
        # Look for main content in common BBC Bitesize structures
        # BBC Bitesize often uses specific classes for content
        main_content = (
            soup.find('main') or
            soup.find('article') or
            soup.find('div', class_=re.compile(r'content|main|article|text|body|guide|topic|revision', re.I)) or
            soup.find('div', id=re.compile(r'content|main|article|body', re.I)) or
            soup.find('div', {'data-testid': re.compile(r'content|article|main', re.I)})
        )
        
        if main_content:
            # Extract structured content
            # Get headings first to maintain structure
            headings = main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for heading in headings:
                text = self.clean_text(heading.get_text())
                if text and len(text) > 3:
                    content.append(f"\n{text}\n{'=' * len(text)}\n")
            
            # Extract paragraphs, lists, and other content
            for elem in main_content.find_all(['p', 'li', 'dd', 'dt', 'blockquote']):
                text = self.clean_text(elem.get_text())
                if text and len(text) > 10:  # Filter out very short text
                    # Avoid duplicates if we already have it as a heading
                    if not any(text in existing for existing in content[-5:]):
                        content.append(text)
        else:
            # Fallback: get all paragraphs and headings
            for elem in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li']):
                text = self.clean_text(elem.get_text())
                if text and len(text) > 10:
                    content.append(text)
        
        # Clean up content - remove duplicates and empty strings
        cleaned_content = []
        seen = set()
        for item in content:
            item_lower = item.lower().strip()
            if item_lower and item_lower not in seen and len(item_lower) > 10:
                seen.add(item_lower)
                cleaned_content.append(item)
        
        return title, '\n\n'.join(cleaned_content)
    
    def find_links(self, html, base_url):
        """Find all relevant links on a page"""
        soup = BeautifulSoup(html, 'html.parser')
        links = set()
        
        # Look for links to National 5 Mathematics content
        # Prioritize links that look like content pages
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if not href:
                continue
            
            # Skip mailto, tel, and other non-HTTP links
            if href.startswith(('mailto:', 'tel:', 'javascript:', '#')):
                continue
            
            # Convert relative URLs to absolute
            full_url = urljoin(base_url, href)
            
            # Normalize URL (remove fragments, trailing slashes)
            parsed = urlparse(full_url)
            normalized_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
            if parsed.query:
                normalized_url += f"?{parsed.query}"
            
            # Filter for relevant URLs
            if self.is_relevant_url(normalized_url):
                links.add(normalized_url)
        
        return links
    
    def is_relevant_url(self, url):
        """Check if URL is relevant to National 5 Mathematics"""
        url_lower = url.lower()
        
        # Must be BBC Bitesize
        if 'bbc.co.uk/bitesize' not in url_lower and 'bbc.com/bitesize' not in url_lower:
            return False
        
        # Exclude certain sections that don't contain learning material
        # BUT keep /revision/ pages as they contain actual learning content
        exclude_patterns = [
            '/quizzes/', '/quiz/',  # Quiz pages (we want the actual content)
            '/games/', '/game/',
            '/images/', '/image/',
            '/downloads/', '/download/',
            '/print/', '/share/',
            '/search',
            '/topics?page=',
            '/articles/',  # Article listings, not content
            '/videos/', '/video/',  # Video pages (optional - remove if you want videos)
            '/my-bitesize',
            '/sign-in',
            '/register',
            '/about',
            '/contact',
            '/terms',
            '/privacy',
            '/cookies',
            '/accessibility',
            '/help',
            '/jobs',
            '/podcasts',
            '/radio',
            '/skillswise',
            '/external',
            '?page=',
            '#',  # Anchors
        ]
        # Don't exclude if it's a revision page (they contain learning material)
        is_revision_page = '/revision/' in url_lower and '/guides/' in url_lower
        if not is_revision_page and any(pattern in url_lower for pattern in exclude_patterns):
            return False
        
        # Check for National 5 Mathematics subject code (ztrjmp3)
        has_subject_code = 'ztrjmp3' in url_lower
        
        # Check for National 5 and Mathematics keywords
        n5_keywords = ['national-5', 'national5', 'n5', 'national 5']
        math_keywords = ['maths', 'mathematics', 'math']
        
        has_n5 = any(keyword in url_lower for keyword in n5_keywords)
        has_math = any(keyword in url_lower for keyword in math_keywords)
        
        # Look for content pages - these typically have guides, topics, or revision paths
        # BBC Bitesize content URLs often look like:
        # /guides/[code]/revision/[number] - revision material pages
        # /guides/..., /topics/..., /revision/..., /learn/...
        has_content_path = any(path in url_lower for path in [
            '/guides/', '/topics/', '/revision/', '/learn/', '/study/',
            '/bitesize/guides/', '/bitesize/topics/'
        ])
        
        # Specifically check for revision pages (e.g., /guides/z3rqcj6/revision/1)
        # These are important learning material pages
        has_revision_page = '/revision/' in url_lower and '/guides/' in url_lower
        
        # Include the main subject page and any pages with the subject code
        if has_subject_code:
            return True
        
        # Include revision pages (they contain actual learning material)
        if has_revision_page:
            return True
        
        # Include content pages that are related to National 5 Mathematics
        if has_content_path and (has_n5 or has_math or has_subject_code):
            return True
        
        # Include pages that clearly mention National 5 and Mathematics
        if has_n5 and has_math:
            return True
        
        return False
    
    def save_content(self, title, content, url):
        """Save scraped content to a file"""
        if not content or len(content.strip()) < 50:
            return False
        
        # Create a safe filename from title or URL
        if title:
            filename = re.sub(r'[^\w\s-]', '', title)[:100]
            filename = re.sub(r'[-\s]+', '-', filename)
        else:
            # Use URL path as filename
            parsed = urlparse(url)
            filename = parsed.path.strip('/').replace('/', '-')[-50:]
        
        if not filename:
            filename = f"content_{self.scraped_count}"
        
        filename = f"{filename}.txt"
        filepath = self.output_dir / filename
        
        # Avoid overwriting - add number if exists
        counter = 1
        original_filepath = filepath
        while filepath.exists():
            stem = original_filepath.stem
            filepath = self.output_dir / f"{stem}_{counter}.txt"
            counter += 1
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"URL: {url}\n")
                f.write(f"Title: {title}\n")
                f.write("=" * 80 + "\n\n")
                f.write(content)
            print(f"Saved: {filepath.name}")
            self.scraped_count += 1
            return True
        except Exception as e:
            print(f"Error saving {filepath}: {e}")
            return False
    
    def crawl(self, start_urls=None, max_pages=200):
        """Main crawling function"""
        if start_urls is None:
            # Default start URLs for National 5 Mathematics
            # ztrjmp3 is BBC's subject code for National 5 Mathematics
            start_urls = [
                "https://www.bbc.co.uk/bitesize/subjects/ztrjmp3",  # National 5 Mathematics main page
            ]
        
        to_visit = list(start_urls)
        pages_crawled = 0
        
        print(f"Starting crawl with {len(start_urls)} starting URLs")
        print(f"Maximum pages to crawl: {max_pages}")
        print(f"Target URL: {start_urls[0]}")
        print("-" * 80)
        
        while to_visit and pages_crawled < max_pages:
            url = to_visit.pop(0)
            
            if url in self.visited_urls:
                continue
            
            print(f"\n[{pages_crawled + 1}/{max_pages}] Crawling: {url}")
            html = self.fetch_page(url)
            
            if not html:
                print("  → Failed to fetch page")
                continue
            
            # Extract content
            title, content = self.extract_content(html, url)
            
            if content and len(content.strip()) > 100:  # Only save substantial content
                saved = self.save_content(title, content, url)
                if saved:
                    print(f"  → Saved: {title[:60]}...")
                else:
                    print(f"  → Content too short, skipping")
            else:
                print(f"  → No substantial content found")
            
            # Find new links
            new_links = self.find_links(html, url)
            print(f"  → Found {len(new_links)} relevant links")
            
            # Add new links to queue (prioritize content pages)
            # Prioritize revision pages first (they contain the actual learning material)
            revision_links = [l for l in new_links if '/revision/' in l.lower() and '/guides/' in l.lower()]
            content_links = [l for l in new_links if any(path in l.lower() for path in ['/guides/', '/topics/']) and l not in revision_links]
            other_links = [l for l in new_links if l not in revision_links and l not in content_links]
            
            # Add revision links first (highest priority - actual learning material)
            for link in revision_links:
                if link not in self.visited_urls and link not in to_visit:
                    to_visit.append(link)
            
            # Then add other content links (guides, topics)
            for link in content_links:
                if link not in self.visited_urls and link not in to_visit:
                    to_visit.append(link)
            
            # Then add other relevant links
            for link in other_links:
                if link not in self.visited_urls and link not in to_visit:
                    to_visit.append(link)
            
            pages_crawled += 1
        
        print("\n" + "=" * 80)
        print(f"Crawl completed!")
        print(f"Total pages visited: {len(self.visited_urls)}")
        print(f"Total files saved: {self.scraped_count}")
        print(f"Files saved in: {self.output_dir.absolute()}")

def main():
    """Main entry point"""
    print("BBC Bitesize National 5 Mathematics Web Crawler")
    print("=" * 80)
    
    crawler = BBCBitesizeCrawler(output_dir="docs")
    
    # You can customize these URLs or add more
    start_urls = [
        "https://www.bbc.co.uk/bitesize/subjects/ztrjmp3",  # National 5 Mathematics main page
    ]
    
    # Crawl with a reasonable limit (increased to get more content)
    crawler.crawl(start_urls=start_urls, max_pages=200)
    
    print("\nNote: Please respect BBC's robots.txt and terms of service.")
    print("This crawler includes rate limiting to be respectful to their servers.")

if __name__ == "__main__":
    main()

