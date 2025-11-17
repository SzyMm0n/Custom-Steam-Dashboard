"""
FastAPI application for Custom Steam Dashboard server.
Provides REST API endpoints and manages background tasks for data collection.
"""
import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv

# Load .env FIRST, before any other imports that use environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from pydantic import ValidationError

from database.database import DatabaseManager, init_db, close_db
from services.steam_service import SteamClient
from services.deals_service import IsThereAnyDealClient
from scheduler import SchedulerManager
from validation import (
    SteamIDValidator,
    AppIDValidator,
    AppIDListValidator,
    VanityURLValidator
)
from security import require_auth, require_session_and_signed_request, rate_limit_key
from middleware import SignatureVerificationMiddleware
import auth_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize rate limiter (using client_id from JWT)
limiter = Limiter(key_func=rate_limit_key, default_limits=["100/minute"])

# Global instances
db: Optional[DatabaseManager] = None
steam_client: Optional[SteamClient] = None
deals_client: Optional[IsThereAnyDealClient] = None
scheduler_manager: Optional[SchedulerManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    global db, steam_client, deals_client, scheduler_manager

    # Startup
    logger.info("Starting Custom Steam Dashboard Server...")
    try:
        # Initialize database
        db = await init_db()
        logger.info("Database initialized")

        # Initialize Steam client
        steam_client = SteamClient()
        logger.info("Steam client initialized")

        # Initialize Deals client
        deals_client = IsThereAnyDealClient()
        logger.info("Deals client initialized")

        # Seed watchlist with top 100 most played games if empty
        await db.seed_watchlist(steam_client)

        # Initialize and start scheduler
        scheduler_manager = SchedulerManager(db, steam_client)
        scheduler_manager.start()
        logger.info("Scheduler started")

        logger.info("Server startup completed successfully")

        yield

    finally:
        # Shutdown
        logger.info("Shutting down Custom Steam Dashboard Server...")

        if scheduler_manager:
            scheduler_manager.shutdown()
            logger.info("Scheduler shut down")

        # Close deals client
        if deals_client:
            await deals_client.aclose()
            logger.info("Deals client closed")

        # Steam client cleanup happens automatically via BaseAsyncService context manager
            logger.info("Steam client closed")

        await close_db()
        logger.info("Database connection closed")

        logger.info("Server shutdown completed")


# Create FastAPI app
app = FastAPI(
    title="Custom Steam Dashboard API",
    description="REST API for Custom Steam Dashboard application",
    version="1.0.0",
    lifespan=lifespan
)

# Register rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add custom error handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": str(exc)}
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle value errors"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )

# Add CORS middleware (simplified for desktop GUI)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://127.0.0.1:*"],  # Only local connections
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Add signature verification middleware
app.add_middleware(SignatureVerificationMiddleware)

# Register authentication router
app.include_router(auth_routes.router)

# Protect API documentation endpoints
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html(payload: dict = Depends(require_auth)):
    """Protected Swagger UI documentation."""
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Custom Steam Dashboard API - Swagger UI",
        oauth2_redirect_url="/docs/oauth2-redirect",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_html(payload: dict = Depends(require_auth)):
    """Protected ReDoc documentation."""
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="Custom Steam Dashboard API - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    )

@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint(payload: dict = Depends(require_auth)):
    """Protected OpenAPI schema."""
    return get_openapi(
        title="Custom Steam Dashboard API",
        version="1.0.0",
        description="REST API for Custom Steam Dashboard application",
        routes=app.routes,
    )

# Disable default docs
app.docs_url = None
app.redoc_url = None
app.openapi_url = None


# ===== API Endpoints =====

@app.get("/")
@limiter.limit("60/minute")
async def root(request: Request):
    """Root endpoint"""
    return {
        "message": "Custom Steam Dashboard API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
@limiter.limit("120/minute")
async def health_check(request: Request):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected" if db and db.pool else "disconnected",
        "scheduler": "running" if scheduler_manager and scheduler_manager.scheduler.running else "stopped"
    }


# ===== Game Endpoints =====

@app.get("/api/games")
@limiter.limit("30/minute")
async def get_all_games(request: Request, client_id: str = Depends(require_session_and_signed_request)):
    """Get all games"""
    try:
        games = await db.get_all_games()
        return {"games": games}
    except Exception as e:
        logger.error(f"Error fetching games: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/games/{appid}")
@limiter.limit("60/minute")
async def get_game(appid: int, request: Request, client_id: str = Depends(require_session_and_signed_request)):
    """Get game details by appid"""
    try:
        # Validate appid
        validator = AppIDValidator(appid=appid)
        validated_appid = validator.appid

        game = await db.get_game(validated_appid)
        if not game:
            raise HTTPException(status_code=404, detail=f"Game with appid {validated_appid} not found")
        return game
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching game: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/games/tags/batch")
@limiter.limit("20/minute")
async def get_games_tags_batch(data: AppIDListValidator, request: Request, client_id: str = Depends(require_session_and_signed_request)):
    """
    Get genres and categories for multiple games in one request.

    Args:
        data: AppIDListValidator with list of Steam application IDs

    Returns:
        Dictionary mapping appid to tags data
    """
    try:
        tags_batch = await db.get_game_tags(data.appids)
        return {"tags": tags_batch}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())
    except Exception as e:
        logger.error(f"Error fetching games tags batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Steam API Endpoints =====

@app.get("/api/owned-games/{steamid}")
@limiter.limit("20/minute")
async def get_most_played_games(steamid: str, request: Request, client_id: str = Depends(require_session_and_signed_request)):
    """Get player owned games from Steam library"""
    try:
        # Validate steamid
        validator = SteamIDValidator(steamid=steamid)
        validated_steamid = validator.steamid

        games = await steam_client.get_player_owned_games(validated_steamid)
        return {"games": [game.model_dump() for game in games]}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())
    except Exception as e:
        logger.error(f"Error fetching most played games: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recently-played/{steamid}")
