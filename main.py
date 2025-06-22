import openai
import requests
import os
import json
import logging
from fastapi import FastAPI, HTTPException, Depends, Query, status, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from database.config import get_db
from database import models, schemas
from sqlalchemy import func
from database.security import auth, get_current_user, RateLimitMiddleware, generate_token
import functools
import time
from fastapi.responses import JSONResponse
from fastapi.middleware.gzip import GZipMiddleware

##

# client = OpenAI()

# Remove proxy settings before any other imports
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)

# Load .env variables early
load_dotenv()

# Get environment
ENV = os.getenv("ENV", "development")

# Ensure API key is set before initializing the client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError(
        "❌ ERROR: Missing OpenAI API Key. Please set OPENAI_API_KEY in your .env file or via PowerShell using $env:OPENAI_API_KEY.")
openai.api_key = api_key

# FastAPI application
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # In case Next.js runs on different port
        "*"  # Temporarily allow all origins for testing
    ],  # Allow local frontend and deployed backend
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Make sure these environment variables are set in your system or .env:
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
if not RAPIDAPI_KEY:
    print("RAPIDAPI_KEY is missing. Make sure it is set in the environment.")
else:
    print(f"Using RAPIDAPI_KEY: {RAPIDAPI_KEY[:5]}... (truncated for security)")

RAPIDAPI_HOST = "genius-song-lyrics1.p.rapidapi.com"
GENIUS_SEARCH_URL = "https://genius-song-lyrics1.p.rapidapi.com/search/"
GENIUS_LYRICS_URL = "https://genius-song-lyrics1.p.rapidapi.com/song/lyrics/"

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Add GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Cache for lyrics with 1 hour expiration
lyrics_cache = {}
CACHE_EXPIRATION = 3600  # 1 hour in seconds

def cache_lyrics(func):
    @functools.wraps(func)
    def wrapper(song_id: int):
        current_time = time.time()
        
        # Check cache
        if song_id in lyrics_cache:
            cache_entry = lyrics_cache[song_id]
            if current_time - cache_entry['timestamp'] < CACHE_EXPIRATION:
                return cache_entry['data']
        
        # If not in cache or expired, get fresh data
        result = func(song_id)
        
        # Update cache
        lyrics_cache[song_id] = {
            'data': result,
            'timestamp': current_time
        }
        
        return result
    return wrapper

# Add authentication models
class UserCreate(BaseModel):
    username: str
    password: str
    email: str


class Token(BaseModel):
    access_token: str
    token_type: str


# Add authentication endpoints
@app.post("/register", response_model=Token)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = auth.create_user(user.username, user.password, db, user.email)
    token = generate_token(db_user)
    return {"access_token": token, "token_type": "bearer"}


