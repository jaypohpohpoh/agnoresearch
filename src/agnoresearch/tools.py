"""Browser and search tools using Crawl4AI and DuckDuckGo."""

import asyncio
import os
import time
from pathlib import Path
from agno.tools import tool

from .schemas import ScrapedContent


# Session storage for Instagram
INSTAGRAM_SESSION_PATH = Path("data/instagram_session.json")

# Retry configuration
MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 2
MAX_CONTENT_LENGTH = 8000


def scrape_website(url: str) -> ScrapedContent:
    """
    Scrape a website URL and return structured content.

    Args:
        url: The URL to scrape.

    Returns:
        ScrapedContent with success status and content/error.
    """
    for attempt in range(MAX_RETRIES):
        try:
            content = asyncio.run(_browse_url_async(url))

            # Check for failure indicators in content
            if content.startswith("Failed to fetch") or content.startswith("Error"):
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY_SECONDS)
                    continue
                return ScrapedContent(url=url, success=False, error=content)

            # Truncate content if too long
            if len(content) > MAX_CONTENT_LENGTH:
                content = content[:MAX_CONTENT_LENGTH] + "\n\n[Content truncated...]"

            return ScrapedContent(
                url=url,
                success=True,
                content=content,
                content_length=len(content),
            )
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY_SECONDS)
                continue
            return ScrapedContent(url=url, success=False, error=str(e))

    return ScrapedContent(url=url, success=False, error="Max retries exceeded")


def scrape_social(url: str) -> ScrapedContent:
    """
    Scrape a social media URL (Instagram or Facebook).

    Args:
        url: The social media URL to scrape.

    Returns:
        ScrapedContent with success status and content/error.
    """
    url_lower = url.lower()

    if "facebook.com" in url_lower:
        # Facebook blocks direct scraping - use search instead
        return ScrapedContent(
            url=url,
            success=False,
            error="Facebook blocks direct scraping. Use search_facebook_structured instead.",
        )

    if "instagram.com" in url_lower:
        for attempt in range(MAX_RETRIES):
            try:
                content = asyncio.run(_browse_instagram_async(url))

                # Check for failure indicators
                if "Failed to fetch" in content or "Error" in content:
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY_SECONDS)
                        continue
                    return ScrapedContent(url=url, success=False, error=content)

                # Check for limited data (login wall)
                if "may require login" in content.lower() or len(content.strip()) < 200:
                    return ScrapedContent(
                        url=url,
                        success=False,
                        error="Instagram returned limited data - may require login or profile is private",
                        content=content,
                        content_length=len(content),
                    )

                if len(content) > MAX_CONTENT_LENGTH:
                    content = content[:MAX_CONTENT_LENGTH] + "\n\n[Content truncated...]"

                return ScrapedContent(
                    url=url,
                    success=True,
                    content=content,
                    content_length=len(content),
                )
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY_SECONDS)
                    continue
                return ScrapedContent(url=url, success=False, error=str(e))

    return ScrapedContent(url=url, success=False, error=f"Unsupported social platform: {url}")


def search_facebook_structured(company_name: str, location: str = "Singapore") -> ScrapedContent:
    """
    Search for a company's Facebook presence via DuckDuckGo.

    Args:
        company_name: Name of the company to search for.
        location: Location to narrow search (default: Singapore).

    Returns:
        ScrapedContent with search results.
    """
    try:
        from duckduckgo_search import DDGS

        query = f"site:facebook.com {company_name} {location}"

        with DDGS() as ddg:
            results = list(ddg.text(query, max_results=5))

        if not results:
            return ScrapedContent(
                url=f"search:facebook:{company_name}",
                success=False,
                error=f"No Facebook results found for '{company_name}' in {location}.",
            )

        output = f"# Facebook Search Results for {company_name}\n\n"
        output += f"Search query: `{query}`\n\n"

        for i, r in enumerate(results, 1):
            title = r.get("title", "Untitled")
            href = r.get("href", "N/A")
            body = r.get("body", "No description available")

            output += f"## {i}. {title}\n"
            output += f"**URL:** {href}\n"
            output += f"**Snippet:** {body}\n\n"

        return ScrapedContent(
            url=f"search:facebook:{company_name}",
            success=True,
            content=output,
            content_length=len(output),
        )

    except ImportError:
        return ScrapedContent(
            url=f"search:facebook:{company_name}",
            success=False,
            error="duckduckgo-search not installed",
        )
    except Exception as e:
        return ScrapedContent(
            url=f"search:facebook:{company_name}",
            success=False,
            error=str(e),
        )