@limiter.limit("20/minute")
async def get_recently_played_games(steamid: str, request: Request, client_id: str = Depends(require_session_and_signed_request)):
    """Get player recently played games from Steam library"""
    try:
        # Validate steamid
        validator = SteamIDValidator(steamid=steamid)
        validated_steamid = validator.steamid

        games = await steam_client.get_recently_played_games(validated_steamid)
        return {"games": [game.model_dump() for game in games]}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())
    except Exception as e:
        logger.error(f"Error fetching recently played games: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/coming-soon")
@limiter.limit("30/minute")
async def get_coming_soon_games(request: Request, client_id: str = Depends(require_session_and_signed_request)):
    """Get coming soon games from Steam"""
    try:
        games = await steam_client.get_coming_soon_games()
        return {"games": [game.model_dump() for game in games]}
    except Exception as e:
        logger.error(f"Error fetching coming soon games: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/player-summary/{steamid}")
@limiter.limit("30/minute")
async def get_player_summary(steamid: str, request: Request, client_id: str = Depends(require_session_and_signed_request)):
    """Get Steam player summary"""
    try:
        # Validate steamid
        validator = SteamIDValidator(steamid=steamid)
        validated_steamid = validator.steamid

        summary = await steam_client.get_player_summary(validated_steamid)
        return summary
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())
    except Exception as e:
        logger.error(f"Error fetching player summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/resolve-vanity/{vanity_url:path}")
@limiter.limit("20/minute")
async def resolve_vanity_url(vanity_url: str, request: Request, client_id: str = Depends(require_session_and_signed_request)):
    """
    Resolve a Steam vanity URL or custom name to a Steam ID64.

    Args:
        vanity_url: Vanity name, custom URL, or full profile URL

    Examples:
        - /api/resolve-vanity/gaben
        - /api/resolve-vanity/my_custom_name
        - /api/resolve-vanity/https://steamcommunity.com/id/gaben
    """
    try:
        # Validate vanity URL
        validator = VanityURLValidator(vanity_url=vanity_url)
        validated_url = validator.vanity_url

        steam_id = await steam_client.resolve_vanity_url(validated_url)
        if steam_id:
            return {"success": True, "steamid": steam_id, "vanity_url": validated_url}
        else:
            raise HTTPException(status_code=404, detail=f"Could not resolve vanity URL: {validated_url}")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving vanity URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== UI Endpoints =====

@app.get("/api/current-players")
@limiter.limit("30/minute")
async def get_current_players_for_ui(request: Request, client_id: str = Depends(require_session_and_signed_request)):
    """Get current player counts for watchlist games for UI"""
    try:
        # Watchlist holds last fetched player counts for each game
        watchlist = await db.get_watchlist()
        return {"games": watchlist}
    except Exception as e:
        logger.error(f"Error fetching current players for UI: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/genres")
@limiter.limit("30/minute")
async def get_all_genres(request: Request, client_id: str = Depends(require_session_and_signed_request)):
    """Get all unique genres from games"""
    try:
        genres = await db.get_all_genres()
        return {"genres": genres}
    except Exception as e:
        logger.error(f"Error fetching genres: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/categories")
@limiter.limit("30/minute")
async def get_all_categories(request: Request, client_id: str = Depends(require_session_and_signed_request)):
    """Get all unique categories from games"""
    try:
        categories = await db.get_all_categories()
        return {"categories": categories}
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Deals Endpoints =====

@app.get("/api/deals/best")
@limiter.limit("20/minute")
async def get_best_deals(
    request: Request,
    limit: int = 20,
    min_discount: int = 20,
    client_id: str = Depends(require_session_and_signed_request)
):
    """
    Get best current game deals from IsThereAnyDeal.

    Checks prices for games in the watchlist database.

    Args:
        limit: Maximum number of deals to return (default: 20, max: 50)
        min_discount: Minimum discount percentage (default: 20)

    Returns:
        List of best deals with price and store information
    """
    try:
        # Validate parameters
        limit = min(max(1, limit), 50)  # Between 1 and 50
        min_discount = min(max(0, min_discount), 100)  # Between 0 and 100

        # Get list of games from watchlist to check for deals
        watchlist = await db.get_watchlist()
        game_appids = [game['appid'] for game in watchlist if 'appid' in game]

        # Create mapping of appid to game name for display
        game_names = {game['appid']: game['name'] for game in watchlist if 'appid' in game and 'name' in game}

        if not game_appids:
            return {
                "deals": [],
                "count": 0,
                "message": "No games in watchlist to check for deals"
            }

        logger.info(f"Checking deals for {len(game_appids)} games from watchlist")

        # Get deals for watchlist games
        deals = await deals_client.get_best_deals(
            limit=limit,
            min_discount=min_discount,
            game_appids=game_appids[:100],  # Limit to first 100 games
            game_names=game_names
        )

        return {
            "deals": [deal.model_dump() for deal in deals],
            "count": len(deals)
        }
    except Exception as e:
        logger.error(f"Error fetching best deals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/deals/game/{appid}")
