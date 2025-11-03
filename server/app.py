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

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database.database import DatabaseManager, init_db, close_db
from services.steam_service import SteamClient
from scheduler import SchedulerManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
db: Optional[DatabaseManager] = None
steam_client: Optional[SteamClient] = None
scheduler_manager: Optional[SchedulerManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    global db, steam_client, scheduler_manager

    # Startup
    logger.info("Starting Custom Steam Dashboard Server...")

    try:
        # Initialize database
        db = await init_db()
        logger.info("Database initialized")

        # Initialize Steam client
        steam_client = SteamClient()
        logger.info("Steam client initialized")

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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== API Endpoints =====

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Custom Steam Dashboard API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected" if db and db.pool else "disconnected",
        "scheduler": "running" if scheduler_manager and scheduler_manager.scheduler.running else "stopped"
    }


# ===== Watchlist Endpoints =====

@app.get("/api/watchlist")
async def get_watchlist():
    """Get all games in the watchlist"""
    try:
        watchlist = await db.get_watchlist()
        return {"watchlist": watchlist}
    except Exception as e:
        logger.error(f"Error fetching watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Game Endpoints =====

@app.get("/api/games")
async def get_all_games():
    """Get all games"""
    try:
        games = await db.get_all_games()
        return {"games": games}
    except Exception as e:
        logger.error(f"Error fetching games: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/games/{appid}")
async def get_game(appid: int):
    """Get game details by appid"""
    try:
        game = await db.get_game(appid)
        if not game:
            raise HTTPException(status_code=404, detail=f"Game with appid {appid} not found")
        return game
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching game: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/games/{appid}/current-players")
async def get_current_players(appid: int):
    """Get current player count for a game from Steam API"""
    try:
        player_count = await steam_client.get_player_count(appid)
        return {
            "appid": appid,
            "player_count": player_count.player_count
        }
    except Exception as e:
        logger.error(f"Error fetching current player count: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Steam API Endpoints =====

@app.get("/api/steam/most-played")
async def get_most_played_games():
    """Get most played games from Steam"""
    try:
        games = await steam_client.get_most_played_games()
        return {"games": [game.model_dump() for game in games]}
    except Exception as e:
        logger.error(f"Error fetching most played games: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/steam/coming-soon")
async def get_coming_soon_games():
    """Get coming soon games from Steam"""
    try:
        games = await steam_client.get_coming_soon_games()
        return {"games": [game.model_dump() for game in games]}
    except Exception as e:
        logger.error(f"Error fetching coming soon games: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