def search_google_reviews(company_name: str, location: str = "") -> ScrapedContent:
    """
    Search for a company's Google reviews via DuckDuckGo.

    Args:
        company_name: Name of the company to search for.
        location: Optional location to narrow search.

    Returns:
        ScrapedContent with review information.
    """
    try:
        from duckduckgo_search import DDGS
        import re

        # Search for Google reviews
        location_str = f" {location}" if location else ""
        query = f'"{company_name}"{location_str} reviews rating stars'

        with DDGS() as ddg:
            results = list(ddg.text(query, max_results=8))

        if not results:
            return ScrapedContent(
                url=f"search:reviews:{company_name}",
                success=False,
                error=f"No review results found for '{company_name}'.",
            )

        output = f"# Review Search Results for {company_name}\n\n"

        # Try to extract rating info from snippets
        rating_found = None
        review_count = None

        for r in results:
            body = r.get("body", "")
            # Look for rating patterns like "4.8 stars", "4.8/5", "Rating: 4.8"
            rating_match = re.search(r'(\d+\.?\d*)\s*(?:stars?|/5|out of 5)', body, re.IGNORECASE)
            if rating_match and not rating_found:
                rating_found = rating_match.group(1)

            # Look for review count patterns like "200 reviews", "(200)"
            count_match = re.search(r'(\d+(?:,\d+)?)\s*reviews?', body, re.IGNORECASE)
            if count_match and not review_count:
                review_count = count_match.group(1)

        if rating_found:
            output += f"**Rating Found:** {rating_found} stars\n"
        if review_count:
            output += f"**Review Count:** {review_count}\n"
        output += "\n"

        # Include relevant snippets
        output += "## Review Snippets\n\n"
        for i, r in enumerate(results[:5], 1):
            title = r.get("title", "Untitled")
            body = r.get("body", "No description available")
            href = r.get("href", "")

            output += f"**{i}. {title}**\n"
            output += f"{body}\n"
            if href:
                output += f"Source: {href}\n"
            output += "\n"

        return ScrapedContent(
            url=f"search:reviews:{company_name}",
            success=True,
            content=output,
            content_length=len(output),
        )

    except ImportError:
        return ScrapedContent(
            url=f"search:reviews:{company_name}",
            success=False,
            error="duckduckgo-search not installed",
        )
    except Exception as e:
        return ScrapedContent(
            url=f"search:reviews:{company_name}",
            success=False,
            error=str(e),
        )


# Legacy tool wrappers for backward compatibility with Agno agent tools


@tool
def browse_url(url: str) -> str:
    """
    Browse a URL and extract its content as markdown.

    Args:
        url: The URL to browse and extract content from.

    Returns:
        Markdown content from the page, or error message if failed.
    """
    # Route to appropriate handler based on URL
    url_lower = url.lower()

    if "instagram.com" in url_lower:
        return asyncio.run(_browse_instagram_async(url))
    elif "facebook.com" in url_lower:
        # Facebook blocks direct scraping - suggest using search_facebook instead
        return (
            f"# Facebook URL: {url}\n\n"
            "[Facebook blocks direct scraping. Use the search_facebook tool instead "
            "to find this company's Facebook presence via DuckDuckGo search.]"
        )
    else:
        return asyncio.run(_browse_url_async(url))


@tool
def search_facebook(company_name: str, location: str = "Singapore") -> str:
    """
    Search for a company's Facebook presence via DuckDuckGo.

    Facebook blocks direct scraping, so this tool searches for Facebook pages
    using DuckDuckGo with a site:facebook.com modifier.

    Args:
        company_name: Name of the company to search for.
        location: Location to narrow search (default: Singapore).

    Returns:
        Facebook search results with page information and snippets.
    """
    try:
        from duckduckgo_search import DDGS

        query = f"site:facebook.com {company_name} {location}"

        with DDGS() as ddg:
            results = list(ddg.text(query, max_results=5))

        if not results:
            return f"No Facebook results found for '{company_name}' in {location}."

        output = f"# Facebook Search Results for {company_name}\n\n"
        output += f"Search query: `{query}`\n\n"

        for i, r in enumerate(results, 1):
            title = r.get("title", "Untitled")
            href = r.get("href", "N/A")
            body = r.get("body", "No description available")

            output += f"## {i}. {title}\n"
            output += f"**URL:** {href}\n"
            output += f"**Snippet:** {body}\n\n"

        return output

    except ImportError:
        return "Error: duckduckgo-search not installed. Run: pip install duckduckgo-search"
    except Exception as e:
        return f"Error searching Facebook: {str(e)}"


