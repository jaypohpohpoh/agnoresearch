"""Browser tool using Crawl4AI for URL scraping."""

import asyncio
from agno.tools import tool


@tool
def browse_url(url: str) -> str:
    """
    Browse a URL and extract its content as markdown.

    Args:
        url: The URL to browse and extract content from.

    Returns:
        Markdown content from the page, or error message if failed.
    """
    return asyncio.run(_browse_url_async(url))


async def _browse_url_async(url: str, timeout: int = 30) -> str:
    """Async implementation of URL browsing."""
    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

        browser_config = BrowserConfig(
            headless=True,
            verbose=False,
        )

        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=timeout * 1000,
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=crawler_config)

            if result.success:
                content = result.markdown or result.cleaned_html or ""

                # Detect blocked/gated content
                content_lower = content.lower()

                # Instagram blocks scrapers - returns minimal/empty content
                if "instagram.com" in url.lower() and len(content.strip()) < 200:
                    return f"# Content from {url}\n\n[Instagram blocked scraping - limited public data available. Consider checking their profile manually for: posting frequency, content themes, engagement levels.]"

                # Facebook often redirects to login
                if "facebook.com" in url.lower():
                    if "log in" in content_lower and "forgotten account" in content_lower:
                        return f"# Content from {url}\n\n[Facebook requires login to view this page. Limited public data available. The page exists but detailed content is gated.]"

                # Check for very thin content that won't be useful
                if len(content.strip()) < 100:
                    return f"# Content from {url}\n\n[Page returned minimal content - may be blocked or require authentication.]"

                # Truncate if too long (keep first 10K chars for LLM context)
                if len(content) > 10000:
                    content = content[:10000] + "\n\n[Content truncated...]"

                return f"# Content from {url}\n\n{content}"
            else:
                return f"Failed to fetch {url}: {result.error_message or 'Unknown error'}"

    except ImportError:
        return "Error: crawl4ai not installed. Run: pip install crawl4ai"
    except Exception as e:
        return f"Error browsing {url}: {str(e)}"
