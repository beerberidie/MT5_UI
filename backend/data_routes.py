"""
3rd Party Data Routes - FastAPI endpoints for external data integrations.

Provides REST API endpoints for:
- Economic Calendar (Econdb API)
- Market News (NewsAPI/Finnhub)
- RSS Feeds
- Technical Indicators
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Request, Query
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import requests

from backend.storage.storage_factory import get_storage

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/data", tags=["3rd Party Data"])

# ==================== MODELS ====================

class EconomicEvent(BaseModel):
    """Model for economic calendar event."""
    id: str
    time: str
    currency: str
    event: str
    impact: str  # high, medium, low
    forecast: Optional[str] = None
    previous: Optional[str] = None
    actual: Optional[str] = None


class EconomicCalendarResponse(BaseModel):
    """Response model for economic calendar."""
    events: List[EconomicEvent]
    total: int
    from_date: str
    to_date: str


class NewsArticle(BaseModel):
    """Model for news article."""
    id: str
    title: str
    description: Optional[str] = None
    source: str
    url: str
    published_at: str
    image_url: Optional[str] = None
    category: Optional[str] = None


class NewsResponse(BaseModel):
    """Response model for news articles."""
    articles: List[NewsArticle]
    total: int
    page: int
    page_size: int


class RSSFeed(BaseModel):
    """Model for RSS feed configuration."""
    id: str
    name: str
    url: str
    category: Optional[str] = None
    enabled: bool = True
    last_fetched: Optional[str] = None
    created_at: str


class RSSArticle(BaseModel):
    """Model for RSS article."""
    id: str
    feed_id: str
    feed_name: str
    title: str
    summary: Optional[str] = None
    link: str
    published: str


class IndicatorData(BaseModel):
    """Model for technical indicator data."""
    symbol: str
    timeframe: str
    timestamp: str
    indicators: Dict[str, Any]


# ==================== HELPER FUNCTIONS ====================

async def _get_integration_by_type(integration_type: str) -> Optional[Dict[str, Any]]:
    """Get API integration configuration by type."""
    storage = get_storage()
    integrations = await storage.get_api_integrations()
    
    for integration in integrations:
        if integration.get("type") == integration_type and integration.get("status") == "active":
            return integration
    
    return None


async def _fetch_econdb_events(
    api_key: str,
    base_url: str,
    from_date: str,
    to_date: str,
    currencies: Optional[List[str]] = None,
    impact: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Fetch economic events from Econdb API."""
    try:
        # Econdb API endpoint for economic calendar
        url = f"{base_url}/calendar"
        
        params = {
            "from": from_date,
            "to": to_date
        }
        
        if currencies:
            params["currencies"] = ",".join(currencies)
        
        if impact:
            params["impact"] = impact
        
        headers = {"Authorization": f"Bearer {api_key}"}
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("events", [])
        else:
            logger.error(f"Econdb API error: {response.status_code} - {response.text}")
            return []
    
    except Exception as e:
        logger.error(f"Error fetching Econdb events: {str(e)}")
        return []