@tool
def browse_instagram(url: str) -> str:
    """
    Browse an Instagram URL with authentication for better access.

    Uses saved session if available, otherwise attempts login with
    credentials from environment variables.

    Args:
        url: Instagram URL to browse (profile, post, etc.).

    Returns:
        Extracted content from Instagram page.
    """
    return asyncio.run(_browse_instagram_async(url))


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


async def _browse_instagram_async(url: str, timeout: int = 45) -> str:
    """Browse Instagram with authentication support."""
    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

        # Check for credentials
        username = os.getenv("INSTAGRAM_USERNAME")
        password = os.getenv("INSTAGRAM_PASSWORD")

        # Ensure data directory exists
        INSTAGRAM_SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Configure browser with session storage if available
        browser_config = BrowserConfig(
            headless=True,
            verbose=False,
        )

        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=timeout * 1000,
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Try to load existing session
            has_session = INSTAGRAM_SESSION_PATH.exists()

            if has_session:
                try:
                    # Load session cookies
                    import json
                    session_data = json.loads(INSTAGRAM_SESSION_PATH.read_text())
                    # Session loading would be handled by browser context
                    # For now, we'll attempt the request directly
                except Exception:
                    has_session = False

            # If no session and we have credentials, try to login first
            if not has_session and username and password:
                login_success = await _instagram_login(crawler, username, password)
                if not login_success:
                    return (
                        f"# Instagram: {url}\n\n"
                        "[Instagram login failed. Attempting to fetch public data only.]\n\n"
                        + await _fetch_instagram_public(crawler, url, crawler_config)
                    )

            # Fetch the Instagram page
            result = await crawler.arun(url=url, config=crawler_config)

            if result.success:
                content = result.markdown or result.cleaned_html or ""

                # Check if we got blocked (login wall)
                content_lower = content.lower()
                if len(content.strip()) < 200 or "log in" in content_lower:
                    # Try public data extraction
                    return (
                        f"# Instagram: {url}\n\n"
                        "[Instagram returned limited data - may require login or profile is private.]\n\n"
                        f"**URL:** {url}\n"
                        "**Note:** Consider checking the profile manually for follower count, "
                        "posting frequency, and content themes."
                    )

                # Extract key Instagram metrics if visible
                extracted = _extract_instagram_data(content, url)
                return extracted

            else:
                return f"Failed to fetch Instagram {url}: {result.error_message or 'Unknown error'}"

    except ImportError:
        return "Error: crawl4ai not installed. Run: pip install crawl4ai"
    except Exception as e:
        return f"Error browsing Instagram {url}: {str(e)}"


async def _instagram_login(crawler, username: str, password: str) -> bool:
    """Attempt Instagram login and save session."""
    try:
        from crawl4ai import CrawlerRunConfig, CacheMode

        login_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=60000,
        )

        # Navigate to login page
        login_result = await crawler.arun(
            url="https://www.instagram.com/accounts/login/",
            config=login_config
        )

        if not login_result.success:
            return False

        # Note: Full login automation would require JavaScript execution
        # and handling 2FA. For now, this is a placeholder that attempts
        # basic cookie-based session management.

        # In production, you would:
        # 1. Use playwright's page.fill() for username/password
        # 2. Click the login button
        # 3. Handle potential 2FA
        # 4. Save cookies/storage state

        return False  # Login automation not fully implemented

    except Exception:
        return False


async def _fetch_instagram_public(crawler, url: str, config) -> str:
    """Fetch whatever public data is available from Instagram."""
    try:
        result = await crawler.arun(url=url, config=config)
        if result.success and result.markdown:
            return result.markdown[:2000]
        return "[No public data available]"
    except Exception:
        return "[Failed to fetch public data]"


def _extract_instagram_data(content: str, url: str) -> str:
    """Extract structured data from Instagram page content."""
    output = f"# Instagram Profile: {url}\n\n"

    # Try to find common Instagram metrics in the content
    import re

    # Look for follower counts (various formats)
    follower_match = re.search(r'(\d+(?:,\d+)*(?:\.\d+)?[KMB]?)\s*(?:followers|Followers)', content)
    if follower_match:
        output += f"**Followers:** {follower_match.group(1)}\n"

    # Look for following counts
    following_match = re.search(r'(\d+(?:,\d+)*(?:\.\d+)?[KMB]?)\s*(?:following|Following)', content)
    if following_match:
        output += f"**Following:** {following_match.group(1)}\n"

    # Look for post counts
    posts_match = re.search(r'(\d+(?:,\d+)*)\s*(?:posts|Posts)', content)
    if posts_match:
        output += f"**Posts:** {posts_match.group(1)}\n"

    output += "\n## Raw Content Preview\n\n"

    # Truncate content for LLM context
    if len(content) > 5000:
        content = content[:5000] + "\n\n[Content truncated...]"

    output += content

    return output
