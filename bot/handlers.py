"""
Audio Processing Module
Handles audio search and download functionality.
"""

import os
import logging
import asyncio
import yt_dlp
from typing import Dict, Optional
import tempfile
import hashlib

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Handles audio search and download operations."""
    
    def __init__(self):
        """Initialize audio processor."""
        self.download_dir = tempfile.mkdtemp(prefix="music_bot_")
        logger.info(f"Audio processor initialized with download directory: {self.download_dir}")
    
    async def download_track(self, track_info: Dict, quality: str) -> Optional[str]:
        """
        Download track audio file with timeout handling.
        
        Args:
            track_info: Track information dictionary
            quality: Quality preference (128, 192, 320)
            
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            # Create search query
            search_query = f"{track_info['name']} {track_info['artist']}"
            logger.info(f"Searching for: {search_query}")
            
            # Configure yt-dlp options
            ydl_opts = self._get_ydl_options(quality)
            
            # Generate unique filename
            file_hash = hashlib.md5(search_query.encode()).hexdigest()[:8]
            output_filename = f"{track_info['name']} - {track_info['artist']} [{file_hash}].%(ext)s"
            ydl_opts['outtmpl'] = os.path.join(self.download_dir, output_filename)
            
            # Search and download with timeout
            loop = asyncio.get_event_loop()
            try:
                file_path = await asyncio.wait_for(
                    loop.run_in_executor(
                        None, 
                        self._download_audio, 
                        search_query, 
                        ydl_opts
                    ),
                    timeout=60  # 1 minute timeout
                )
                
                if file_path and os.path.exists(file_path):
                    logger.info(f"Successfully downloaded: {file_path}")
                    return file_path
                else:
                    logger.error(f"Download failed for: {search_query}")
                    return None
                    
            except asyncio.TimeoutError:
                logger.error(f"Download timeout for: {search_query}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading track {track_info['name']}: {e}")
            return None
    
    def _download_audio(self, search_query: str, ydl_opts: Dict) -> Optional[str]:
        """
        Internal method to download audio using yt-dlp.
        
        Args:
            search_query: Search query string
            ydl_opts: yt-dlp options
            
        Returns:
            Path to downloaded file or None
        """
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Search for the track
                search_results = ydl.extract_info(
                    f"ytsearch1:{search_query}",
                    download=False
                )
                
                if not search_results or 'entries' not in search_results or not search_results['entries']:
                    logger.error(f"No search results found for: {search_query}")
                    return None
                
                # Get the first result
                video_info = search_results['entries'][0]
                video_url = video_info['url']
                
                # Download the audio
                ydl.download([video_url])
                
                # Find the downloaded file
                expected_path = ydl.prepare_filename(video_info)
                
                # yt-dlp might change the extension, so find the actual file
                base_path = os.path.splitext(expected_path)[0]
                for ext in ['.mp3', '.m4a', '.webm', '.ogg']:
                    potential_path = base_path + ext
                    if os.path.exists(potential_path):
                        return potential_path
                
                # If exact match not found, look in download directory
                for file in os.listdir(self.download_dir):
                    if file.startswith(os.path.basename(base_path)):
                        return os.path.join(self.download_dir, file)
                
                logger.error(f"Downloaded file not found for: {search_query}")
                return None
                
        except Exception as e:
            logger.error(f"yt-dlp download error: {e}")
            return None
    
    def _get_ydl_options(self, quality: str) -> Dict:
        """
        Get yt-dlp options based on quality preference.
        
        Args:
            quality: Quality setting (128, 192, 320)
            
        Returns:
            yt-dlp options dictionary
        """
        # Base options optimized for speed and reliability
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'extractflat': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'writedescription': False,
            'writeinfojson': False,
            'writethumbnail': False,
            'socket_timeout': 20,
            'http_chunk_size': 10485760,  # 10 MB chunks
            'retries': 2,
            'fragment_retries': 2,
        }
        
        # Skip post-processing for faster downloads - send raw audio
        # Quality selection will be handled by format selection instead
        if quality == "128":
            ydl_opts['format'] = 'bestaudio[abr<=128]/bestaudio'
        elif quality == "192":
            ydl_opts['format'] = 'bestaudio[abr<=192]/bestaudio'  
        elif quality == "320":
            ydl_opts['format'] = 'bestaudio/best'
        else:
            ydl_opts['format'] = 'bestaudio[abr<=192]/bestaudio'
        
        return ydl_opts
    
    def cleanup_file(self, file_path: str):
        """
        Clean up downloaded file.
        
        Args:
            file_path: Path to file to be cleaned up
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup file {file_path}: {e}")
    
    def cleanup_all(self):
        """Clean up all downloaded files."""
        try:
            for file in os.listdir(self.download_dir):
                file_path = os.path.join(self.download_dir, file)
                self.cleanup_file(file_path)
            os.rmdir(self.download_dir)
            logger.info("All files cleaned up successfully")
        except Exception as e:
            logger.warning(f"Failed to cleanup all files: {e}")
"""
Demo Songs Module
Provides rotating demo song URLs for testing bot functionality.
"""

import random
import logging

logger = logging.getLogger(__name__)

class DemoSongs:
    """Manages demo song URLs for testing."""
    
    def __init__(self):
        """Initialize with popular demo songs."""
        self.demo_urls = [
            "https://open.spotify.com/track/4iV5W9uYEdYUVa79Axb7Rh",  # Never Gonna Give You Up - Rick Astley
            "https://open.spotify.com/track/0VjIjW4GlULA8KFjAl1kgK",  # Blinding Lights - The Weeknd
            "https://open.spotify.com/track/11dFghVXANMlKmJXsNCbNl",  # Rather Be - Clean Bandit
            "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC",  # Never Gonna Give You Up - Rick Astley (alternative)
            "https://open.spotify.com/track/7qiZfU4dY1lWllzX7mPBI3",  # Shape of You - Ed Sheeran
            "https://open.spotify.com/track/2takcwOaAZWiXQijPHIx7B",  # Time to Dance - The Sounds
            "https://open.spotify.com/track/1Je1IMUlBXcx1Fz0WE7oPT",  # Somebody That I Used to Know - Gotye
            "https://open.spotify.com/track/5ghIJDpPoe3CfHMGu71E6T",  # Closer - The Chainsmokers
            "https://open.spotify.com/track/3a1lNhkSLSkpJE4MSHpDu9",  # Counting Stars - OneRepublic
            "https://open.spotify.com/track/0tgVpDi06FyKpA1z0VMD4v",  # Perfect - Ed Sheeran
            "https://open.spotify.com/track/6habFhsOp2NvshLv26DqMb",  # Stressed Out - Twenty One Pilots
            "https://open.spotify.com/track/1lDWb6b6ieDQ2xT7ewTC3G",  # Despacito - Luis Fonsi
            "https://open.spotify.com/track/7BKLCZ1jbUBVqRi2FVlTVw",  # Uptown Funk - Mark Ronson ft. Bruno Mars
            "https://open.spotify.com/track/6RUKPb4LETWmmr3iAEQktW",  # Shake It Off - Taylor Swift
            "https://open.spotify.com/track/4VqPOruhp5EdPBeR92t6lQ",  # Gangnam Style - PSY
            "https://open.spotify.com/track/0wwPcA6wtMf6HUMpIRdeP7",  # All of Me - John Legend
            "https://open.spotify.com/track/2Fxmhks0bxGSBdJ92vM42m",  # bad guy - Billie Eilish
            "https://open.spotify.com/track/4Dvkj6JhhA12EX05fT7y2e",  # Thunder - Imagine Dragons
            "https://open.spotify.com/track/5tz69p7tJuGPeMGwNTxYuV",  # Someone Like You - Adele
            "https://open.spotify.com/track/4iJyoBOLtHqaGxP12qzhQI",  # Roar - Katy Perry
        ]
        
        # Shuffle the list initially
        random.shuffle(self.demo_urls)
        logger.info(f"Demo songs initialized with {len(self.demo_urls)} songs")
    
    def get_random_demo_url(self) -> str:
        """
        Get a random demo URL.
        
        Returns:
            Random demo song URL
        """
        demo_url = random.choice(self.demo_urls)
        logger.info(f"Providing demo URL: {demo_url}")
        return demo_url
    
    def get_demo_batch(self, count: int = 5) -> list:
        """
        Get a batch of random demo URLs.
        
        Args:
            count: Number of URLs to return
            
        Returns:
            List of demo URLs
        """
        return random.sample(self.demo_urls, min(count, len(self.demo_urls)))
    
    def refresh_demo_list(self):
        """Shuffle the demo list for variety."""
        random.shuffle(self.demo_urls)
        logger.info("Demo song list refreshed")
    
    def add_demo_song(self, url: str):
        """
        Add a new demo song URL.
        
        Args:
            url: Spotify URL to add
        """
        if url not in self.demo_urls:
            self.demo_urls.append(url)
            logger.info(f"Added new demo song: {url}")
        else:
            logger.info(f"Demo song already exists: {url}")
    
    def remove_demo_song(self, url: str):
        """
        Remove a demo song URL.
        
        Args:
            url: Spotify URL to remove
        """
        if url in self.demo_urls:
            self.demo_urls.remove(url)
            logger.info(f"Removed demo song: {url}")
        else:
            logger.warning(f"Demo song not found: {url}")
    
    def get_demo_count(self) -> int:
        """
        Get the total number of demo songs.
        
        Returns:
            Number of demo songs available
        """
        return len(self.demo_urls)
"""
Telegram Bot Handlers
Contains all command and callback handlers for the music bot.
"""

import logging
import re
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from .spotify_client import SpotifyClient
from .audio_processor import AudioProcessor
from .demo_songs import DemoSongs
from .utils import create_quality_keyboard, create_main_keyboard, extract_spotify_id
from config import BOT_WELCOME, BOT_HELP, QUALITY_OPTIONS

logger = logging.getLogger(__name__)

# Initialize components
spotify_client = SpotifyClient()
audio_processor = AudioProcessor()
demo_songs = DemoSongs()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with attractive welcome message."""
    keyboard = create_main_keyboard()
    
    await update.message.reply_text(
        BOT_WELCOME,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command with detailed instructions."""
    keyboard = [[InlineKeyboardButton("🏠 Back to Main Menu", callback_data="main_menu")]]
    
    await update.message.reply_text(
        BOT_HELP,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming text messages (URLs)."""
    message_text = update.message.text.strip()
    
    # Check if it's a Spotify URL
    if "spotify.com" in message_text:
        await handle_spotify_url(update, context, message_text)
    else:
        # Guide user to use proper links
        keyboard = [[InlineKeyboardButton("🎪 Try Demo", callback_data="try_demo")]]
        await update.message.reply_text(
            "🤔 *Hmm, that doesn't look like a valid music link!*\n\n"
            "Please share a proper music platform link, or try our demo feature! 🎶",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def handle_spotify_url(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    """Process Spotify URLs and initiate download flow."""
    # Send processing message
    processing_msg = await update.message.reply_text(
        "🔍 *Analyzing your request...*\n\n"
        "⏳ Please wait while I prepare everything for you! ✨",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        # Extract Spotify ID and type
        spotify_id, content_type = extract_spotify_id(url)
        
        if content_type == "track":
            await handle_single_track(update, context, spotify_id, processing_msg)
        elif content_type == "playlist":
            await handle_playlist(update, context, spotify_id, processing_msg)
        elif content_type == "album":
            await handle_album(update, context, spotify_id, processing_msg)
        else:
            await processing_msg.edit_text(
                "🚫 *Oops! Unsupported link type.*\n\n"
                "Please share a track, playlist, or album link! 🎶",
                parse_mode=ParseMode.MARKDOWN
            )
            
    except Exception as e:
        logger.error(f"Error processing Spotify URL: {e}")
        await processing_msg.edit_text(
            "🚫 *Something went wrong!*\n\n"
            "Please check your link and try again. 🔄",
            parse_mode=ParseMode.MARKDOWN
        )

async def handle_single_track(update: Update, context: ContextTypes.DEFAULT_TYPE, track_id: str, processing_msg):
    """Handle single track download with quality selection."""
    try:
        # Get track metadata
        track_info = await spotify_client.get_track_info(track_id)
        
        if not track_info:
            await processing_msg.edit_text(
                "🚫 *Track not found!*\n\n"
                "Please check your link and try again. 🔄",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Store track info in context for later use
        context.user_data['current_track'] = track_info
        context.user_data['processing_msg_id'] = processing_msg.message_id
        
        # Create quality selection keyboard
        keyboard = create_quality_keyboard(track_id)
        
        await processing_msg.edit_text(
            f"🎶 *Found your track!*\n\n"
            f"🎤 **{track_info['name']}**\n"
            f"👨‍🎤 *by {track_info['artist']}*\n"
            f"⏱️ *Duration: {track_info['duration']}*\n\n"
            f"🎯 *Choose your preferred quality:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"Error handling single track: {e}")
        await processing_msg.edit_text(
            "🚫 *Error retrieving track information.*\n\n"
            "Please try again later! 🔄",
            parse_mode=ParseMode.MARKDOWN
        )

async def handle_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE, playlist_id: str, processing_msg):
    """Handle playlist download."""
    try:
        # Get playlist info
        playlist_info = await spotify_client.get_playlist_info(playlist_id)
        
        if not playlist_info:
            await processing_msg.edit_text(
                "🚫 *Playlist not found!*\n\n"
                "Please check your link and try again. 🔄",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        track_count = len(playlist_info['tracks'])
        
        # Create quality selection for playlist
        keyboard = []
        for quality_text, quality_value in QUALITY_OPTIONS.items():
            button = InlineKeyboardButton(
                f"📥 {quality_text}", 
                callback_data=f"download_playlist_{playlist_id}_{quality_value}"
            )
            keyboard.append([button])
        keyboard.append([InlineKeyboardButton("🚫 Cancel", callback_data="cancel_download")])
        
        await processing_msg.edit_text(
            f"🎧 *Playlist Found!*\n\n"
            f"🎼 **{playlist_info['name']}**\n"
            f"👨‍🎤 *by {playlist_info['owner']}*\n"
            f"🎶 *{track_count} tracks*\n\n"
            f"🎯 *Choose quality to download all {track_count} tracks:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # Store playlist info
        context.user_data['current_playlist'] = playlist_info
        context.user_data['processing_msg_id'] = processing_msg.message_id
        
    except Exception as e:
        logger.error(f"Error handling playlist: {e}")
        await processing_msg.edit_text(
            "🚫 *Error retrieving playlist information.*\n\n"
            "Please try again later! 🔄",
            parse_mode=ParseMode.MARKDOWN
        )

async def handle_album(update: Update, context: ContextTypes.DEFAULT_TYPE, album_id: str, processing_msg):
    """Handle album download."""
    try:
        # Get album info
        album_info = await spotify_client.get_album_info(album_id)
        
        if not album_info:
            await processing_msg.edit_text(
                "🚫 *Album not found!*\n\n"
                "Please check your link and try again. 🔄",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        track_count = len(album_info['tracks'])
        
        # Create quality selection for album
        keyboard = []
        for quality_text, quality_value in QUALITY_OPTIONS.items():
            button = InlineKeyboardButton(
                f"💿 {quality_text}", 
                callback_data=f"download_album_{album_id}_{quality_value}"
            )
            keyboard.append([button])
        keyboard.append([InlineKeyboardButton("🚫 Cancel", callback_data="cancel_download")])
        
        await processing_msg.edit_text(
            f"💽 *Album Found!*\n\n"
            f"🎼 **{album_info['name']}**\n"
            f"👨‍🎤 *by {album_info['artist']}*\n"
            f"🎶 *{track_count} tracks*\n\n"
            f"🎯 *Choose quality to download all {track_count} tracks:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # Store album info
        context.user_data['current_album'] = album_info
        context.user_data['processing_msg_id'] = processing_msg.message_id
        
    except Exception as e:
        logger.error(f"Error handling album: {e}")
        await processing_msg.edit_text(
            "🚫 *Error retrieving album information.*\n\n"
            "Please try again later! 🔄",
            parse_mode=ParseMode.MARKDOWN
        )

async def handle_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button callbacks."""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    if callback_data == "main_menu":
        await show_main_menu(query, context)
    elif callback_data == "help":
        await show_help_info(query, context)
    elif callback_data == "try_demo":
        await show_demo_options(query, context)
    elif callback_data == "get_demo_url":
        await provide_demo_url(query, context)
    elif callback_data == "share_bot":
        await show_share_info(query, context)
    elif callback_data.startswith("quality_"):
        await handle_quality_selection(query, context)
    elif callback_data.startswith("download_"):
        await handle_download_request(query, context)
    elif callback_data == "cancel_download":
        await cancel_download(query, context)
    else:
        await query.message.reply_text("🤔 Unknown action. Please try again!")

async def show_main_menu(query, context):
    """Show main menu."""
    keyboard = create_main_keyboard()
    
    await query.edit_message_text(
        BOT_WELCOME,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_help_info(query, context):
    """Show help information."""
    keyboard = [[InlineKeyboardButton("🏠 Back to Main Menu", callback_data="main_menu")]]
    
    await query.edit_message_text(
        BOT_HELP,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_demo_options(query, context):
    """Show demo options."""
    keyboard = [
        [InlineKeyboardButton("🎲 Get Random Demo URL", callback_data="get_demo_url")],
        [InlineKeyboardButton("🏠 Back to Main Menu", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        "🎪 *Demo Mode*\n\n"
        "Test the bot with popular tracks! 🎶\n\n"
        "Click below to get a random demo link that you can copy and test! ✨",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def provide_demo_url(query, context):
    """Provide a random demo URL."""
    demo_url = demo_songs.get_random_demo_url()
    
    keyboard = [
        [InlineKeyboardButton("🎲 Another Demo URL", callback_data="get_demo_url")],
        [InlineKeyboardButton("🏠 Back to Main Menu", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        f"🎯 *Here's your demo link!*\n\n"
        f"`{demo_url}`\n\n"
        f"📋 *Tap to copy the link above, then send it back to me to test the download!* ✨\n\n"
        f"🔄 Want another demo link?",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_share_info(query, context):
    """Show bot sharing information."""
    bot_username = context.bot.username
    share_text = f"🎶 Check out this amazing MusicFlow Bot! @{bot_username} 🎶"
    share_url = f"https://t.me/share/url?url=https://t.me/{bot_username}&text={share_text}"
    
    keyboard = [
        [InlineKeyboardButton("📤 Share with Friends", url=share_url)],
        [InlineKeyboardButton("🏠 Back to Main Menu", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        "📢 *Share MusicFlow Bot!*\n\n"
        "Help your friends discover seamless music downloads! 🎶✨\n\n"
        "Click the button below to share:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_quality_selection(query, context):
    """Handle quality selection for downloads."""
    quality = query.data.replace("quality_", "")
    track_info = context.user_data.get('current_track')
    
    if not track_info:
        await query.edit_message_text("❌ Session expired. Please send the link again!")
        return
    
    # Start download
    await start_track_download(query, context, track_info, quality)

async def start_track_download(query, context, track_info, quality):
    """Start downloading a single track."""
    # Remove keyboard (bubble effect)
    await query.edit_message_text(
        f"⬇️ *Downloading...*\n\n"
        f"🎶 **{track_info['name']}**\n"
        f"👨‍🎤 *by {track_info['artist']}*\n"
        f"🎯 *Quality: {quality}kbps*\n\n"
        f"⏳ Finding and processing your track...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        # Process download
        file_path = await audio_processor.download_track(track_info, quality)
        
        if file_path:
            # Send the file
            await context.bot.send_audio(
                chat_id=query.message.chat_id,
                audio=open(file_path, 'rb'),
                title=track_info['name'],
                performer=track_info['artist'],
                duration=track_info['duration_ms'] // 1000,
                caption=f"🎶 **{track_info['name']}** by *{track_info['artist']}*",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Update message to show completion
            await query.edit_message_text(
                f"✅ *Download Complete!*\n\n"
                f"🎶 **{track_info['name']}**\n"
                f"👨‍🎤 *by {track_info['artist']}*\n\n"
                f"Enjoy your music! 🎧✨",
                parse_mode=ParseMode.MARKDOWN
            )
            
        else:
            raise Exception("Download failed")
            
    except Exception as e:
        logger.error(f"Download error: {e}")
        await query.edit_message_text(
            f"❌ *Download failed!*\n\n"
            f"🎶 **{track_info['name']}**\n"
            f"👨‍🎤 *by {track_info['artist']}*\n\n"
            f"Please try again later. 🔄",
            parse_mode=ParseMode.MARKDOWN
        )

async def handle_download_request(query, context):
    """Handle playlist/album download requests with quality."""
    if query.data.startswith("download_playlist_"):
        parts = query.data.split("_")
        if len(parts) >= 4:  # download_playlist_id_quality
            quality = parts[-1]
            playlist_info = context.user_data.get('current_playlist')
            if playlist_info:
                await start_playlist_download(query, context, playlist_info, quality)
    elif query.data.startswith("download_album_"):
        parts = query.data.split("_")
        if len(parts) >= 4:  # download_album_id_quality
            quality = parts[-1]
            album_info = context.user_data.get('current_album')
            if album_info:
                await start_album_download(query, context, album_info, quality)

async def start_playlist_download(query, context, playlist_info, quality):
    """Start downloading playlist tracks with selected quality."""
    tracks = playlist_info['tracks']
    total_tracks = len(tracks)
    
    await query.edit_message_text(
        f"🚀 *Starting Playlist Download*\n\n"
        f"🎧 **{playlist_info['name']}**\n"
        f"🎶 *Processing {total_tracks} tracks...*\n"
        f"🎯 *Quality: {quality}kbps*\n\n"
        f"⏳ Sit back and enjoy while I get your music! 🎶",
        parse_mode=ParseMode.MARKDOWN
    )
    
    success_count = 0
    for i, track in enumerate(tracks, 1):
        try:
            # Update progress
            await query.edit_message_text(
                f"💫 *Downloading Playlist*\n\n"
                f"🎧 **{playlist_info['name']}**\n"
                f"🎶 *Track {i}/{total_tracks}*\n"
                f"🔥 **{track['name']}** by *{track['artist']}*\n\n"
                f"Progress: {'█' * (i * 10 // total_tracks)}{'░' * (10 - i * 10 // total_tracks)} {i * 100 // total_tracks}%",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Download track with selected quality
            file_path = await audio_processor.download_track(track, quality)
            
            if file_path:
                await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=open(file_path, 'rb'),
                    title=track['name'],
                    performer=track['artist'],
                    caption=f"💎 **{track['name']}** by *{track['artist']}*\n🎧 From playlist: *{playlist_info['name']}*",
                    parse_mode=ParseMode.MARKDOWN
                )
                success_count += 1
                
        except Exception as e:
            logger.error(f"Error downloading track {track['name']}: {e}")
            continue
    
    # Final summary
    await query.edit_message_text(
        f"🎉 *Playlist Download Complete!*\n\n"
        f"🎧 **{playlist_info['name']}**\n"
        f"💎 *Successfully downloaded: {success_count}/{total_tracks} tracks*\n\n"
        f"Enjoy your amazing music collection! 🎶✨",
        parse_mode=ParseMode.MARKDOWN
    )

async def start_album_download(query, context, album_info, quality):
    """Start downloading album tracks."""
    tracks = album_info['tracks']
    total_tracks = len(tracks)
    
    await query.edit_message_text(
        f"🚀 *Starting Album Download*\n\n"
        f"💽 **{album_info['name']}**\n"
        f"🎶 *Processing {total_tracks} tracks...*\n"
        f"🎯 *Quality: {quality}kbps*\n\n"
        f"⏳ Sit back and enjoy while I get your music! 🎶",
        parse_mode=ParseMode.MARKDOWN
    )
    
    success_count = 0
    for i, track in enumerate(tracks, 1):
        try:
            # Update progress
            await query.edit_message_text(
                f"💫 *Downloading Album*\n\n"
                f"💽 **{album_info['name']}**\n"
                f"🎶 *Track {i}/{total_tracks}*\n"
                f"🔥 **{track['name']}** by *{track['artist']}*\n\n"
                f"Progress: {'█' * (i * 10 // total_tracks)}{'░' * (10 - i * 10 // total_tracks)} {i * 100 // total_tracks}%",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Download track with selected quality
            file_path = await audio_processor.download_track(track, quality)
            
            if file_path:
                await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=open(file_path, 'rb'),
                    title=track['name'],
                    performer=track['artist'],
                    caption=f"💎 **{track['name']}** by *{track['artist']}*\n💽 From album: *{album_info['name']}*",
                    parse_mode=ParseMode.MARKDOWN
                )
                success_count += 1
                
        except Exception as e:
            logger.error(f"Error downloading track {track['name']}: {e}")
            continue
    
    # Final summary
    await query.edit_message_text(
        f"🎉 *Album Download Complete!*\n\n"
        f"💽 **{album_info['name']}**\n"
        f"💎 *Successfully downloaded: {success_count}/{total_tracks} tracks*\n\n"
        f"Enjoy your amazing music collection! 🎶✨",
        parse_mode=ParseMode.MARKDOWN
    )

async def cancel_download(query, context):
    """Cancel download process."""
    await query.edit_message_text(
        "🚫 *Download Cancelled*\n\n"
        "No worries! Feel free to try again anytime. 🎵",
        parse_mode=ParseMode.MARKDOWN
    )
"""
Spotify API Client
Handles all Spotify API interactions for metadata extraction.
"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import logging
import asyncio
from typing import Dict, List, Optional
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

logger = logging.getLogger(__name__)

class SpotifyClient:
    """Client for interacting with Spotify Web API."""
    
    def __init__(self):
        """Initialize Spotify client with credentials."""
        try:
            client_credentials_manager = SpotifyClientCredentials(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET
            )
            self.sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
            logger.info("Spotify client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Spotify client: {e}")
            self.sp = None
    
    async def get_track_info(self, track_id: str) -> Optional[Dict]:
        """
        Get track information from Spotify.
        
        Args:
            track_id: Spotify track ID
            
        Returns:
            Dictionary containing track information or None if failed
        """
        if not self.sp:
            logger.error("Spotify client not initialized")
            return None
            
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            track = await loop.run_in_executor(None, self.sp.track, track_id)
            
            # Extract relevant information
            track_info = {
                'id': track['id'],
                'name': track['name'],
                'artist': ', '.join([artist['name'] for artist in track['artists']]),
                'album': track['album']['name'],
                'duration': self._format_duration(track['duration_ms']),
                'duration_ms': track['duration_ms'],
                'popularity': track['popularity'],
                'preview_url': track.get('preview_url'),
                'external_urls': track['external_urls'],
                'release_date': track['album']['release_date'],
                'image_url': track['album']['images'][0]['url'] if track['album']['images'] else None
            }
            
            logger.info(f"Successfully retrieved track info for: {track_info['name']}")
            return track_info
            
        except Exception as e:
            logger.error(f"Error retrieving track info for {track_id}: {e}")
            return None
    
    async def get_playlist_info(self, playlist_id: str) -> Optional[Dict]:
        """
        Get playlist information from Spotify.
        
        Args:
            playlist_id: Spotify playlist ID
            
        Returns:
            Dictionary containing playlist information or None if failed
        """
        if not self.sp:
            logger.error("Spotify client not initialized")
            return None
            
        try:
            loop = asyncio.get_event_loop()
            
            # Get playlist basic info
            playlist = await loop.run_in_executor(None, self.sp.playlist, playlist_id)
            
            # Get all tracks (handle pagination)
            tracks = []
            results = playlist['tracks']
            
            while results:
                for item in results['items']:
                    if item['track'] and item['track']['type'] == 'track':
                        track = item['track']
                        track_info = {
                            'id': track['id'],
                            'name': track['name'],
                            'artist': ', '.join([artist['name'] for artist in track['artists']]),
                            'album': track['album']['name'],
                            'duration': self._format_duration(track['duration_ms']),
                            'duration_ms': track['duration_ms'],
                            'popularity': track['popularity']
                        }
                        tracks.append(track_info)
                
                # Get next page if available
                if results['next']:
                    results = await loop.run_in_executor(None, self.sp.next, results)
                else:
                    results = None
            
            playlist_info = {
                'id': playlist['id'],
                'name': playlist['name'],
                'description': playlist.get('description', ''),
                'owner': playlist['owner']['display_name'],
                'tracks': tracks,
                'total_tracks': len(tracks),
                'followers': playlist['followers']['total'],
                'image_url': playlist['images'][0]['url'] if playlist['images'] else None
            }
            
            logger.info(f"Successfully retrieved playlist info: {playlist_info['name']} ({len(tracks)} tracks)")
            return playlist_info
            
        except Exception as e:
            logger.error(f"Error retrieving playlist info for {playlist_id}: {e}")
            return None
    
    async def get_album_info(self, album_id: str) -> Optional[Dict]:
        """
        Get album information from Spotify.
        
        Args:
            album_id: Spotify album ID
            
        Returns:
            Dictionary containing album information or None if failed
        """
        if not self.sp:
            logger.error("Spotify client not initialized")
            return None
            
        try:
            loop = asyncio.get_event_loop()
            
            # Get album info
            album = await loop.run_in_executor(None, self.sp.album, album_id)
            
            # Extract track information
            tracks = []
            for track in album['tracks']['items']:
                track_info = {
                    'id': track['id'],
                    'name': track['name'],
                    'artist': ', '.join([artist['name'] for artist in track['artists']]),
                    'album': album['name'],
                    'duration': self._format_duration(track['duration_ms']),
                    'duration_ms': track['duration_ms'],
                    'track_number': track['track_number']
                }
                tracks.append(track_info)
            
            album_info = {
                'id': album['id'],
                'name': album['name'],
                'artist': ', '.join([artist['name'] for artist in album['artists']]),
                'tracks': tracks,
                'total_tracks': album['total_tracks'],
                'release_date': album['release_date'],
                'genres': album.get('genres', []),
                'popularity': album['popularity'],
                'image_url': album['images'][0]['url'] if album['images'] else None
            }
            
            logger.info(f"Successfully retrieved album info: {album_info['name']} ({len(tracks)} tracks)")
            return album_info
            
        except Exception as e:
            logger.error(f"Error retrieving album info for {album_id}: {e}")
            return None
    
    async def search_track(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for tracks on Spotify.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of track dictionaries
        """
        if not self.sp:
            logger.error("Spotify client not initialized")
            return []
            
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None, 
                lambda: self.sp.search(q=query, type='track', limit=limit)
            )
            
            tracks = []
            for track in results['tracks']['items']:
                track_info = {
                    'id': track['id'],
                    'name': track['name'],
                    'artist': ', '.join([artist['name'] for artist in track['artists']]),
                    'album': track['album']['name'],
                    'duration': self._format_duration(track['duration_ms']),
                    'duration_ms': track['duration_ms'],
                    'popularity': track['popularity'],
                    'external_urls': track['external_urls']
                }
                tracks.append(track_info)
            
            logger.info(f"Search returned {len(tracks)} results for query: {query}")
            return tracks
            
        except Exception as e:
            logger.error(f"Error searching tracks for query '{query}': {e}")
            return []
    
    def _format_duration(self, duration_ms: int) -> str:
        """
        Format duration from milliseconds to MM:SS format.
        
        Args:
            duration_ms: Duration in milliseconds
            
        Returns:
            Formatted duration string
        """
        seconds = duration_ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"
"""
Utility Functions
Contains helper functions for the Telegram music bot.
"""

import re
import logging
from typing import List, Tuple, Optional
from telegram import InlineKeyboardButton
from config import QUALITY_OPTIONS

logger = logging.getLogger(__name__)

def extract_spotify_id(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract Spotify ID and content type from a Spotify URL.
    
    Args:
        url: Spotify URL
        
    Returns:
        Tuple of (spotify_id, content_type) or (None, None) if invalid
    """
    try:
        # Regular expression patterns for different Spotify URL formats
        patterns = {
            'track': r'spotify\.com/track/([a-zA-Z0-9]+)',
            'playlist': r'spotify\.com/playlist/([a-zA-Z0-9]+)',
            'album': r'spotify\.com/album/([a-zA-Z0-9]+)',
        }
        
        # Also handle spotify: URI format
        uri_patterns = {
            'track': r'spotify:track:([a-zA-Z0-9]+)',
            'playlist': r'spotify:playlist:([a-zA-Z0-9]+)',
            'album': r'spotify:album:([a-zA-Z0-9]+)',
        }
        
        # Try web URL patterns first
        for content_type, pattern in patterns.items():
            match = re.search(pattern, url)
            if match:
                spotify_id = match.group(1)
                logger.info(f"Extracted {content_type} ID: {spotify_id}")
                return spotify_id, content_type
        
        # Try URI patterns
        for content_type, pattern in uri_patterns.items():
            match = re.search(pattern, url)
            if match:
                spotify_id = match.group(1)
                logger.info(f"Extracted {content_type} ID from URI: {spotify_id}")
                return spotify_id, content_type
        
        logger.warning(f"No valid Spotify ID found in URL: {url}")
        return None, None
        
    except Exception as e:
        logger.error(f"Error extracting Spotify ID from URL {url}: {e}")
        return None, None

def create_quality_keyboard(track_id: str) -> List[List[InlineKeyboardButton]]:
    """
    Create inline keyboard for quality selection in a better grid layout.
    
    Args:
        track_id: Spotify track ID
        
    Returns:
        List of keyboard button rows
    """
    keyboard = []
    
    # Add quality option buttons in rows of 2
    quality_buttons = []
    for quality_text, quality_value in QUALITY_OPTIONS.items():
        button = InlineKeyboardButton(
            quality_text, 
            callback_data=f"quality_{quality_value}"
        )
        quality_buttons.append(button)
    
    # Arrange in rows of 2 buttons
    for i in range(0, len(quality_buttons), 2):
        if i + 1 < len(quality_buttons):
            keyboard.append([quality_buttons[i], quality_buttons[i + 1]])
        else:
            keyboard.append([quality_buttons[i]])
    
    # Add cancel button on its own row
    keyboard.append([InlineKeyboardButton("🚫 Cancel", callback_data="cancel_download")])
    
    return keyboard

def create_main_keyboard() -> List[List[InlineKeyboardButton]]:
    """
    Create main menu inline keyboard with better layout.
    
    Returns:
        List of keyboard button rows
    """
    keyboard = [
        [InlineKeyboardButton("🎪 Try Demo", callback_data="try_demo"), 
         InlineKeyboardButton("💡 Help", callback_data="help")],
        [InlineKeyboardButton("🚀 Share Bot", callback_data="share_bot")]
    ]
    
    return keyboard

def validate_spotify_url(url: str) -> bool:
    """
    Validate if a URL is a valid Spotify URL.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid Spotify URL, False otherwise
    """
    spotify_patterns = [
        r'https?://open\.spotify\.com/(track|playlist|album)/[a-zA-Z0-9]+',
        r'spotify:(track|playlist|album):[a-zA-Z0-9]+'
    ]
    
    for pattern in spotify_patterns:
        if re.match(pattern, url):
            return True
    
    return False

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    size_index = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and size_index < len(size_names) - 1:
        size /= 1024.0
        size_index += 1
    
    return f"{size:.1f} {size_names[size_index]}"

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove invalid characters for file systems
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')
    
    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    
    return sanitized

def create_progress_bar(current: int, total: int, length: int = 10) -> str:
    """
    Create a progress bar string.
    
    Args:
        current: Current progress value
        total: Total value
        length: Length of progress bar
        
    Returns:
        Progress bar string
    """
    if total == 0:
        return "░" * length
    
    progress = min(current / total, 1.0)
    filled_length = int(length * progress)
    
    bar = "█" * filled_length + "░" * (length - filled_length)
    percentage = int(progress * 100)
    
    return f"{bar} {percentage}%"

def is_valid_quality(quality: str) -> bool:
    """
    Check if quality value is valid.
    
    Args:
        quality: Quality string to validate
        
    Returns:
        True if valid, False otherwise
    """
    valid_qualities = ["128", "192", "320"]
    return quality in valid_qualities

def truncate_text(text: str, max_length: int = 50) -> str:
    """
    Truncate text to specified length with ellipsis.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."

def escape_markdown(text: str) -> str:
    """
    Escape markdown special characters.
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text
    """
    # Characters that need escaping in Telegram markdown
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def create_search_query(track_name: str, artist_name: str) -> str:
    """
    Create optimized search query for audio search.
    
    Args:
        track_name: Name of the track
        artist_name: Name of the artist
        
    Returns:
        Optimized search query
    """
    # Clean track name
    track_clean = re.sub(r'\([^)]*\)', '', track_name)  # Remove parentheses content
    track_clean = re.sub(r'\[[^\]]*\]', '', track_clean)  # Remove brackets content
    track_clean = re.sub(r'\s+', ' ', track_clean).strip()  # Clean whitespace
    
    # Clean artist name
    artist_clean = re.sub(r'\([^)]*\)', '', artist_name)
    artist_clean = re.sub(r'\[[^\]]*\]', '', artist_clean)
    artist_clean = re.sub(r'\s+', ' ', artist_clean).strip()
    
    # Create search query
    search_query = f"{track_clean} {artist_clean}"
    
    logger.info(f"Created search query: {search_query}")
    return search_query
