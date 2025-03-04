from enum import Enum

class EmbyLibraryItemType(Enum):
    AUDIO = "Audio"
    VIDEO = "Video"
    FOLDER = "Folder"
    EPISODE = "Episode"
    MOVIE = "Movie"
    TRAILER = "Trailer"
    ADULT_VIDEO = "AdultVideo"
    MUSIC_VIDEO = "MusicVideo"
    BOX_SET = "BoxSet"
    MUSIC_ALBUM = "MusicAlbum"
    MUSIC_ARTIST = "MusicArtist"
    SEASON = "Season"
    SERIES = "Series"
    GAME = "Game"
    GAME_SYSTEM = "GameSystem"
    BOOK = "Book"


class EmbyImageType(Enum):
    PRIMARY = "Primary"
    ART = "Art"
    BACKDROP = "Backdrop"
    BANNER = "Banner"
    LOGO = "Logo"
    THUMB = "Thumb"
    DISC = "Disc"
    BOX = "Box"
    SCREENSHOT = "Screenshot"
    MENU = "Menu"
    CHAPTER = "Chapter"