# Emby Media Management Toolkit

A suite of Python scripts for automating Emby media server management, media organization, and playlist synchronization with Spotify, Emby, Jellyfin and Navidrome

## Overview

This project provides a robust set of tools for managing your Emby media server, including media organization, metadata enhancement, playlist synchronization, and various automation tasks. It runs as a containerized application with scheduled jobs to keep your media library well-organized and up-to-date.

## Features

### Media Organization

- **Movies**: Automatically organize downloaded movies and move them to your media server
- **TV Shows**: Sort and organize TV episodes with Sonarr integration
- **Music**: Organize music albums and tracks with proper metadata

### Spotify Integration

- **Playlist Synchronization**: Keep Emby playlists in sync with your Spotify playlists
- **Track Download**: Find and download missing songs from your playlists
- **Liked Songs Sync**: Synchronize your Spotify liked songs to Emby
- **Music Organization**: Properly sort and tag downloaded Spotify tracks

### Emby Management

- **Playlist Management**: Delete duplicate playlists and share playlists between users
- **Metadata Enhancement**: Update and improve metadata for your media
- **Smart Playlists**: Generate series mix playlists and other dynamic collections

### Utilities

- **Lyrics Retrieval**: Find and attach lyrics to your music files
- **Metadata Identification**: Identify music with missing metadata
- **Artist Folder Management**: Merge similar artist folders to organize your music library

## Prerequisites

- Docker
- Docker Compose (recommended for easy deployment)
- Emby Media Server instance
- Spotify Developer account (for playlist integration)
- Sonarr (for TV show management)

## Installation

### Using Docker (Recommended)

1. Clone this repository:

   ```bash
   git clone https://github.com/yourusername/emby-scripts.git
   cd emby-scripts
   ```

2. Build and start the Docker container:

   ```bash
   docker build -t emby-scripts .
   docker run -d --name emby-scripts emby-scripts
   ```

### Using Docker Compose

Create a `docker-compose.yml` file with the following content:

```yaml
version: "3"
services:
  emby-scripts:
    build: .
    volumes:
      - ./config:/app/config
      - /path/to/your/media:/media
    restart: unless-stopped
    env_file:
      - .env
```

Start the services:

```bash
docker-compose up -d
```

## Configuration

Create a `.env` file with the following variables:

```
# Emby Configuration
EMBY_URL=http://your-emby-server:8096
EMBY_USERNAME=your_username
EMBY_PASSWORD=your_password

# Spotify Configuration
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://localhost
SPOTIFY_SCOPE=playlist-read-private,user-library-read

# Sonarr Configuration
SONARR_URL=http://your-sonarr:8989
SONARR_API_KEY=your_api_key

# Media Directories
MOVIES_DOWNLOAD_DIR=/path/to/downloads/movies
MOVIES_ORGANIZED_DIR=/path/to/organized/movies
TV_DOWNLOAD_DIR=/path/to/downloads/tv
TV_ORGANIZED_DIR=/path/to/organized/tv
MUSIC_DOWNLOAD_DIR=/path/to/downloads/music
MUSIC_ORGANIZED_DIR=/path/to/organized/music
MUSIC_STORAGE_DIR=/path/to/media/music
MUSIC_SPOTIFY_DOWNLOAD_DIR=/path/to/spotify/downloads
MUSIC_SPOTIFY_ORGANIZED_DIR=/path/to/spotify/organized
```

## Scheduled Tasks

The application uses cron to schedule various media management tasks:

- Media organization: Sort and organize new downloads
- Playlist synchronization: Keep Emby playlists in sync with Spotify
- Metadata updates: Enhance media metadata periodically

## Local Development

1. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run scripts directly:

   ```bash
   python -m src.main
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License
