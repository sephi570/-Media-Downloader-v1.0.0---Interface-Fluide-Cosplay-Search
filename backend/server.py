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
        # Create temporary Instaloader instance
        L = instaloader.Instaloader()
        
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
        raise HTTPException(status_code=400, detail=f"Failed to extract Instagram info: {str(e)}")

def get_reddit_info(url: str) -> dict:
    """Extract Reddit post information"""
    try:
        # Parse Reddit URL to get submission ID
        if '/comments/' in url:
            submission_id = url.split('/comments/')[1].split('/')[0]
        else:
            raise ValueError("Unsupported Reddit URL format")
        
        # Use requests to get Reddit JSON (no auth needed for public posts)
        json_url = f"https://www.reddit.com/comments/{submission_id}.json"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
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
    """Background task for downloading videos"""
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

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "YouTube Downloader API is running"}

@app.post("/api/video/info")
async def get_video_information(request: DownloadRequest):
    """Get video information without downloading"""
    return get_video_info(request.url)

@app.post("/api/video/download")
async def start_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    """Start video download process"""
    download_id = str(uuid.uuid4())
    
    # Validate URL
    if not request.url or 'youtube.com' not in request.url and 'youtu.be' not in request.url:
        raise HTTPException(status_code=400, detail="Please provide a valid YouTube URL")
    
    # Create download record
    download_record = {
        "id": download_id,
        "url": request.url,
        "status": "pending",
        "progress": 0.0,
        "created_at": datetime.utcnow(),
        "quality": request.quality,
        "audio_only": request.audio_only,
        "output_format": request.output_format
    }
    
    await db.downloads.insert_one(download_record)
    
    # Start background download
    background_tasks.add_task(
        download_video_task,
        download_id,
        request.url,
        request.quality,
        request.audio_only,
        request.output_format
    )
    
    return {"download_id": download_id, "status": "started"}

@app.get("/api/video/status/{download_id}")
async def get_download_status(download_id: str):
    """Get download status and progress"""
    download = await db.downloads.find_one({"id": download_id})
    if not download:
        raise HTTPException(status_code=404, detail="Download not found")
    
    return DownloadStatus(**download)

@app.get("/api/video/downloads")
async def list_downloads(limit: int = 50, status: Optional[str] = None):
    """List all downloads with optional status filter"""
    query = {}
    if status:
        query["status"] = status
    
    cursor = db.downloads.find(query).sort("created_at", -1).limit(limit)
    downloads = await cursor.to_list(length=limit)
    
    return [DownloadStatus(**download) for download in downloads]

@app.get("/api/video/download/{download_id}")
async def download_file(download_id: str):
    """Download the completed video file"""
    download = await db.downloads.find_one({"id": download_id})
    if not download:
        raise HTTPException(status_code=404, detail="Download not found")
    
    if download["status"] != "completed":
        raise HTTPException(status_code=400, detail="Download not completed")
    
    # Find the file
    if not download.get("filename") or not download.get("uploader"):
        raise HTTPException(status_code=404, detail="File information not found")
    
    uploader_dir = os.path.join(DOWNLOAD_BASE_DIR, sanitize_filename(download["uploader"]))
    filepath = os.path.join(uploader_dir, download["filename"])
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        filepath,
        media_type='application/octet-stream',
        filename=download["filename"]
    )

@app.delete("/api/video/download/{download_id}")
async def delete_download(download_id: str):
    """Delete download record and file"""
    download = await db.downloads.find_one({"id": download_id})
    if not download:
        raise HTTPException(status_code=404, detail="Download not found")
    
    # Delete file if exists
    if download.get("filename") and download.get("uploader"):
        uploader_dir = os.path.join(DOWNLOAD_BASE_DIR, sanitize_filename(download["uploader"]))
        filepath = os.path.join(uploader_dir, download["filename"])
        
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                logging.error(f"Failed to delete file {filepath}: {str(e)}")
    
    # Delete database record
    await db.downloads.delete_one({"id": download_id})
    
    return {"message": "Download deleted successfully"}

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