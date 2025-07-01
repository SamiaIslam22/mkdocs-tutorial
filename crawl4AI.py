import asyncio
import os
import re
from typing import List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
import requests
from xml.etree import ElementTree
from urllib.parse import urlparse, unquote


def clean_filename(url: str) -> str:
    """Convert URL to a clean filename"""
    parsed = urlparse(url)
    # Remove protocol and www
    clean_path = parsed.netloc.replace('www.', '') + parsed.path
    # Remove file extensions and clean up
    clean_path = re.sub(r'\.[^/]*$', '', clean_path)
    # Replace special characters with hyphens
    clean_path = re.sub(r'[^a-zA-Z0-9/]', '-', clean_path)
    # Remove consecutive hyphens
    clean_path = re.sub(r'-+', '-', clean_path)
    # Remove leading/trailing hyphens
    clean_path = clean_path.strip('-')
    return clean_path + '.md'


async def crawl_and_save(urls: List[str], output_dir: str = "docs/scraped"):
    print(f"\n=== Crawling and Saving to {output_dir} ===")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    browser_config = BrowserConfig(
        headless=True,
        extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    )
    crawl_config = CrawlerRunConfig(markdown_generator=DefaultMarkdownGenerator())
    
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()
    
    try:
        session_id = "session1"
        for i, url in enumerate(urls):
            print(f"Processing {i+1}/{len(urls)}: {url}")
            
            result = await crawler.arun(
                url=url, config=crawl_config, session_id=session_id
            )
            
            if result.success and result.markdown.raw_markdown:
                # Create filename from URL
                filename = clean_filename(url)
                filepath = os.path.join(output_dir, filename)
                
                # Ensure directory exists for nested paths
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                # Add title and source URL to the content
                content = f"# {result.metadata.get('title', 'Scraped Content')}\n\n"
                content += f"**Source:** [{url}]({url})\n\n"
                content += "---\n\n"
                content += result.markdown.raw_markdown
                
                # Save to file
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"  ✓ Saved: {filepath}")
            else:
                print(f"  ✗ Failed: {url} - {result.error_message}")
                
    finally:
        await crawler.close()
    
    print(f"\n✓ Crawling complete! Files saved to {output_dir}")


def get_nanotechnyc_urls():
    """
    Fetches all URLs from the NanoTechNYC website.
    First gets the sitemap index, then processes each individual sitemap.
    """
    sitemap_url = "https://www.nanotechnyc.com/sitemap.xml"
    all_urls = []
    
    try:
        # Get the main sitemap (sitemap index)
        response = requests.get(sitemap_url)
        response.raise_for_status()

        root = ElementTree.fromstring(response.content)
        namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        
        # Get all sitemap URLs from the index
        sitemap_urls = [loc.text for loc in root.findall(".//ns:loc", namespace)]
        print(f"Found {len(sitemap_urls)} sitemap files")
        
        # Process each sitemap to get actual content URLs
        for sitemap_url in sitemap_urls:
            try:
                print(f"Processing sitemap: {sitemap_url}")
                response = requests.get(sitemap_url)
                response.raise_for_status()
                
                sitemap_root = ElementTree.fromstring(response.content)
                urls = [loc.text for loc in sitemap_root.findall(".//ns:loc", namespace)]
                
                # Filter out XML files and add only actual content pages
                content_urls = [url for url in urls if not url.endswith('.xml')]
                all_urls.extend(content_urls)
                print(f"  Found {len(content_urls)} content URLs")
                
            except Exception as e:
                print(f"  Error processing {sitemap_url}: {e}")
                continue

        return all_urls
    except Exception as e:
        print(f"Error fetching main sitemap: {e}")
        return []


async def main():
    urls = get_nanotechnyc_urls()
    if urls:
        print(f"Found {len(urls)} URLs to crawl")
        await crawl_and_save(urls)
        
        # Update mkdocs.yml navigation (optional)
        print("\nTo include scraped content in navigation, add to mkdocs.yml:")
        print("nav:")
        print("  - Home: index.md")
        print("  - Scraped Content: scraped/")
    else:
        print("No URLs found to crawl")


if __name__ == "__main__":
    asyncio.run(main())