async def _fetch_news_articles(
    api_key: str,
    base_url: str,
    category: Optional[str] = None,
    query: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    """Fetch news articles from NewsAPI or Finnhub."""
    try:
        if "newsapi" in base_url.lower():
            # NewsAPI
            url = f"{base_url}/top-headlines" if not query else f"{base_url}/everything"
            
            params = {
                "apiKey": api_key,
                "pageSize": page_size,
                "page": page
            }
            
            if category and not query:
                params["category"] = category
            
            if query:
                params["q"] = query
            else:
                params["category"] = category or "business"
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "articles": data.get("articles", []),
                    "total": data.get("totalResults", 0)
                }
        
        else:
            # Finnhub
            url = f"{base_url}/news"
            
            params = {
                "token": api_key,
                "category": category or "forex"
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                articles = response.json()
                return {
                    "articles": articles,
                    "total": len(articles)
                }
        
        logger.error(f"News API error: {response.status_code} - {response.text}")
        return {"articles": [], "total": 0}
    
    except Exception as e:
        logger.error(f"Error fetching news articles: {str(e)}")
        return {"articles": [], "total": 0}


# ==================== ECONOMIC CALENDAR ROUTES ====================

@router.get("/economic-calendar", response_model=EconomicCalendarResponse)
async def get_economic_calendar(
    request: Request,
    from_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    currencies: Optional[str] = Query(None, description="Comma-separated currency codes (e.g., USD,EUR,GBP)"),
    impact: Optional[str] = Query(None, description="Impact level: high, medium, low")
):
    """
    Get economic calendar events.
    
    Fetches events from Econdb API integration configured in settings.
    """
    try:
        # Get Econdb integration
        integration = await _get_integration_by_type("economic_calendar")
        
        if not integration:
            raise HTTPException(
                status_code=404,
                detail="No active economic calendar integration found. Please configure Econdb API in Settings."
            )
        
        # Default date range: today to 7 days ahead
        if not from_date:
            from_date = datetime.utcnow().strftime("%Y-%m-%d")
        if not to_date:
            to_date = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        # Parse currencies
        currency_list = currencies.split(",") if currencies else None
        
        # Fetch events
        api_key = integration.get("api_key", "")
        base_url = integration.get("base_url", "https://www.econdb.com/api")
        
        events_data = await _fetch_econdb_events(
            api_key=api_key,
            base_url=base_url,
            from_date=from_date,
            to_date=to_date,
            currencies=currency_list,
            impact=impact
        )
        
        # Transform to response model
        events = []
        for event in events_data:
            events.append(EconomicEvent(
                id=event.get("id", str(hash(event.get("event", "") + event.get("time", "")))),
                time=event.get("time", ""),
                currency=event.get("currency", ""),
                event=event.get("event", ""),
                impact=event.get("impact", "medium"),
                forecast=event.get("forecast"),
                previous=event.get("previous"),
                actual=event.get("actual")
            ))
        
        return EconomicCalendarResponse(
            events=events,
            total=len(events),
            from_date=from_date,
            to_date=to_date
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_economic_calendar: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch economic calendar: {str(e)}")


# ==================== MARKET NEWS ROUTES ====================

@router.get("/news", response_model=NewsResponse)
async def get_news(
    request: Request,
    category: Optional[str] = Query(None, description="News category (business, forex, crypto, etc.)"),
    query: Optional[str] = Query(None, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Get market news articles.

    Fetches articles from NewsAPI or Finnhub integration configured in settings.
    """
    try:
        # Get news integration
        integration = await _get_integration_by_type("news")

        if not integration:
            raise HTTPException(
                status_code=404,
                detail="No active news integration found. Please configure NewsAPI or Finnhub in Settings."
            )

        # Fetch articles
        api_key = integration.get("api_key", "")
        base_url = integration.get("base_url", "https://newsapi.org/v2")

        result = await _fetch_news_articles(
            api_key=api_key,
            base_url=base_url,
            category=category,
            query=query,
            page=page,
            page_size=page_size
        )

        # Transform to response model
        articles = []
        for idx, article in enumerate(result.get("articles", [])):
            # Handle both NewsAPI and Finnhub formats
            if "newsapi" in base_url.lower():
                # NewsAPI format
                articles.append(NewsArticle(
                    id=str(hash(article.get("url", "") + str(idx))),
                    title=article.get("title", ""),
                    description=article.get("description"),
                    source=article.get("source", {}).get("name", "Unknown"),
                    url=article.get("url", ""),
                    published_at=article.get("publishedAt", ""),
                    image_url=article.get("urlToImage"),
                    category=category
                ))
            else:
                # Finnhub format
                articles.append(NewsArticle(
                    id=str(article.get("id", idx)),
                    title=article.get("headline", ""),
                    description=article.get("summary"),
                    source=article.get("source", "Finnhub"),
                    url=article.get("url", ""),
                    published_at=datetime.fromtimestamp(article.get("datetime", 0)).isoformat() if article.get("datetime") else "",
                    image_url=article.get("image"),
                    category=article.get("category")
                ))

        return NewsResponse(
            articles=articles,
            total=result.get("total", len(articles)),
            page=page,
            page_size=page_size
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_news: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch news: {str(e)}")


# ==================== RSS FEED ROUTES ====================

@router.get("/rss/feeds")
async def get_rss_feeds(request: Request):
    """Get all configured RSS feeds."""
    try:
        storage = get_storage()
        feeds = await storage.get_rss_feeds()
        return {"feeds": feeds}
    except Exception as e:
        logger.error(f"Error in get_rss_feeds: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch RSS feeds: {str(e)}")


@router.post("/rss/feeds")
async def add_rss_feed(
    request: Request,
    name: str = Query(..., description="Feed name"),
    url: str = Query(..., description="Feed URL"),
    category: Optional[str] = Query(None, description="Feed category")
):
    """Add a new RSS feed."""
    try:
        storage = get_storage()
        feed = await storage.add_rss_feed({
            "name": name,
            "url": url,
            "category": category
        })
        return feed
    except Exception as e:
        logger.error(f"Error in add_rss_feed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add RSS feed: {str(e)}")


@router.delete("/rss/feeds/{feed_id}")
async def delete_rss_feed(request: Request, feed_id: str):
    """Delete an RSS feed."""
    try:
        storage = get_storage()
        success = await storage.remove_rss_feed(feed_id)
        if not success:
            raise HTTPException(status_code=404, detail="Feed not found")
        return {"success": True, "message": "Feed deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_rss_feed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete RSS feed: {str(e)}")


@router.get("/rss/articles")
async def get_rss_articles(
    request: Request,
    feed_id: Optional[str] = Query(None, description="Filter by feed ID"),
    limit: int = Query(50, ge=1, le=200, description="Maximum articles to return")
):
    """Get articles from RSS feeds."""
    try:
        import feedparser

        storage = get_storage()
        feeds = await storage.get_rss_feeds()

        # Filter by feed_id if provided
        if feed_id:
            feeds = [f for f in feeds if f.get("id") == feed_id]

        # Only fetch from enabled feeds
        feeds = [f for f in feeds if f.get("enabled", True)]

        all_articles = []

        for feed in feeds:
            try:
                # Parse RSS feed
                parsed = feedparser.parse(feed.get("url", ""))

                for entry in parsed.entries[:limit]:
                    all_articles.append({
                        "id": entry.get("id", entry.get("link", "")),
                        "feed_id": feed.get("id", ""),
                        "feed_name": feed.get("name", ""),
                        "title": entry.get("title", ""),
                        "summary": entry.get("summary", entry.get("description", "")),
                        "link": entry.get("link", ""),
                        "published": entry.get("published", entry.get("updated", ""))
                    })

                # Update last_fetched timestamp
                await storage.update_rss_feed(feed.get("id"), {
                    "last_fetched": datetime.utcnow().isoformat()
                })

            except Exception as e:
                logger.error(f"Error parsing feed {feed.get('name')}: {str(e)}")
                continue

        # Sort by published date (newest first)
        all_articles.sort(key=lambda x: x.get("published", ""), reverse=True)

        return {"articles": all_articles[:limit], "total": len(all_articles)}

    except Exception as e:
        logger.error(f"Error in get_rss_articles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch RSS articles: {str(e)}")


# ==================== TECHNICAL INDICATORS ROUTES ====================

@router.get("/indicators/{symbol}")
async def get_indicators(
    request: Request,
    symbol: str,
    timeframe: str = Query("H1", description="Timeframe (M1, M5, M15, M30, H1, H4, D1)")
):
    """
    Get technical indicator data for a symbol.

    Returns calculated indicators from MT5 data.
    """
    try:
        from backend.mt5_client import MT5Client
        from backend.ai.indicators import calculate_indicators

        mt5 = MT5Client()

        # Get historical bars
        bars = mt5.get_bars(symbol, timeframe, count=200)

        if not bars or len(bars) == 0:
            raise HTTPException(status_code=404, detail=f"No data available for {symbol}")

        # Calculate indicators
        indicators = calculate_indicators(bars)

        return IndicatorData(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=datetime.utcnow().isoformat(),
            indicators=indicators
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_indicators: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch indicators: {str(e)}")

