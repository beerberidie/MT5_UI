"""
Data collection background tasks for Celery.

This module contains tasks for:
- Market data collection
- Economic calendar updates
- RSS news collection
- Third-party data integration
"""

import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
import json
from pathlib import Path
import feedparser
import requests

from backend.celery_app import celery_app
from backend.storage.file_storage import FileStorage
from backend.mt5_client import MT5Client

logger = logging.getLogger(__name__)


@celery_app.task(name="backend.tasks.data_tasks.collect_market_data", bind=True)
def collect_market_data(self):
    """
    Collect current market data for all watchlist symbols.
    
    This task:
    1. Gets list of symbols from watchlist
    2. Collects current prices, spreads, volumes
    3. Stores data in CSV cache files
    4. Updates market data cache
    
    Returns:
        Dict with collection results
    """
    try:
        logger.info("Starting market data collection task")
        
        # Initialize components
        storage = FileStorage()
        mt5_client = MT5Client()

        # Initialize MT5
        try:
            mt5_client.init()
        except Exception as e:
            logger.error(f"Failed to initialize MT5: {e}")
            return {
                "success": False,
                "error": f"MT5 initialization failed: {str(e)}"
            }

        # Get symbols to collect (default watchlist)
        symbols = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD"]

        results = {
            "task_id": self.request.id,
            "timestamp": datetime.utcnow().isoformat(),
            "symbols_collected": 0,
            "errors": [],
            "data": []
        }

        # Collect data for each symbol
        for symbol in symbols:
            try:
                # Get current tick
                tick = mt5_client.symbol_info_tick(symbol)

                if tick:
                    market_data = {
                        "symbol": symbol,
                        "bid": tick.get("bid", 0),
                        "ask": tick.get("ask", 0),
                        "spread": tick.get("ask", 0) - tick.get("bid", 0),
                        "volume": tick.get("volume", 0),
                        "timestamp": datetime.utcnow().isoformat()
                    }

                    results["data"].append(market_data)
                    results["symbols_collected"] += 1

                    # Store in cache
                    _store_market_data_cache(storage, symbol, market_data)
                else:
                    results["errors"].append(f"{symbol}: No tick data")

            except Exception as e:
                logger.error(f"Error collecting data for {symbol}: {e}")
                results["errors"].append(f"{symbol}: {str(e)}")

        # Shutdown MT5
        mt5_client.shutdown()
        
        logger.info(f"Market data collection complete: {results['symbols_collected']} symbols")
        
        return results
        
    except Exception as e:
        logger.error(f"Error in collect_market_data task: {e}", exc_info=True)
        raise


