from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import yt_dlp
import os
import asyncio
import logging
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
import re
import subprocess
import tempfile
import instaloader
import praw
from urllib.parse import urlparse
import requests
import json

# Environment variables
import os
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')

# Platform authentication settings
INSTAGRAM_USERNAME = os.environ.get('INSTAGRAM_USERNAME', '')
INSTAGRAM_PASSWORD = os.environ.get('INSTAGRAM_PASSWORD', '')
REDDIT_CLIENT_ID = os.environ.get('REDDIT_CLIENT_ID', '')
REDDIT_CLIENT_SECRET = os.environ.get('REDDIT_CLIENT_SECRET', '')
REDDIT_USERNAME = os.environ.get('REDDIT_USERNAME', '')
REDDIT_PASSWORD = os.environ.get('REDDIT_PASSWORD', '')

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
client = AsyncIOMotorClient(MONGO_URL)
db = client.youtube_downloader

# Download directory structure
DOWNLOAD_BASE_DIR = "downloads"
os.makedirs(DOWNLOAD_BASE_DIR, exist_ok=True)

class DownloadRequest(BaseModel):
    url: str
    quality: str = "best"
    audio_only: bool = False
    output_format: str = "mp4"
    platform: str = "auto"  # auto, youtube, instagram, reddit

class AuthConfig(BaseModel):
    platform: str
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    additional_data: Optional[dict] = None

class MediaInfo(BaseModel):
    title: str
    platform: str
    uploader: Optional[str] = None
    duration: Optional[int] = None
    view_count: Optional[int] = None
    upload_date: Optional[str] = None
    thumbnail: Optional[str] = None
    media_type: str = "video"  # video, image, gallery
    media_count: int = 1

# Global auth storage (in production, use secure database)
auth_storage = {}

class DownloadStatus(BaseModel):
    id: str
    url: str
    status: str
    progress: float = 0.0
    filename: Optional[str] = None
    file_size: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    title: Optional[str] = None
    uploader: Optional[str] = None

def sanitize_filename(filename):
    """Sanitize filename for filesystem compatibility"""
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace multiple spaces with single space
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    # Limit length
    return sanitized[:200] if len(sanitized) > 200 else sanitized

