"""tests/fixtures/songs.py — Test data factories for songs"""
import uuid
from app.models.song import Song


SAMPLE_SONGS = [
    {"title": "Kesariya", "artist": "Arijit Singh", "youtube_video_id": "BVBWugH_aFE", "genre": "Bollywood"},
    {"title": "Brown Munde", "artist": "AP Dhillon", "youtube_video_id": "u5M7yGMSFNk", "genre": "Punjabi"},
    {"title": "Calm Down", "artist": "Rema", "youtube_video_id": "WvzYKdHHBws", "genre": "Afrobeats"},
    {"title": "Pasoori", "artist": "Ali Sethi", "youtube_video_id": "Z2rXR5YXUV0", "genre": "Pop"},
    {"title": "Dynamite", "artist": "BTS", "youtube_video_id": "gdZLi9oWNZg", "genre": "K-Pop"},
]


def make_song(venue_id: uuid.UUID, **kwargs) -> Song:
    import random
    base = random.choice(SAMPLE_SONGS).copy()
    base.update(kwargs)
    return Song(venue_id=venue_id, is_enabled=True, is_embeddable=True, **base)
