"""External Search and Market Research Provider Abstraction with SSRF Safeguards."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import ipaddress
import logging
import re
import socket
from typing import List, Optional
from urllib.parse import urlparse
import httpx

from app.config import get_settings
from app.schemas.market_research import SourceItem

logger = logging.getLogger(__name__)


def is_safe_external_url(url: str) -> bool:
    """Validate that URL uses public HTTP/HTTPS and does not target private or local networks (SSRF defense)."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        # Block localhost and typical internal hostnames
        if hostname.lower() in ("localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal"):
            return False

        # Resolve IP to protect against DNS rebinding or private IP ranges
        try:
            addr_info = socket.getaddrinfo(hostname, None)
            for item in addr_info:
                ip_str = item[4][0]
                ip_obj = ipaddress.ip_address(ip_str)
                if (
                    ip_obj.is_private
                    or ip_obj.is_loopback
                    or ip_obj.is_link_local
                    or ip_obj.is_multicast
                    or ip_obj.is_unspecified
                ):
                    return False
        except (socket.gaierror, ValueError):
            # If resolution fails, don't allow potentially malicious host
            return False

        return True
    except Exception:
        return False


class BaseResearchProvider(ABC):
    """Abstract interface for external market research and search providers."""

    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> List[SourceItem]:
        """Execute web search and return structured source citations."""
        pass


class DuckDuckGoSearchProvider(BaseResearchProvider):
    """Public DuckDuckGo provider requiring no paid credentials."""

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self.timeout = timeout_seconds
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    def search(self, query: str, max_results: int = 5) -> List[SourceItem]:
        sources: List[SourceItem] = []
        retrieval_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True, headers=self.headers) as client:
                # Use DuckDuckGo HTML search endpoint
                url = "https://html.duckduckgo.com/html/"
                response = client.post(url, data={"q": query})

                if response.status_code == 200:
                    html_text = response.text
                    # Extract search result links: <a class="result__url" href="..."> or <a class="result__snippet" ...>
                    # Using regex to parse simple anchor and snippet tags reliably without heavy external parser
                    link_pattern = re.compile(
                        r'<a[^>]+class="result__snippet"[^>]*href="(?P<raw_url>[^"]+)"[^>]*>(?P<snippet>.*?)</a>',
                        re.IGNORECASE | re.DOTALL,
                    )
                    title_pattern = re.compile(
                        r'<a[^>]+class="result__url"[^>]*href="(?P<raw_url>[^"]+)"[^>]*>(?P<title>.*?)</a>',
                        re.IGNORECASE | re.DOTALL,
                    )

                    matches = list(link_pattern.finditer(html_text))
                    for m in matches[:max_results]:
                        raw_u = m.group("raw_url")
                        # Unpack DDG redirect wrapper: //duckduckgo.com/l/?uddg=https%3A%2F%2F...
                        if "uddg=" in raw_u:
                            import urllib.parse
                            qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw_u).query)
                            target_url = qs.get("uddg", [raw_u])[0]
                        else:
                            target_url = raw_u

                        if not target_url.startswith("http"):
                            target_url = "https:" + target_url if target_url.startswith("//") else "https://" + target_url

                        # SSRF safeguard
                        if not is_safe_external_url(target_url):
                            continue

                        snippet_clean = re.sub(r"<[^>]+>", "", m.group("snippet")).strip()
                        parsed_host = urlparse(target_url).hostname or "Source"

                        sources.append(
                            SourceItem(
                                url=target_url,
                                title=f"{parsed_host} — Search Result",
                                snippet=snippet_clean or f"Information regarding {query}",
                                retrieved_at=retrieval_date,
                                source_type="website",
                            )
                        )

            logger.info(f"DuckDuckGo search for '{query}' returned {len(sources)} sources.")
            return sources

        except Exception as e:
            logger.warning(f"DuckDuckGo search request failed for query '{query}': {str(e)}")
            return sources


class TavilySearchProvider(BaseResearchProvider):
    """Tavily AI research provider when API key is configured."""

    def __init__(self, api_key: str, timeout_seconds: float = 12.0) -> None:
        self.api_key = api_key
        self.timeout = timeout_seconds

    def search(self, query: str, max_results: int = 5) -> List[SourceItem]:
        sources: List[SourceItem] = []
        retrieval_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": self.api_key,
                        "query": query,
                        "search_depth": "basic",
                        "max_results": max_results,
                    },
                )
                if res.status_code == 200:
                    data = res.json()
                    for r in data.get("results", []):
                        u = r.get("url", "")
                        if is_safe_external_url(u):
                            sources.append(
                                SourceItem(
                                    url=u,
                                    title=r.get("title", "Market Research Source"),
                                    snippet=r.get("content", ""),
                                    retrieved_at=retrieval_date,
                                    source_type="website",
                                )
                            )
            return sources
        except Exception as e:
            logger.warning(f"Tavily search request failed for '{query}': {str(e)}")
            return sources


class MockResearchProvider(BaseResearchProvider):
    """Deterministic test double providing realistic research citations."""

    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail

    def search(self, query: str, max_results: int = 5) -> List[SourceItem]:
        if self.should_fail:
            raise RuntimeError("Simulated search provider failure.")

        return [
            SourceItem(
                url="https://news.ycombinator.com/item?id=38129412",
                title="Hacker News: Discussion on AI Business Planning & Architecture Tools",
                snippet="Founders discussing lean business canvases, why spreadsheets fail for financial forecasts, and willingness to pay.",
                retrieved_at="2026-10-10",
                source_type="website",
                evidence_note="Community discussion indicating active demand",
            ),
            SourceItem(
                url="https://www.producthunt.com/products/business-model-canvas",
                title="Product Hunt: Competitor Directory and User Reviews",
                snippet="Existing solutions charge between $19/mo and $49/mo, with frequent complaints about lack of deterministic financial calculations.",
                retrieved_at="2026-10-10",
                source_type="industry_report",
                evidence_note="Pricing and feature benchmark",
            ),
            SourceItem(
                url="https://github.com/topics/business-plan-generator",
                title="GitHub Topics: Open Source Startup Architecture Tools",
                snippet="Over 250 open source repositories addressing business generation, demonstrating high developer interest.",
                retrieved_at="2026-10-10",
                source_type="website",
                evidence_note="Technical ecosystem adoption",
            ),
        ][:max_results]


def get_research_provider() -> BaseResearchProvider:
    """Factory selecting configured search provider."""
    import os
    tavily_key = os.environ.get("TAVILY_API_KEY") or os.environ.get("RESEARCH_API_KEY")
    if tavily_key and tavily_key.strip():
        return TavilySearchProvider(api_key=tavily_key.strip())
    return DuckDuckGoSearchProvider()
