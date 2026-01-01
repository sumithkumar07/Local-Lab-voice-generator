"""
Text-to-Speech API Server using Kokoro TTS
A lightweight, high-quality voice generator for YouTube narration
"""

import os
import uuid
import time
import asyncio
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import soundfile as sf
import numpy as np
from hardware import HardwareDetector
from backend.engine import engine_manager

# System Status (Cached)
SYSTEM_STATUS = {}

# Create output directories
OUTPUT_DIR = Path(__file__).parent / "audio_output"
OUTPUT_DIR.mkdir(exist_ok=True)
PREVIEW_DIR = Path(__file__).parent / "voice_previews"
PREVIEW_DIR.mkdir(exist_ok=True)

# Auto-cleanup settings (1 hour = 3600 seconds)
CLEANUP_AGE_SECONDS = 3600
CLEANUP_INTERVAL_SECONDS = 300  # Check every 5 minutes

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown"""
    # Startup
    cleanup_old_files()
    cleanup_thread = threading.Thread(target=cleanup_scheduler, daemon=True)
    cleanup_thread.start()
    
    # Run Hardware Check
    global SYSTEM_STATUS
    print("🔍 Analyzing System Hardware...")
    SYSTEM_STATUS = HardwareDetector.analyze_system()
    print(f"🖥️  System Status: {SYSTEM_STATUS['message']}")
    
    yield
    # Shutdown (if needed)

# Initialize FastAPI
app = FastAPI(
    title="Voice Generator API",
    description="Generate natural-sounding narration for YouTube videos",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# pipelines = {}

# Available voices with descriptions
VOICES = {
    # American English - Female
    "af_heart": {"name": "Heart", "gender": "Female", "accent": "American", "style": "Warm & Friendly", "lang": "a"},
    "af_bella": {"name": "Bella", "gender": "Female", "accent": "American", "style": "Elegant", "lang": "a"},
    "af_nicole": {"name": "Nicole", "gender": "Female", "accent": "American", "style": "Professional", "lang": "a"},
    "af_sarah": {"name": "Sarah", "gender": "Female", "accent": "American", "style": "Casual", "lang": "a"},
    "af_sky": {"name": "Sky", "gender": "Female", "accent": "American", "style": "Bright", "lang": "a"},
    # American English - Male
    "am_adam": {"name": "Adam", "gender": "Male", "accent": "American", "style": "Confident", "lang": "a"},
    "am_michael": {"name": "Michael", "gender": "Male", "accent": "American", "style": "Narrator", "lang": "a"},
    "am_eric": {"name": "Eric", "gender": "Male", "accent": "American", "style": "Deep", "lang": "a"},
    "am_fenrir": {"name": "Fenrir", "gender": "Male", "accent": "American", "style": "Dramatic", "lang": "a"},
    "am_liam": {"name": "Liam", "gender": "Male", "accent": "American", "style": "Youthful", "lang": "a"},
    "am_onyx": {"name": "Onyx", "gender": "Male", "accent": "American", "style": "Rich", "lang": "a"},
    "am_puck": {"name": "Puck", "gender": "Male", "accent": "American", "style": "Playful", "lang": "a"},
    "am_santa": {"name": "Santa", "gender": "Male", "accent": "American", "style": "Jolly", "lang": "a"},
    # British English - Female
    "bf_emma": {"name": "Emma", "gender": "Female", "accent": "British", "style": "Refined", "lang": "b"},
    "bf_isabella": {"name": "Isabella", "gender": "Female", "accent": "British", "style": "Sophisticated", "lang": "b"},
    "bf_alice": {"name": "Alice", "gender": "Female", "accent": "British", "style": "Classic", "lang": "b"},
    "bf_lily": {"name": "Lily", "gender": "Female", "accent": "British", "style": "Gentle", "lang": "b"},
    # British English - Male
    "bm_george": {"name": "George", "gender": "Male", "accent": "British", "style": "Distinguished", "lang": "b"},
    "bm_lewis": {"name": "Lewis", "gender": "Male", "accent": "British", "style": "Friendly", "lang": "b"},
    "bm_daniel": {"name": "Daniel", "gender": "Male", "accent": "British", "style": "Authoritative", "lang": "b"},
    "bm_fable": {"name": "Fable", "gender": "Male", "accent": "British", "style": "Storyteller", "lang": "b"},
    # Hindi - Female
    "hf_alpha": {"name": "Alpha", "gender": "Female", "accent": "Hindi", "style": "Clear", "lang": "h"},
    "hf_beta": {"name": "Beta", "gender": "Female", "accent": "Hindi", "style": "Expressive", "lang": "h"},
    # Hindi - Male
    "hm_omega": {"name": "Omega", "gender": "Male", "accent": "Hindi", "style": "Deep", "lang": "h"},
    "hm_psi": {"name": "Psi", "gender": "Male", "accent": "Hindi", "style": "Narrator", "lang": "h"},
}

# Preview text for each language
PREVIEW_TEXTS = {
    "a": "Hello! This is a sample of my voice.",
    "b": "Hello! This is a sample of my voice.",
    "h": "नमस्ते! यह मेरी आवाज़ का एक नमूना है।",
}

# Request models
class SynthesizeRequest(BaseModel):
    text: str
    voice: str = "am_michael"
    speed: float = 1.0
    format: str = "wav"  # "wav" or "mp3"
    model: str = "kokoro" # "kokoro" or "pro"

class SynthesizeResponse(BaseModel):
    success: bool
    audio_url: str
    audio_url_mp3: Optional[str] = None
    filename: str
    duration: float
    message: str


# Legacy pipeline loader removed (Moved to engine.py)


def cleanup_old_files():
    """Delete audio files older than CLEANUP_AGE_SECONDS"""
    current_time = time.time()
    deleted_count = 0
    
    for file_path in OUTPUT_DIR.glob("*.*"):
        if file_path.is_file():
            file_age = current_time - file_path.stat().st_mtime
            if file_age > CLEANUP_AGE_SECONDS:
                try:
                    file_path.unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"⚠️ Failed to delete {file_path}: {e}")
    
    if deleted_count > 0:
        print(f"🧹 Auto-cleanup: Deleted {deleted_count} old audio files")


def cleanup_scheduler():
    """Background thread for periodic cleanup"""
    while True:
        time.sleep(CLEANUP_INTERVAL_SECONDS)
        cleanup_old_files()


def convert_to_mp3(wav_path: Path, mp3_path: Path):
    """Convert WAV to MP3 using pydub"""
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_wav(str(wav_path))
        audio.export(str(mp3_path), format="mp3", bitrate="192k")
        return True
    except Exception as e:
        print(f"⚠️ MP3 conversion failed: {e}")
        return False

# Serve static files (CSS, JS, Images)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def serve_home():
    """Serve the main page"""
    return FileResponse("frontend/index.html")


@app.get("/api/voices")
async def get_voices():
    """Get list of available voices"""
    return JSONResponse({
        "success": True,
        "voices": VOICES,
        "default": "am_michael"
    })


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "model": "Kokoro-82M", "version": "2.0.0"}


@app.get("/api/system")
async def get_system_status():
    """Get hardware detection status"""
    return SYSTEM_STATUS


@app.get("/api/preview/{voice_id}")
async def get_voice_preview(voice_id: str):
    """Generate or serve a voice preview sample"""
    
    if voice_id not in VOICES:
        raise HTTPException(status_code=404, detail="Voice not found")
    
    voice_info = VOICES[voice_id]
    lang_code = voice_info.get('lang', 'a')
    preview_file = PREVIEW_DIR / f"{voice_id}.mp3"
    
    # Return cached preview if exists
    if preview_file.exists():
        return FileResponse(preview_file, media_type="audio/mpeg")
    
    # Generate preview
    try:
        pipe = get_pipeline(lang_code)
        preview_text = PREVIEW_TEXTS.get(lang_code, PREVIEW_TEXTS['a'])
        
        audio_chunks = []
        generator = pipe(preview_text, voice=voice_id, speed=1.0)
        
        for _, _, audio in generator:
            audio_chunks.append(audio)
        
        full_audio = np.concatenate(audio_chunks) if len(audio_chunks) > 1 else audio_chunks[0]
        
        # Save as WAV first
        wav_path = PREVIEW_DIR / f"{voice_id}.wav"
        sf.write(str(wav_path), full_audio, 24000)
        
        # Convert to MP3
        convert_to_mp3(wav_path, preview_file)
        
        # Remove WAV, keep MP3
        if preview_file.exists():
            wav_path.unlink(missing_ok=True)
        
        return FileResponse(preview_file, media_type="audio/mpeg")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(e)}")



def chunk_text(text: str, max_chars: int = 350) -> list[str]:
    """
    Split text into chunks that respect sentence boundaries and max character limits.
    Helps prevent Kokoro from truncating long text.
    """
    chunks = []
    current_chunk = ""
    
    # Split by common sentence endings to preserve flow
    # This is a simple split; for better results, one might use regex or nltk
    sentences = text.replace('\n', ' ').split('. ')
    
    for sentence in sentences:
        # Re-add the period that was removed by split (if it wasn't just whitespace)
        if sentence.strip():
            sentence = sentence.strip()
            if not sentence.endswith(('.', '!', '?')):
                 sentence += "."
            
            # Check if adding this sentence exceeds limit
            if len(current_chunk) + len(sentence) + 1 <= max_chars:
                current_chunk += sentence + " "
            else:
                # If current chunk is not empty, push it
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # Start new chunk
                current_chunk = sentence + " "
    
    # Push the last chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks


@app.post("/api/synthesize")
async def synthesize(request: SynthesizeRequest):
    """Convert text to speech"""
    
    # Validate input
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    # Increased limit since we now support chunking
    if len(request.text) > 50000:
        raise HTTPException(status_code=400, detail="Text too long (max 50,000 characters)")
    
    if request.voice not in VOICES:
        raise HTTPException(status_code=400, detail=f"Invalid voice. Available: {list(VOICES.keys())}")
    
    if not 0.5 <= request.speed <= 2.0:
        raise HTTPException(status_code=400, detail="Speed must be between 0.5 and 2.0")
    
    if request.format not in ["wav", "mp3"]:
        raise HTTPException(status_code=400, detail="Format must be 'wav' or 'mp3'")
    
    try:
        # Get the language code for this voice
        voice_info = VOICES[request.voice]
        lang_code = voice_info.get('lang', 'a')
        
        # Get pipeline (Managed by EngineManager now)
        # pipe = get_pipeline(lang_code)
        
        # Generate unique filename
        file_id = uuid.uuid4().hex
        wav_filename = f"{file_id}.wav"
        wav_path = OUTPUT_DIR / wav_filename
        
        # Generate audio
        print(f"🎤 Generating audio with voice '{request.voice}' (lang: {lang_code})...")
        
        # 1. Chunk the text
        text_chunks = chunk_text(request.text)
        print(f"  📄 Split text into {len(text_chunks)} chunks for seamless generation")
        
        all_audio_segments = []
        silence_duration = 0.25  # 250ms silence between chunks
        sample_rate = 24000
        silence_segment = np.zeros(int(sample_rate * silence_duration))
        
        # 2. Generate audio for each chunk
        for i, chunk in enumerate(text_chunks):
            print(f"  ⚡ Processing chunk {i+1}/{len(text_chunks)} ({len(chunk)} chars)...")
            
            # Generate audio for this chunk (via EngineManager)
            chunk_audio_pieces = []
            
            # Use Engine Manager to generate
            # Note: generate returns a generator for Kokoro
            generator = engine_manager.generate(
                chunk, 
                voice=request.voice, 
                speed=request.speed, 
                model_type=request.model
            )
            
            if generator:
                try:
                    for _, _, audio in generator:
                        chunk_audio_pieces.append(audio)
                except Exception as e:
                    print(f"    ⚠️ Chunk generation error: {e}")
            
            if chunk_audio_pieces:
                # Combine pieces of this chunk
                chunk_full_audio = np.concatenate(chunk_audio_pieces)
                all_audio_segments.append(chunk_full_audio)
                
                # Add silence if not the last chunk
                if i < len(text_chunks) - 1:
                    all_audio_segments.append(silence_segment)
        
        if not all_audio_segments:
             raise Exception("No audio generated from text")

        # 3. Concatenate all chunks and silences
        full_audio = np.concatenate(all_audio_segments)
        
        # Save WAV file
        sf.write(str(wav_path), full_audio, sample_rate)
        
        # Calculate duration
        duration = len(full_audio) / sample_rate
        
        # Convert to MP3 if requested or always provide both
        mp3_filename = f"{file_id}.mp3"
        mp3_path = OUTPUT_DIR / mp3_filename
        mp3_url = None
        
        if convert_to_mp3(wav_path, mp3_path):
            mp3_url = f"/audio/{mp3_filename}"
            print(f"✅ Audio saved: {wav_filename} + {mp3_filename} ({duration:.2f}s)")
        else:
            print(f"✅ Audio saved: {wav_filename} ({duration:.2f}s)")
        
        # Return appropriate format
        primary_url = f"/audio/{mp3_filename}" if request.format == "mp3" and mp3_url else f"/audio/{wav_filename}"
        primary_filename = mp3_filename if request.format == "mp3" and mp3_url else wav_filename
        
        return SynthesizeResponse(
            success=True,
            audio_url=primary_url,
            audio_url_mp3=mp3_url,
            filename=primary_filename,
            duration=round(duration, 2),
            message=f"Generated {duration:.1f}s of audio (from {len(text_chunks)} chunks)"
        )
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.get("/audio/{filename}")
async def get_audio(filename: str):
    """Serve generated audio files"""
    # Security: Prevent path traversal attacks
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = OUTPUT_DIR / filename
    
    # Also check previews directory
    if not file_path.exists():
        file_path = PREVIEW_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    # Determine media type
    media_type = "audio/mpeg" if filename.endswith(".mp3") else "audio/wav"
    
    return FileResponse(
        file_path,
        media_type=media_type,
        filename=filename
    )


@app.delete("/api/audio/{filename}")
async def delete_audio(filename: str):
    """Delete a generated audio file"""
    # Security: Prevent path traversal attacks
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = OUTPUT_DIR / filename
    
    if file_path.exists():
        file_path.unlink()
        return {"success": True, "message": "File deleted"}
    
    raise HTTPException(status_code=404, detail="File not found")


@app.get("/api/cleanup")
async def manual_cleanup():
    """Manually trigger cleanup of old files"""
    cleanup_old_files()
    return {"success": True, "message": "Cleanup completed"}





if __name__ == "__main__":
    import uvicorn
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                 🧪  LOCAL LAB - VOICE STUDIO  🧪           ║
    ║                                                           ║
    ║   Professional AI Narration Tool                          ║
    ║   Model: Kokoro-82M                                       ║
    ║   Version: 1.0.0 (Local Lab Release)                      ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