@limiter.limit("30/minute")
async def get_game_deal(appid: int, request: Request, client_id: str = Depends(require_session_and_signed_request)):
    """
    Get price information and deals for a specific game by Steam AppID.

    First checks database for game details, then fetches from Steam API if not found.
    Returns best available deal from IsThereAnyDeal.

    Args:
        appid: Steam application ID

    Returns:
        Price information and best deal for the game
    """
    try:
        # Validate appid
        validator = AppIDValidator(appid=appid)
        validated_appid = validator.appid

        # First, try to get game from database
        game = await db.get_game(validated_appid)

        # If not in database, fetch from Steam API and add to database
        if not game:
            logger.info(f"Game {validated_appid} not in database, fetching from Steam API")
            game_details = await steam_client.get_game_details(validated_appid)

            if not game_details:
                raise HTTPException(
                    status_code=404,
                    detail=f"Game with appid {validated_appid} not found"
                )

            # Add game to database
            await db.upsert_game(game_details)
            logger.info(f"Added game {validated_appid} to database")

            # Fetch the newly added game
            game = await db.get_game(validated_appid)

        # Get deal information from IsThereAnyDeal
        deal = await deals_client.get_game_prices(validated_appid)

        if not deal:
            # Return game info without deal
            return {
                "game": game,
                "deal": None,
                "message": "No active deals found for this game"
            }

        return {
            "game": game,
            "deal": deal.model_dump()
        }

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching game deal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/deals/search")
@limiter.limit("30/minute")
async def search_game_deals(
    request: Request,
    title: str,
    client_id: str = Depends(require_session_and_signed_request)
):
    """
    Search for game deals by title.

    Args:
        title: Game title to search for

    Returns:
        Game information with current deal/price info
    """
    try:
        if not title or len(title.strip()) < 2:
            raise HTTPException(
                status_code=400,
                detail="Title must be at least 2 characters long"
            )

        # Search for game in ITAD
        game_info = await deals_client.search_game(title.strip())

        if not game_info:
            return {
                "found": False,
                "message": f"No game found matching '{title}'"
            }

        # Try to get Steam AppID from the game info
        steam_appid = None
        if "assets" in game_info and "steam" in game_info["assets"]:
            steam_appid_str = game_info["assets"]["steam"]
            if steam_appid_str and steam_appid_str.startswith("app/"):
                steam_appid = int(steam_appid_str.split("/")[1])

        # Get price information if we have Steam AppID
        deal = None
        if steam_appid:
            deal = await deals_client.get_game_prices(steam_appid)

        return {
            "found": True,
            "game": {
                "title": game_info.get("title"),
                "id": game_info.get("id"),
                "steam_appid": steam_appid
            },
            "deal": deal.model_dump() if deal else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching for game deals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/player-history/compare")
@limiter.limit("20/minute")
async def get_player_history_comparison(
    data: AppIDListValidator,
    request: Request,
    client_id: str = Depends(require_session_and_signed_request),
    days: float = 7,
    limit: int = 1000
):
    """
    Get player count history for multiple games for comparison.

    Args:
        data: AppIDListValidator with list of Steam application IDs
        days: Number of days of history to retrieve (default: 7, supports fractional days for hours)
        limit: Maximum number of records per game (default: 1000)

    Returns:
        Dictionary mapping appid to player count history
    """
    try:
        # Validate days parameter (supports fractional days for hour ranges)
        days = min(max(0.04, days), 30)  # Between 1 hour (0.04 days) and 30 days
        limit = min(max(10, limit), 5000)  # Between 10 and 5000 records

        history_data = {}

        for appid in data.appids:
            # Get player count history for each game
            history = await db.get_player_count_history(appid, limit=limit)

            # Filter by days if needed
            if days and history:
                import time
                cutoff_timestamp = int(time.time()) - int(days * 24 * 60 * 60)
                history = [
                    record for record in history
                    if record.get('time_stamp', 0) >= cutoff_timestamp
                ]

            # Get game info for name
            game = await db.get_game(appid)

            history_data[appid] = {
                "name": game.get("name", f"Game {appid}") if game else f"Game {appid}",
                "history": history
            }

        return {"games": history_data}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())
    except Exception as e:
        logger.error(f"Error fetching player history comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    import os
    uvicorn.run(app, host=os.getenv("HOST","0.0.0.0"), port=os.getenv("PORT",8000))