def get_video_info(url: str):
    """Extract video information without downloading"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'format': 'best',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'extractor_args': {
            'youtube': {
                'player_client': ['web'],
                'player_skip': ['configs', 'webpage']
            }
        }
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'view_count': info.get('view_count', 0),
                'upload_date': info.get('upload_date', ''),
                'thumbnail': info.get('thumbnail', ''),
                'formats': [
                    {
                        'format_id': f.get('format_id'),
                        'ext': f.get('ext'),
                        'quality': f.get('quality', 0),
                        'filesize': f.get('filesize'),
                        'format_note': f.get('format_note', '')
                    }
                    for f in info.get('formats', [])
                    if f.get('vcodec') != 'none'
                ]
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to extract video info: {str(e)}")

def detect_platform(url: str) -> str:
    """Detect platform from URL"""
    url_lower = url.lower()
    
    if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube'
    elif 'instagram.com' in url_lower:
        return 'instagram'
    elif 'reddit.com' in url_lower:
        return 'reddit'
    elif 'pornhub.com' in url_lower:
        return 'pornhub'
    elif 'redtube.com' in url_lower:
        return 'redtube'
    elif 'nhentai.net' in url_lower:
        return 'nhentai'
    elif 'luscious.net' in url_lower:
        return 'luscious'
    else:
        return 'unknown'

def get_instagram_info(url: str) -> dict:
    """Extract Instagram post/story information"""
    try:
        # Create Instaloader instance with authentication if available
        L = instaloader.Instaloader()
        
        # Try to login if credentials are available
        if INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD:
            try:
                L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
            except Exception as login_error:
                # Continue without login, but note the limitation
                logging.warning(f"Instagram login failed: {str(login_error)}")
        
        # Extract shortcode from URL
        if '/p/' in url:
            shortcode = url.split('/p/')[1].split('/')[0]
        elif '/reel/' in url:
            shortcode = url.split('/reel/')[1].split('/')[0]
        else:
            raise ValueError("Unsupported Instagram URL format")
        
        # Get post information
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        return {
            'title': post.caption[:100] + '...' if post.caption and len(post.caption) > 100 else post.caption or 'Instagram Post',
            'platform': 'instagram',
            'uploader': post.owner_username,
            'upload_date': post.date_utc.strftime('%Y%m%d'),
            'media_type': 'video' if post.is_video else 'image',
            'media_count': 1 if not post.typename == 'GraphSidecar' else len(list(post.get_sidecar_nodes())),
            'view_count': post.video_view_count if post.is_video else post.likes,
            'thumbnail': post.url
        }
    except Exception as e:
        # If authentication fails, provide helpful error message
        if "401" in str(e) or "login" in str(e).lower():
            raise HTTPException(
                status_code=400, 
                detail=f"Instagram authentication required. Please configure INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD environment variables. Error: {str(e)}"
            )
        raise HTTPException(status_code=400, detail=f"Failed to extract Instagram info: {str(e)}")

def get_reddit_info(url: str) -> dict:
    """Extract Reddit post information"""
    try:
        # First try the simple JSON approach (no auth required)
        if '/comments/' in url:
            submission_id = url.split('/comments/')[1].split('/')[0]
        else:
            raise ValueError("Unsupported Reddit URL format")
        
        # Use requests to get Reddit JSON (no auth needed for public posts)
        json_url = f"https://www.reddit.com/comments/{submission_id}.json"
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; gallery-dl-bot/1.0)'}
        
        response = requests.get(json_url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        post_data = data[0]['data']['children'][0]['data']
        
        # Determine media type
        media_type = 'text'
        if post_data.get('is_video'):
            media_type = 'video'
        elif post_data.get('url') and any(ext in post_data['url'].lower() for ext in ['.jpg', '.png', '.gif', '.jpeg']):
            media_type = 'image'
        elif 'gallery' in post_data.get('url', ''):
            media_type = 'gallery'
        
        return {
            'title': post_data.get('title', 'Reddit Post'),
            'platform': 'reddit',
            'uploader': f"u/{post_data.get('author', 'unknown')}",
            'upload_date': datetime.fromtimestamp(post_data.get('created_utc', 0)).strftime('%Y%m%d'),
            'media_type': media_type,
            'media_count': 1,
            'view_count': post_data.get('score', 0),
            'thumbnail': post_data.get('thumbnail') if post_data.get('thumbnail') != 'self' else None
        }
    except Exception as e:
        # If we can't get basic info, suggest authentication setup
        if "403" in str(e) or "429" in str(e):
            raise HTTPException(
                status_code=400, 
                detail=f"Reddit access limited. For better access, configure REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET environment variables. Error: {str(e)}"
            )
        raise HTTPException(status_code=400, detail=f"Failed to extract Reddit info: {str(e)}")

def get_media_info(url: str) -> dict:
    """Get media information based on platform"""
    platform = detect_platform(url)
    
    if platform == 'youtube':
        return get_video_info(url)
    elif platform == 'instagram':
        return get_instagram_info(url)
    elif platform == 'reddit':
        return get_reddit_info(url)
    else:
        # Try with yt-dlp for other platforms
        try:
            return get_video_info(url)
        except:
            raise HTTPException(status_code=400, detail=f"Unsupported platform or invalid URL: {platform}")

class DownloadProgress:
    def __init__(self, download_id: str):
        self.download_id = download_id
        self.progress = 0.0
        
    def progress_hook(self, d):
        if d['status'] == 'downloading':
            if 'total_bytes' in d:
                self.progress = (d['downloaded_bytes'] / d['total_bytes']) * 100
            elif 'total_bytes_estimate' in d:
                self.progress = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
            
            # Update progress in database asynchronously
            asyncio.create_task(self.update_progress_db())
    
    async def update_progress_db(self):
        try:
            await db.downloads.update_one(
                {"id": self.download_id},
                {"$set": {"progress": self.progress}}
            )
        except Exception as e:
            logging.error(f"Failed to update progress for {self.download_id}: {str(e)}")

async def download_video_task(download_id: str, url: str, quality: str, audio_only: bool, output_format: str):
    """Download video using yt-dlp"""
    try:
        # Update status to downloading
        await db.downloads.update_one(
            {"id": download_id},
            {"$set": {"status": "downloading"}}
        )
        
        # Get video info
        video_info = get_video_info(url)
        safe_title = sanitize_filename(video_info['title'])
        safe_uploader = sanitize_filename(video_info['uploader'])
        
        # Create organized folder structure
        uploader_dir = os.path.join(DOWNLOAD_BASE_DIR, safe_uploader)
        os.makedirs(uploader_dir, exist_ok=True)
        
        progress_tracker = DownloadProgress(download_id)
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best' if audio_only else quality,
            'outtmpl': os.path.join(uploader_dir, f'{safe_title}.%(ext)s'),
            'progress_hooks': [progress_tracker.progress_hook],
            'noplaylist': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'extractor_args': {
                'youtube': {
                    'player_client': ['web'],
                    'player_skip': ['configs', 'webpage']
                }
            }
        }
        
        if audio_only:
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        elif output_format != 'mp4':
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': output_format,
            }]
        
        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Find the downloaded file
        downloaded_files = []
        for file in os.listdir(uploader_dir):
            if safe_title in file:
                downloaded_files.append(file)
        
        if downloaded_files:
            filename = downloaded_files[0]
            filepath = os.path.join(uploader_dir, filename)
            file_size = os.path.getsize(filepath)
            
            # Update completion status
            await db.downloads.update_one(
                {"id": download_id},
                {
                    "$set": {
                        "status": "completed",
                        "progress": 100.0,
                        "filename": filename,
                        "file_size": file_size,
                        "completed_at": datetime.utcnow(),
                        "title": video_info['title'],
                        "uploader": video_info['uploader']
                    }
                }
            )
        else:
            raise Exception("Downloaded file not found")
            
    except Exception as e:
        # Update error status
        await db.downloads.update_one(
            {"id": download_id},
            {
                "$set": {
                    "status": "failed",
                    "error_message": str(e)
                }
            }
        )
        logging.error(f"Download failed for {download_id}: {str(e)}")

async def download_instagram_task(download_id: str, url: str, quality: str):
    """Download Instagram media"""
    try:
        await db.downloads.update_one(
            {"id": download_id},
            {"$set": {"status": "downloading", "progress": 10.0}}
        )
        
        # Get media info
        media_info = get_instagram_info(url)
        safe_title = sanitize_filename(media_info['title'])
        safe_uploader = sanitize_filename(media_info['uploader'])
        
        # Create organized folder structure
        platform_dir = os.path.join(DOWNLOAD_BASE_DIR, "Instagram", safe_uploader)
        os.makedirs(platform_dir, exist_ok=True)
        
        # Use Instaloader to download with authentication
        L = instaloader.Instaloader(
            dirname_pattern=platform_dir,
            filename_pattern="{shortcode}_{date_utc}",
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False
        )
        
        # Try to login if credentials are available
        if INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD:
            try:
                L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
                logging.info("Instagram login successful")
            except Exception as login_error:
                logging.warning(f"Instagram login failed: {str(login_error)}")
                # Continue without login for public posts
        
        # Extract shortcode from URL
        if '/p/' in url:
            shortcode = url.split('/p/')[1].split('/')[0]
        elif '/reel/' in url:
            shortcode = url.split('/reel/')[1].split('/')[0]
        else:
            raise ValueError("Unsupported Instagram URL format")
        
        # Progress update
        await db.downloads.update_one(
            {"id": download_id},
            {"$set": {"progress": 50.0}}
        )
        
        # Download the post
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target="")
        
        # Find downloaded files
        downloaded_files = []
        for file in os.listdir(platform_dir):
            if shortcode in file and not file.endswith('.json.xz'):  # Skip metadata files
                downloaded_files.append(file)
        
        if downloaded_files:
            # Take the first media file (usually the main content)
            filename = downloaded_files[0]
            filepath = os.path.join(platform_dir, filename)
            file_size = os.path.getsize(filepath)
            
            await db.downloads.update_one(
                {"id": download_id},
                {
                    "$set": {
                        "status": "completed",
                        "progress": 100.0,
                        "filename": filename,
                        "file_size": file_size,
                        "completed_at": datetime.utcnow(),
                        "title": media_info['title'],
                        "uploader": media_info['uploader']
                    }
                }
            )
        else:
            raise Exception("Downloaded file not found")
            
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "login" in error_msg.lower():
            error_msg = f"Instagram authentication required. Please configure INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD environment variables. {error_msg}"
        
        await db.downloads.update_one(
            {"id": download_id},
            {
                "$set": {
                    "status": "failed",
                    "error_message": error_msg
                }
            }
        )
        logging.error(f"Instagram download failed for {download_id}: {error_msg}")

async def download_reddit_task(download_id: str, url: str, quality: str):
    """Download Reddit media using gallery-dl"""
    try:
        await db.downloads.update_one(
            {"id": download_id},
            {"$set": {"status": "downloading", "progress": 10.0}}
        )
        
        # Get media info
        media_info = get_reddit_info(url)
        safe_title = sanitize_filename(media_info['title'])
        safe_uploader = sanitize_filename(media_info['uploader'])
        
        # Create organized folder structure
        platform_dir = os.path.join(DOWNLOAD_BASE_DIR, "Reddit", safe_uploader)
        os.makedirs(platform_dir, exist_ok=True)
        
        # Progress update
        await db.downloads.update_one(
            {"id": download_id},
            {"$set": {"progress": 30.0}}
        )
        
        # Create gallery-dl config for Reddit authentication if available
        config_data = {}
        if REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET:
            config_data = {
                "extractor": {
                    "reddit": {
                        "client-id": REDDIT_CLIENT_ID,
                        "client-secret": REDDIT_CLIENT_SECRET
                    }
                }
            }
            
            if REDDIT_USERNAME and REDDIT_PASSWORD:
                config_data["extractor"]["reddit"].update({
                    "username": REDDIT_USERNAME,
                    "password": REDDIT_PASSWORD
                })
        
        # Use gallery-dl to download Reddit content
        cmd = [
            "gallery-dl",
            "--dest", platform_dir,
            "--filename", "{category}_{subcategory}_{id}_{num}.{extension}"
        ]
        
        # Add config if we have authentication
        if config_data:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as config_file:
                json.dump(config_data, config_file)
                cmd.extend(["--config", config_file.name])
                
                # Add URL and run command
                cmd.append(url)
                
                # Run gallery-dl command
                process = subprocess.run(cmd, capture_output=True, text=True)
                
                # Clean up temp config file
                os.unlink(config_file.name)
        else:
            # Run without authentication config
            cmd.append(url)
            process = subprocess.run(cmd, capture_output=True, text=True)
        
        # Progress update
        await db.downloads.update_one(
            {"id": download_id},
            {"$set": {"progress": 80.0}}
        )
        
        if process.returncode == 0:
            # Find downloaded files
            downloaded_files = []
            for root, dirs, files in os.walk(platform_dir):
                for file in files:
                    if file.endswith(('.jpg', '.png', '.gif', '.mp4', '.webm', '.jpeg')):
                        downloaded_files.append(file)
                        break  # Take first file found
            
            if downloaded_files:
                filename = downloaded_files[0]
                filepath = os.path.join(platform_dir, filename)
                file_size = os.path.getsize(filepath)
                
                await db.downloads.update_one(
                    {"id": download_id},
                    {
                        "$set": {
                            "status": "completed",
                            "progress": 100.0,
                            "filename": filename,
                            "file_size": file_size,
                            "completed_at": datetime.utcnow(),
                            "title": media_info['title'],
                            "uploader": media_info['uploader']
                        }
                    }
                )
            else:
                raise Exception("No media files found to download")
        else:
            error_msg = process.stderr
            if "403" in error_msg or "rate limit" in error_msg.lower():
                error_msg = f"Reddit access limited. For better access, configure REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables. {error_msg}"
            raise Exception(f"gallery-dl failed: {error_msg}")
            
    except Exception as e:
        error_msg = str(e)
        await db.downloads.update_one(
            {"id": download_id},
            {
                "$set": {
                    "status": "failed",
                    "error_message": error_msg
                }
            }
        )
        logging.error(f"Reddit download failed for {download_id}: {error_msg}")

async def download_media_task(download_id: str, url: str, quality: str, audio_only: bool, output_format: str, platform: str):
    """Universal download function that routes to appropriate downloader"""
    detected_platform = detect_platform(url) if platform == "auto" else platform
    
    if detected_platform == 'youtube':
        await download_video_task(download_id, url, quality, audio_only, output_format)
    elif detected_platform == 'instagram':
        await download_instagram_task(download_id, url, quality)
    elif detected_platform == 'reddit':
        await download_reddit_task(download_id, url, quality)
    else:
        # Try with yt-dlp for other platforms
        try:
            await download_video_task(download_id, url, quality, audio_only, output_format)
        except Exception as e:
            await db.downloads.update_one(
                {"id": download_id},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": f"Unsupported platform '{detected_platform}': {str(e)}"
                    }
                }
            )
            logging.error(f"Unsupported platform download failed for {download_id}: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "YouTube Downloader API is running"}

@app.post("/api/media/info")
async def get_media_information(request: DownloadRequest):
    """Get media information from any supported platform"""
    return get_media_info(request.url)

@app.post("/api/media/download")
async def start_media_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    """Start media download process for any supported platform"""
    download_id = str(uuid.uuid4())
    
    # Detect platform
    platform = detect_platform(request.url) if request.platform == "auto" else request.platform
    
    # Validate URL based on platform
    if platform == 'unknown':
        raise HTTPException(status_code=400, detail="Unsupported platform or invalid URL")
    
    # Create download record
    download_record = {
        "id": download_id,
        "url": request.url,
        "status": "pending",
        "progress": 0.0,
        "created_at": datetime.utcnow(),
        "quality": request.quality,
        "audio_only": request.audio_only,
        "output_format": request.output_format,
        "platform": platform
    }
    
    await db.downloads.insert_one(download_record)
    
    # Start background download with new universal function
    background_tasks.add_task(
        download_media_task,
        download_id,
        request.url,
        request.quality,
        request.audio_only,
        request.output_format,
        request.platform
    )
    
    return {"download_id": download_id, "status": "started", "platform": platform}

@app.get("/api/media/status/{download_id}")
async def get_download_status(download_id: str):
    """Get download status and progress"""
    download = await db.downloads.find_one({"id": download_id})
    if not download:
        raise HTTPException(status_code=404, detail="Download not found")
    
    return DownloadStatus(**download)

@app.get("/api/media/downloads")
async def list_downloads(limit: int = 50, status: Optional[str] = None, platform: Optional[str] = None):
    """List all downloads with optional status and platform filter"""
    query = {}
    if status:
        query["status"] = status
    if platform:
        query["platform"] = platform
    
    cursor = db.downloads.find(query).sort("created_at", -1).limit(limit)
    downloads = await cursor.to_list(length=limit)
    
    return [DownloadStatus(**download) for download in downloads]

@app.get("/api/media/download/{download_id}")
async def download_file(download_id: str):
    """Download the completed media file"""
    download = await db.downloads.find_one({"id": download_id})
    if not download:
        raise HTTPException(status_code=404, detail="Download not found")
    
    if download["status"] != "completed":
        raise HTTPException(status_code=400, detail="Download not completed")
    
    # Find the file based on platform
    if not download.get("filename") or not download.get("uploader"):
        raise HTTPException(status_code=404, detail="File information not found")
    
    platform = download.get("platform", "unknown")
    
    if platform == "youtube":
        platform_dir = os.path.join(DOWNLOAD_BASE_DIR, sanitize_filename(download["uploader"]))
    elif platform == "instagram":
        platform_dir = os.path.join(DOWNLOAD_BASE_DIR, "Instagram", sanitize_filename(download["uploader"]))
    elif platform == "reddit":
        platform_dir = os.path.join(DOWNLOAD_BASE_DIR, "Reddit", sanitize_filename(download["uploader"]))
    else:
        platform_dir = os.path.join(DOWNLOAD_BASE_DIR, "Other", sanitize_filename(download["uploader"]))
    
    filepath = os.path.join(platform_dir, download["filename"])
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        filepath,
        media_type='application/octet-stream',
        filename=download["filename"]
    )

@app.delete("/api/media/download/{download_id}")
async def delete_download(download_id: str):
    """Delete download record and file"""
    download = await db.downloads.find_one({"id": download_id})
    if not download:
        raise HTTPException(status_code=404, detail="Download not found")
    
    # Delete file if exists
    if download.get("filename") and download.get("uploader"):
        platform = download.get("platform", "unknown")
        
        if platform == "youtube":
            platform_dir = os.path.join(DOWNLOAD_BASE_DIR, sanitize_filename(download["uploader"]))
        elif platform == "instagram":
            platform_dir = os.path.join(DOWNLOAD_BASE_DIR, "Instagram", sanitize_filename(download["uploader"]))
        elif platform == "reddit":
            platform_dir = os.path.join(DOWNLOAD_BASE_DIR, "Reddit", sanitize_filename(download["uploader"]))
        else:
            platform_dir = os.path.join(DOWNLOAD_BASE_DIR, "Other", sanitize_filename(download["uploader"]))
        
        filepath = os.path.join(platform_dir, download["filename"])
        
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                logging.error(f"Failed to delete file {filepath}: {str(e)}")
    
    # Delete database record
    await db.downloads.delete_one({"id": download_id})
    
    return {"message": "Download deleted successfully"}

@app.get("/api/auth/status")
async def get_auth_status():
    """Get authentication status for different platforms"""
    return {
        "instagram": {
            "configured": bool(INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD),
            "username": INSTAGRAM_USERNAME if INSTAGRAM_USERNAME else None
        },
        "reddit": {
            "configured": bool(REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET),
            "has_user_auth": bool(REDDIT_USERNAME and REDDIT_PASSWORD)
        },
        "youtube": {
            "configured": True,
            "note": "YouTube works without authentication via yt-dlp"
        }
    }

@app.get("/api/platforms")
async def get_supported_platforms():
    """Get list of supported platforms"""
    return {
        "supported_platforms": [
            {"name": "YouTube", "key": "youtube", "formats": ["mp4", "avi", "mkv", "webm", "mp3"]},
            {"name": "Instagram", "key": "instagram", "formats": ["jpg", "mp4"]},
            {"name": "Reddit", "key": "reddit", "formats": ["jpg", "png", "gif", "mp4", "webm"]},
            {"name": "Other (via yt-dlp)", "key": "other", "formats": ["mp4", "avi", "mkv", "webm", "mp3"]}
        ]
    }

@app.get("/api/stats")
async def get_stats():
    """Get download statistics"""
    total_downloads = await db.downloads.count_documents({})
    completed_downloads = await db.downloads.count_documents({"status": "completed"})
    failed_downloads = await db.downloads.count_documents({"status": "failed"})
    downloading = await db.downloads.count_documents({"status": "downloading"})
    
    return {
        "total_downloads": total_downloads,
        "completed_downloads": completed_downloads,
        "failed_downloads": failed_downloads,
        "currently_downloading": downloading,
        "success_rate": (completed_downloads / total_downloads * 100) if total_downloads > 0 else 0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)