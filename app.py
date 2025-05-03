import openai
import requests
import os
import json
import logging
from fastapi import FastAPI, HTTPException
from bs4 import BeautifulSoup
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional

##

# client = OpenAI()

# Remove proxy settings before any other imports
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)

# Load .env variables early
load_dotenv()

# Ensure API key is set before initializing the client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ ERROR: Missing OpenAI API Key. Please set OPENAI_API_KEY in your .env file or via PowerShell using $env:OPENAI_API_KEY.")
openai.api_key = api_key

# FastAPI application
app = FastAPI()

# Make sure these environment variables are set in your system or .env:
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
if not RAPIDAPI_KEY:
    print("RAPIDAPI_KEY is missing. Make sure it is set in the environment.")
else:
    print(f"Using RAPIDAPI_KEY: {RAPIDAPI_KEY[:5]}... (truncated for security)")

RAPIDAPI_HOST = "genius-song-lyrics1.p.rapidapi.com"
GENIUS_SEARCH_URL = "https://genius-song-lyrics1.p.rapidapi.com/search/"
GENIUS_LYRICS_URL = "https://genius-song-lyrics1.p.rapidapi.com/song/lyrics/"

# Helper function to get lyrics by song ID
def get_lyrics_by_id(song_id: int):
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
def analyze_lyrics_endpoint(record_id: int, track: str = "", artist: str = ""):
    try:
        lyrics_data = get_lyrics_by_id(song_id=record_id)
        lyrics_text = lyrics_data.get("plainLyrics", "")

        analysis_json = analyze_lyrics_with_function_call(
            song_title=track or "Unknown Title",
            artist=artist or "Unknown Artist",
            lyrics=lyrics_text
        )

        return {
            "analysis": analysis_json,
            "lyrics": lyrics_text
        }

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
    This function generates a cohesive lyric analysis for the song using the OpenAI API.
    """
    messages = [
        {
            "role": "user",
            "content": (
                "You are a highly skilled music analyst. Your task is to write a flowing, narrative-style lyric analysis "
                "that feels deeply connected to the song’s emotional journey and cultural context. The language should "
                "adapt naturally to the track’s vibe—whether it’s a gentle, reflective piece or an upbeat, electrifying anthem—"
                "and speak to a broad range of listeners without resorting to complex jargon or first-person pronouns.\n\n"

                "Structure & Requirements:\n\n"

                "1. **Overall Headline**:\n"
                "   - Begin the final output with a concise, striking phrase that captures the song’s primary essence.\n\n"

                "2. **Introduction & Hook**:\n"
                "   - Start with a captivating opening that immediately sets the emotional or conceptual tone.\n"
                "   - Reference any standout imagery or initial themes found in the lyrics.\n\n"

                "3. **Narrative Flow**:\n"
                "   - Guide the reader through the song’s progression in a natural storyline, mentioning relevant sections (Intro, Verse, Chorus, Bridge, etc.).\n"
                "   - Incorporate at least one direct quote from each unique section, weaving it seamlessly into the analysis rather than isolating it.\n"
                "   - Provide a 2–6 word 'verseSummary' for each section that highlights its main idea.\n"
                "   - Emphasize changes in perspective or mood, ensuring the write-up has a sense of forward motion.\n\n"

                "4. **Contextual & Cultural Nuance**:\n"
                "   - Bring depth to the analysis by noting cultural, historical, or social references in the lyrics where relevant.\n"
                "   - Connect these references to broader human experiences—love, transformation, ambition, etc.—to ground the song’s impact in shared realities.\n\n"

                "5. **Emotional Arc & Theme Development**:\n"
                "   - Explore how each part of the song builds upon the previous one, gradually revealing the emotional core.\n"
                "   - Discuss any notable shifts in tone, lyrical perspective, or intensity that deepen the narrative.\n"
                "   - Avoid first-person pronouns, maintaining a universal viewpoint that invites listeners of all backgrounds to engage.\n\n"

                "6. **Conclusion & Reflection**:\n"
                "   - Wrap up with a unifying reflection that ties the entire journey together.\n"
                "   - Offer a memorable insight or takeaway, showing how the song’s message resonates beyond the music itself.\n\n"

                "7. **Final Output Format**:\n"
                "   - Return one strictly valid JSON object matching the following schema:\n"
                "     {\n"
                "       \"overallHeadline\": str,\n"
                "       \"songTitle\": str,\n"
                "       \"artist\": str,\n"
                "       \"introduction\": str,\n"
                "       \"sectionAnalyses\": [\n"
                "         {\n"
                "           \"sectionName\": str,\n"
                "           \"verseSummary\": str,\n"
                "           \"quotedLines\": (optional) str,\n"
                "           \"analysis\": str\n"
                "         }, ...\n"
                "       ],\n"
                "       \"conclusion\": str\n"
                "     }\n\n"
                "   - Include each field exactly as listed, with no extra keys or commentary.\n\n"

                "Incorporate these instructions to create a highly engaging, context-rich analysis that reads like a journey "
                "through the song’s evolving landscape. Use vivid yet accessible language that resonates with a wide audience."
            )
        },
        {
            "role": "user",
            "content": (
                f"Song Title: {song_title}\n"
                f"Artist: {artist}\n\n"
                f"Lyrics: {lyrics}"
            )
        }
    ]

    try:
        # Correctly using the OpenAI API for chat-based completions
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Or use "gpt-3.5-turbo" if you prefer
            messages=messages,
            max_tokens=1500  # Adjust this based on how much output you need
        )

        # Extract and return the result from OpenAI's response
        analysis = response['choices'][0]['message']['content'].strip()
        return {
            "overallHeadline": "Song Analysis",
            "songTitle": song_title,
            "artist": artist,
            "introduction": "A deep dive into the song's lyrics, capturing its essence and emotional flow.",
            "sectionAnalyses": [],  # You can extend this if you need detailed section-by-section analysis
            "conclusion": analysis
        }

    except openai.error.OpenAIError as e:
        logging.error(f"OpenAI API error: {e}")
        raise HTTPException(status_code=500, detail="Error contacting OpenAI API")


@app.post("/re_analyze")
def re_analyze_endpoint(data: dict):
    """
    Accepts an existing analysis and a new viewer comment, and returns an updated analysis.
    The endpoint instructs the AI to update the analysis by integrating the new viewer comment into the narrative.
    Rather than simply appending the comment, the updated analysis should incorporate its sentiment and perspective into the
    existing insights. If the comment is not constructive, return the analysis unchanged (except for incrementing the version number
    and noting that the comment was not integrated).
    
    Expected input:
    {
      "oldAnalysis": { ... },  // JSON object following the LyricAnalysis schema plus any extras
      "newComment": "viewer comment text",
      "artist": "Artist Name",
      "track": "Track Title"
    }
    """
    try:
        old_analysis = data.get("oldAnalysis", {})
        new_comment = data.get("newComment", "")
        artist = data.get("artist", "")
        track = data.get("track", "")
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


if __name__ == "__main__":
    import uvicorn
    # Example CLI: uvicorn app:app --host 0.0.0.0 --port 8000