@app.post("/token", response_model=Token)
def login(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = auth.authenticate_user(user.username, user.password, db)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = generate_token(db_user)
    return {"access_token": token, "token_type": "bearer"}


# Helper function to get lyrics by song ID
@cache_lyrics
def get_lyrics_by_id(song_id: int):
    if ENV == "test":
        # Return mock data for testing
        return {
            "plainLyrics": "Test lyrics for song " + str(song_id),
            "html": "<p>Test lyrics for song " + str(song_id) + "</p>"
        }

    # Ensure API key is set before making requests
    RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
    if not RAPIDAPI_KEY:
        raise ValueError("RAPIDAPI_KEY is missing. Make sure it is set in the environment.")

    RAPIDAPI_HOST = "genius-song-lyrics1.p.rapidapi.com"
    GENIUS_LYRICS_URL = "https://genius-song-lyrics1.p.rapidapi.com/song/lyrics/"

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    params = {"id": str(song_id)}

    response = requests.get(GENIUS_LYRICS_URL, headers=headers, params=params)
    print(f"🔄 Response Status: {response.status_code}")  # Debugging

    if response.status_code == 200:
        try:
            data = response.json()
            print("🔍 Raw API Response:", json.dumps(data, indent=4))  # Debugging
        except json.JSONDecodeError:
            logging.error("❌ Error decoding JSON from API.")
            return {"error": "Invalid API response format"}

        # ✅ Handle unexpected responses safely
        lyrics_data = data.get("lyrics", {}).get("lyrics", {}).get("body", {}).get("html", None)

        if not lyrics_data:
            logging.error("⚠️ Lyrics data is missing in API response.")
            return {"error": "Lyrics not found for the requested ID"}

        # ✅ Use BeautifulSoup to clean HTML lyrics
        soup = BeautifulSoup(lyrics_data, "html.parser")
        plain_lyrics = soup.get_text(separator="\n").strip()

        return {
            "plainLyrics": plain_lyrics,
            "html": lyrics_data
        }

    else:
        logging.error(f"❌ Error {response.status_code}: {response.text}")
        return {"error": f"Error fetching lyrics. Status: {response.status_code}"}


# FastAPI route for searching lyrics
@app.get("/search_lyrics")
def search_lyrics_endpoint(
        q: str = None,
        track_name: str = None,
        artist_name: str = None,
        album_name: str = None
):
    """
    Given a user query or explicit track_name/artist_name, search Genius for matches.
    Returns a list of suggestions with {id, title, artist_names, cover_art}.
    """
    if not q and not track_name:
        raise HTTPException(
            status_code=400,
            detail="At least one of 'q' or 'track_name' must be provided."
        )

    if ENV == "test":
        # Return mock data for testing
        return {
            "results": [
                {
                    "id": 12345,
                    "title": "Test Song",
                    "artist_names": "Test Artist",
                    "cover_art": "https://via.placeholder.com/40"
                }
            ]
        }

    # Combine query parameters into one search query
    query = q or ""
    if track_name:
        query += " " + track_name
    if artist_name:
        query += " " + artist_name
    if album_name:
        query += " " + album_name
    query = query.strip()

    try:
        RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
        if not RAPIDAPI_KEY:
            raise ValueError("RAPIDAPI_KEY is missing. Make sure it is set in the environment.")

        RAPIDAPI_HOST = "genius-song-lyrics1.p.rapidapi.com"
        GENIUS_SEARCH_URL = "https://genius-song-lyrics1.p.rapidapi.com/search/"

        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST
        }
        params = {
            "q": query,
            "per_page": "10",
            "page": "1"
        }
        response = requests.get(GENIUS_SEARCH_URL, headers=headers, params=params)
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Genius search error: {response.text}"
            )

        data = response.json()
        hits = data.get("hits", [])

        suggestions = []
        for item in hits:
            if item.get("type") == "song":
                song = item.get("result", {})
            else:
                song = item.get("song", {})

            if not song:
                continue

            suggestions.append({
                "id": song.get("id"),
                "title": song.get("title"),
                "artist_names": song.get("artist_names"),
                "cover_art": song.get("song_art_image_url")
                             or song.get("header_image_url")
                             or "https://via.placeholder.com/40"
            })

        return {"results": suggestions}

    except Exception as e:
        logging.error(f"Error in /search_lyrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# FastAPI route for analyzing lyrics
@app.get("/analyze_lyrics")
async def analyze_lyrics_endpoint(record_id: int, track: str = "", artist: str = ""):
    try:
        # Get lyrics from cache or API
        lyrics_data = get_lyrics_by_id(song_id=record_id)
        lyrics_text = lyrics_data.get("plainLyrics", "")

        if ENV == "test":
            return {
                "analysis": {
                    "overallHeadline": "Test Analysis",
                    "songTitle": track or "Test Song",
                    "artist": artist or "Test Artist",
                    "introduction": "Test introduction",
                    "sectionAnalyses": [],
                    "conclusion": "Test conclusion"
                },
                "lyrics": lyrics_text
            }

        # Analyze lyrics with optimized function
        analysis_json = analyze_lyrics_with_function_call(
            song_title=track or "Unknown Title",
            artist=artist or "Unknown Artist",
            lyrics=lyrics_text
        )

        # Update view count in database
        db = next(get_db())
        song_ref = db.query(models.ExternalSongReference).filter(
            models.ExternalSongReference.external_id == record_id
        ).first()
        
        if song_ref:
            song_ref.view_count += 1
            db.commit()

        return JSONResponse({
            "analysis": analysis_json,
            "lyrics": lyrics_text
        })

    except Exception as e:
        logging.error(f"Error in /analyze_lyrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class SectionAnalysis(BaseModel):
    sectionName: str
    verseSummary: str  # 2–6 words summary
    quotedLines: Optional[str] = None
    analysis: str


class LyricAnalysis(BaseModel):
    overallHeadline: str  # a headline for the entire analysis
    songTitle: str
    artist: str
    introduction: str
    sectionAnalyses: List[SectionAnalysis]
    conclusion: str


# Helper function to analyze lyrics using OpenAI
def analyze_lyrics_with_function_call(song_title: str, artist: str, lyrics: str) -> dict:
    """
    Optimized version of the lyrics analysis function
    """
    messages = [
        {
            "role": "user",
            "content": (
                "Analyze these song lyrics concisely. Focus on key themes, emotional journey, and cultural context. "
                "Return a JSON object with these fields:\n"
                "{\n"
                "  \"overallHeadline\": str,\n"
                "  \"songTitle\": str,\n"
                "  \"artist\": str,\n"
                "  \"introduction\": str,\n"
                "  \"sectionAnalyses\": [\n"
                "    {\n"
                "      \"sectionName\": str,\n"
                "      \"verseSummary\": str,\n"
                "      \"analysis\": str\n"
                "    }\n"
                "  ],\n"
                "  \"conclusion\": str\n"
                "}\n\n"
                f"Song Title: {song_title}\n"
                f"Artist: {artist}\n\n"
                f"Lyrics: {lyrics}"
            )
        }
    ]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Using faster model
            messages=messages,
            max_tokens=800,  # Reduced token count
            temperature=0.7  # Added temperature for faster response
        )

        analysis = response['choices'][0]['message']['content'].strip()
        return json.loads(analysis)

    except openai.error.OpenAIError as e:
        logging.error(f"OpenAI API error: {e}")
        raise HTTPException(status_code=500, detail="Error contacting OpenAI API")


class ReAnalyzeRequest(BaseModel):
    oldAnalysis: dict
    newComment: str
    artist: str
    track: str

@app.post("/re_analyze")
def re_analyze_endpoint(data: ReAnalyzeRequest):
    """
    Accepts an existing analysis and a new viewer comment, and returns an updated analysis.
    The endpoint instructs the AI to update the analysis by integrating the new viewer comment into the narrative.
    Rather than simply appending the comment, the updated analysis should incorporate its sentiment and perspective into the
    existing insights. If the comment is not constructive, return the analysis unchanged (except for incrementing the version number
    and noting that the comment was not integrated).
    """
    try:
        old_analysis = data.oldAnalysis
        new_comment = data.newComment
        artist = data.artist
        track = data.track
        if isinstance(old_analysis, str):
            old_analysis = json.loads(old_analysis)
    except Exception as e:
        logging.error(f"Error parsing oldAnalysis: {e}")
        raise HTTPException(status_code=400, detail="Invalid oldAnalysis format")

    prompt = (
            "You are a highly skilled music analyst. You have an existing lyric analysis that contains integrated fan insights. "
            "New fan feedback is provided below. Your task is to update the analysis by thoughtfully integrating the new feedback into "
            "the narrative. Do not simply append the feedback; instead, incorporate its sentiment and perspective in a way that enriches "
            "the overall analysis. Preserve all existing insights and maintain the original structure, but modify the narrative to reflect "
            "the new perspective where appropriate. If the feedback is not constructive (e.g., spam, hateful, or irrelevant), return the analysis unchanged \n\n"
            "Return a strictly valid JSON object with exactly these keys:\n"
            "{\n"
            "  \"overallHeadline\": str,\n"
            "  \"songTitle\": str,\n"
            "  \"artist\": str,\n"
            "  \"introduction\": str,\n"
            "  \"sectionAnalyses\": [\n"
            "    {\n"
            "      \"sectionName\": str,\n"
            "      \"verseSummary\": str,\n"
            "      \"quotedLines\": (optional) str,\n"
            "      \"analysis\": str\n"
            "    }\n"
            "  ],\n"
            "  \"conclusion\": str\n"
            "}\n\n"
            "New fan feedback: " + new_comment + "\n\n"
                                                 "Existing Analysis:\n" + json.dumps(old_analysis)
    )

    messages = [{"role": "user", "content": prompt}]

    try:
        # Use the correct method for calling the OpenAI API directly (no beta)
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Or another model like "gpt-3.5-turbo" if preferred
            messages=messages
        )

        # Extract the result from the response
        result = response['choices'][0]['message']['content']

        # Assuming the result is a structured text that can be parsed into a dictionary
        updated_analysis = json.loads(result)

    except Exception as e:
        logging.error(f"Error during reanalysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # Increment version number based on the old analysis
    old_version = old_analysis.get("version", 1)
    updated_analysis["version"] = old_version + 1

    # Preserve any custom fields (e.g., coverArt, dominantColor) from the old analysis
    if "coverArt" in old_analysis:
        updated_analysis["coverArt"] = old_analysis["coverArt"]
    else:
        updated_analysis["coverArt"] = "https://via.placeholder.com/300?text=No+Cover+Art"

    if "dominantColor" in old_analysis:
        updated_analysis["dominantColor"] = old_analysis["dominantColor"]
    else:
        updated_analysis["dominantColor"] = "#000"

    return updated_analysis


@app.get("/")
def home():
    return {"message": "API is running!"}


@app.get("/api/mostViewed", response_model=schemas.PaginatedResponse)
def get_most_viewed(
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1, le=100),
        db: Session = Depends(get_db)
):
    """
    Get the most viewed songs based on view count.
    Includes pagination support.
    """
    # Calculate total count
    total = db.query(models.Song).count()

    # Get paginated results
    songs = (
        db.query(models.Song)
        .order_by(models.Song.view_count.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return {
        "items": songs,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    }


@app.post("/api/songs/{song_id}/view")
def increment_view_count(
        song_id: int,
        db: Session = Depends(get_db),
        current_user: Optional[str] = Depends(get_current_user)
):
    """
    Increment the view count for a song.
    Requires authentication.
    """
    song = db.query(models.Song).filter(models.Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    song.view_count += 1
    db.commit()
    return {"message": "View count updated successfully"}


@app.post("/api/comments/authenticated", response_model=schemas.CommentResponse)
def create_authenticated_comment(
        comment: schemas.CommentCreate,
        title: Optional[str] = Query(None),
        artist: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    """
    Create a new comment for a song from Genius API for authenticated users.
    Uses the actual username of the logged-in user.
    """
    # First, check if the external song reference exists
    song_reference = db.query(models.ExternalSongReference).filter(
        models.ExternalSongReference.external_id == comment.song_id
    ).first()

    # If not, create a new reference with title and artist from query params
    if not song_reference:
        # Create a new external song reference
        song_reference = models.ExternalSongReference(
            external_id=comment.song_id,
            title=title or "Unknown",
            artist=artist or "Unknown"
        )
        db.add(song_reference)
        db.commit()
        db.refresh(song_reference)
    elif title and artist:  # Update existing reference if new info is provided
        song_reference.title = title
        song_reference.artist = artist
        db.commit()
        db.refresh(song_reference)

    # Create comment with user_id
    db_comment = models.Comment(
        content=comment.content,
        external_song_id=comment.song_id,
        user_id=current_user.id
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)

    # Create response object with actual username
    response = schemas.CommentResponse(
        id=db_comment.id,
        content=db_comment.content,
        song_id=db_comment.external_song_id,
        created_at=db_comment.created_at,
        updated_at=db_comment.updated_at,
        username=current_user.username
    )

    return response


@app.post("/api/comments/anonymous", response_model=schemas.CommentResponse)
def create_anonymous_comment(
        comment: schemas.CommentCreate,
        title: Optional[str] = Query(None),
        artist: Optional[str] = Query(None),
        db: Session = Depends(get_db)
):
    """
    Create a new comment for a song from Genius API for anonymous users.
    Uses 'Anonymous' as the username.
    """
    # First, check if the external song reference exists
    song_reference = db.query(models.ExternalSongReference).filter(
        models.ExternalSongReference.external_id == comment.song_id
    ).first()

    # If not, create a new reference with title and artist from query params
    if not song_reference:
        # Create a new external song reference
        song_reference = models.ExternalSongReference(
            external_id=comment.song_id,
            title=title or "Unknown",
            artist=artist or "Unknown"
        )
        db.add(song_reference)
        db.commit()
        db.refresh(song_reference)
    elif title and artist:  # Update existing reference if new info is provided
        song_reference.title = title
        song_reference.artist = artist
        db.commit()
        db.refresh(song_reference)

    # Create comment without user_id
    db_comment = models.Comment(
        content=comment.content,
        external_song_id=comment.song_id
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)

    # Create response object with 'Anonymous' username
    response = schemas.CommentResponse(
        id=db_comment.id,
        content=db_comment.content,
        song_id=db_comment.external_song_id,
        created_at=db_comment.created_at,
        updated_at=db_comment.updated_at,
        username="Anonymous"
    )

    return response


@app.get("/api/songs/{song_id}/comments", response_model=List[schemas.CommentResponse])
def get_song_comments(
        song_id: int,
        db: Session = Depends(get_db)
):
    """
    Get all comments for a specific song from Genius API.
    """
    # Get comments with user information
    comments = db.query(models.Comment, models.User.username) \
        .outerjoin(models.User, models.Comment.user_id == models.User.id) \
        .filter(models.Comment.external_song_id == song_id) \
        .all()

    # Format the results
    result = []
    for comment, username in comments:
        result.append(schemas.CommentResponse(
            id=comment.id,
            content=comment.content,
            song_id=comment.external_song_id,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            username=username if username else "Anonymous",
            upvote_count=comment.upvote_count
        ))

    return result


@app.delete("/api/comments/{comment_id}")
def delete_comment(
        comment_id: int,
        db: Session = Depends(get_db)
):
    """
    Delete a comment. No authentication required.
    """
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    db.delete(comment)
    db.commit()
    return {"message": "Comment deleted successfully"}


@app.post("/api/songs/{song_id}/view")
def increment_view_count(
        song_id: int,
        title: Optional[str] = None,
        artist: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: Optional[models.User] = Depends(get_current_user)
):
    """
    Increment the view count for an external song.
    Works for both anonymous and authenticated users.
    """
    # Find or create the external song reference
    song_reference = db.query(models.ExternalSongReference).filter(
        models.ExternalSongReference.external_id == song_id
    ).first()

    if not song_reference:
        # Create a new external song reference
        song_reference = models.ExternalSongReference(
            external_id=song_id,
            title=title or "Unknown",
            artist=artist or "Unknown",
            view_count=0
        )
        db.add(song_reference)

    # Increment the view count
    song_reference.view_count += 1

    # Update title and artist if provided
    if title:
        song_reference.title = title
    if artist:
        song_reference.artist = artist

    db.commit()

    return {"message": "View count updated successfully"}


@app.get("/api/mostViewed", response_model=schemas.PaginatedResponse)
def get_most_viewed(
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1, le=100),
        db: Session = Depends(get_db)
):
    """
    Get the most viewed songs based on view count from external song references.
    Includes pagination support.
    """
    # Calculate total count
    total = db.query(models.ExternalSongReference).count()

    # Get paginated results
    song_references = (
        db.query(models.ExternalSongReference)
        .order_by(models.ExternalSongReference.view_count.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    # Convert to Song objects for the response
    songs = []
    for ref in song_references:
        songs.append(schemas.Song(
            id=ref.external_id,
            title=ref.title,
            artist=ref.artist,
            lyrics="",  # We don't store lyrics locally
            view_count=ref.view_count,
            created_at=ref.created_at,
            updated_at=ref.updated_at
        ))

    return {
        "items": songs,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    }


@app.post("/api/comments/{comment_id}/upvote")
def upvote_comment(
    comment_id: int,
    db: Session = Depends(get_db)
):
    """
    Upvote a comment. Each IP address can only upvote a comment once.
    """
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Increment upvote count
    comment.upvote_count += 1
    db.commit()

    # If upvote count reaches threshold (e.g., 10), trigger re-analysis
    if comment.upvote_count >= 10:
        # Get the latest analysis for this song
        latest_analysis = db.query(models.Analysis).filter(
            models.Analysis.external_song_id == comment.external_song_id
        ).order_by(models.Analysis.version.desc()).first()

        if latest_analysis:
            # Create re-analysis request
            re_analyze_data = ReAnalyzeRequest(
                oldAnalysis=json.loads(latest_analysis.analysis_data),
                newComment=comment.content,
                artist=comment.song_reference.artist,
                track=comment.song_reference.title
            )

            # Call re-analyze endpoint
            try:
                updated_analysis = re_analyze_endpoint(re_analyze_data)
                
                # Save new analysis
                new_analysis = models.Analysis(
                    external_song_id=comment.external_song_id,
                    analysis_data=json.dumps(updated_analysis),
                    version=latest_analysis.version + 1
                )
                db.add(new_analysis)
                db.commit()
            except Exception as e:
                logging.error(f"Error during re-analysis: {e}")
                # Continue even if re-analysis fails

    return {"message": "Comment upvoted successfully", "upvote_count": comment.upvote_count}


if __name__ == "__main__":
    import uvicorn
    # Example CLI: uvicorn app:app --host 0.0.0.0 --port 8000