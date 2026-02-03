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
