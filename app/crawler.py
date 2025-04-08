# app/crawler.py
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from collections import defaultdict

PRODUCT_PATTERNS = {
    "virgio.com": [r"/products/"],
    "tatacliq.com": [r"/p[-/]"],
    "nykaafashion.com": [r"/p/", r"/product/"],
    "westside.com": [r"/products/"],
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/89.0 Safari/537.36"
}

MAX_CONCURRENT_REQUESTS = 10
MAX_PAGES_PER_DOMAIN = 300


class Crawler:
    def __init__(self, domains):
        self.domains = domains
        self.visited = set()
        self.results = defaultdict(set)
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    def is_valid_product_url(self, url, domain):
        patterns = PRODUCT_PATTERNS.get(domain, [])
        for pattern in patterns:
            if re.search(pattern, url):
                return True
        return False

    def normalize_url(self, base_url, link):
        return urljoin(base_url, link)

    def get_links(self, html, base_url, domain):
        soup = BeautifulSoup(html, 'lxml')
        links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = self.normalize_url(base_url, href)
            parsed = urlparse(full_url)
            if domain in parsed.netloc:
                links.add(full_url.split('#')[0])
        return links

    async def fetch(self, session, url):
        try:
            async with self.semaphore:
                async with session.get(url, timeout=10) as response:
                    if 'text/html' in response.headers.get('Content-Type', ''):
                        return await response.text()
        except Exception:
            pass
        return None

    async def crawl_domain(self, session, domain):
        queue = asyncio.Queue()
        await queue.put(f"https://{domain}")
        pages_crawled = 0

        while not queue.empty() and pages_crawled < MAX_PAGES_PER_DOMAIN:
            current_url = await queue.get()
            if current_url in self.visited:
                continue
            self.visited.add(current_url)

            html = await self.fetch(session, current_url)
            if not html:
                continue

            pages_crawled += 1
            links = self.get_links(html, current_url, domain)

            for link in links:
                if self.is_valid_product_url(link, domain):
                    self.results[domain].add(link)
                elif link not in self.visited:
                    await queue.put(link)

    async def run(self):
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            tasks = [self.crawl_domain(session, domain) for domain in self.domains]
            await asyncio.gather(*tasks)
        return {k: list(v) for k, v in self.results.items()}