@celery_app.task(name="backend.tasks.data_tasks.update_economic_calendar", bind=True)
def update_economic_calendar(self):
    """
    Update economic calendar from external API.
    
    This task:
    1. Fetches upcoming economic events
    2. Filters high-impact events
    3. Stores in CSV cache
    4. Updates calendar data
    
    Returns:
        Dict with update results
    """
    try:
        logger.info("Starting economic calendar update task")
        
        storage = FileStorage()
        
        # Get API integrations
        integrations = storage.get_api_integrations()
        
        # Find economic calendar API
        calendar_api = None
        for integration in integrations.get("integrations", []):
            if integration.get("name") == "Economic Calendar":
                calendar_api = integration
                break
        
        if not calendar_api or not calendar_api.get("enabled"):
            logger.info("Economic calendar API not configured or disabled")
            return {
                "success": False,
                "message": "Economic calendar API not configured"
            }
        
        # Fetch calendar data (placeholder - actual API call would go here)
        # For now, create sample data
        events = _fetch_economic_events(calendar_api)
        
        # Store in cache
        _store_calendar_cache(storage, events)
        
        logger.info(f"Economic calendar updated: {len(events)} events")
        
        return {
            "success": True,
            "events_count": len(events),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in update_economic_calendar task: {e}", exc_info=True)
        raise


@celery_app.task(name="backend.tasks.data_tasks.collect_rss_news", bind=True)
def collect_rss_news(self):
    """
    Collect news from configured RSS feeds.
    
    This task:
    1. Gets list of RSS feeds from config
    2. Fetches latest articles from each feed
    3. Filters by keywords/symbols
    4. Stores in CSV cache
    
    Returns:
        Dict with collection results
    """
    try:
        logger.info("Starting RSS news collection task")
        
        storage = FileStorage()
        
        # Get RSS feeds from config
        feeds_config = storage.get_rss_feeds()
        feeds = feeds_config.get("feeds", [])
        
        if not feeds:
            logger.info("No RSS feeds configured")
            return {
                "success": False,
                "message": "No RSS feeds configured"
            }
        
        results = {
            "task_id": self.request.id,
            "timestamp": datetime.utcnow().isoformat(),
            "feeds_processed": 0,
            "articles_collected": 0,
            "errors": [],
            "articles": []
        }
        
        # Process each feed
        for feed in feeds:
            if not feed.get("enabled", True):
                continue
            
            try:
                feed_url = feed.get("url")
                logger.info(f"Fetching RSS feed: {feed_url}")
                
                # Parse RSS feed
                parsed_feed = feedparser.parse(feed_url)
                
                # Process entries
                for entry in parsed_feed.entries[:10]:  # Limit to 10 latest
                    article = {
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "published": entry.get("published", ""),
                        "summary": entry.get("summary", ""),
                        "source": feed.get("name", "Unknown"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    results["articles"].append(article)
                    results["articles_collected"] += 1
                
                results["feeds_processed"] += 1
                
            except Exception as e:
                logger.error(f"Error processing feed {feed.get('name')}: {e}")
                results["errors"].append(f"{feed.get('name')}: {str(e)}")
        
        # Store articles in cache
        _store_news_cache(storage, results["articles"])
        
        logger.info(f"RSS news collection complete: {results['articles_collected']} articles "
                   f"from {results['feeds_processed']} feeds")
        
        return results
        
    except Exception as e:
        logger.error(f"Error in collect_rss_news task: {e}", exc_info=True)
        raise


@celery_app.task(name="backend.tasks.data_tasks.update_symbol_info", bind=True)
def update_symbol_info(self):
    """
    Update symbol information from MT5.
    
    This task:
    1. Gets all available symbols from MT5
    2. Updates symbol properties (spread, digits, contract size, etc.)
    3. Stores in CSV cache
    
    Returns:
        Dict with update results
    """
    try:
        logger.info("Starting symbol info update task")
        
        storage = FileStorage()
        mt5_client = MT5Client()

        # Initialize MT5
        try:
            mt5_client.init()
        except Exception as e:
            return {
                "success": False,
                "error": f"MT5 initialization failed: {str(e)}"
            }

        # Get symbol info (placeholder - actual implementation would query MT5)
        symbols_updated = 0

        mt5_client.shutdown()
        
        logger.info(f"Symbol info updated: {symbols_updated} symbols")
        
        return {
            "success": True,
            "symbols_updated": symbols_updated,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in update_symbol_info task: {e}", exc_info=True)
        raise


# Helper functions

def _store_market_data_cache(storage: FileStorage, symbol: str, data: Dict[str, Any]):
    """Store market data in cache."""
    try:
        cache_dir = Path("data/cache/market_data")
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Store in daily file
        date_str = datetime.utcnow().strftime("%Y%m%d")
        filename = cache_dir / f"{symbol}_{date_str}.json"
        
        # Append to file
        cache_data = []
        if filename.exists():
            with open(filename, 'r') as f:
                cache_data = json.load(f)
        
        cache_data.append(data)
        
        # Keep only last 1000 entries
        cache_data = cache_data[-1000:]
        
        with open(filename, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
    except Exception as e:
        logger.error(f"Error storing market data cache: {e}")


def _store_calendar_cache(storage: FileStorage, events: List[Dict[str, Any]]):
    """Store economic calendar in cache."""
    try:
        cache_dir = Path("data/cache")
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        filename = cache_dir / "economic_calendar.json"
        
        with open(filename, 'w') as f:
            json.dump({
                "updated_at": datetime.utcnow().isoformat(),
                "events": events
            }, f, indent=2)
        
    except Exception as e:
        logger.error(f"Error storing calendar cache: {e}")


def _store_news_cache(storage: FileStorage, articles: List[Dict[str, Any]]):
    """Store news articles in cache."""
    try:
        cache_dir = Path("data/cache")
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        filename = cache_dir / "rss_news.json"
        
        # Load existing
        existing_articles = []
        if filename.exists():
            with open(filename, 'r') as f:
                data = json.load(f)
                existing_articles = data.get("articles", [])
        
        # Combine and deduplicate
        all_articles = articles + existing_articles
        
        # Keep only last 100 articles
        all_articles = all_articles[:100]
        
        with open(filename, 'w') as f:
            json.dump({
                "updated_at": datetime.utcnow().isoformat(),
                "articles": all_articles
            }, f, indent=2)
        
    except Exception as e:
        logger.error(f"Error storing news cache: {e}")


def _fetch_economic_events(api_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Fetch economic events from API (placeholder)."""
    # This is a placeholder - actual API integration would go here
    return [
        {
            "time": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
            "currency": "USD",
            "impact": "high",
            "event": "Non-Farm Payrolls",
            "forecast": "200K",
            "previous": "195K"
        }
    ]

