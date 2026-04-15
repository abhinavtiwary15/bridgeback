"""
BridgeBack — Layer 3: Community Event Matcher
Queries Meetup API + Nominatim (OpenStreetMap) for local events
matching the user's interests and location.
No API key required for Nominatim.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import requests

from config import MEETUP_API_KEY, USER_LOCATION

# ── Geocoding (Nominatim / OpenStreetMap — free, no key) ──────────────────────


def geocode_location(location_str: str) -> Optional[Dict]:
    """
    Convert city name or address string to lat/lon.
    Returns {"lat": float, "lon": float, "display_name": str} or None.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": location_str, "format": "json", "limit": 1}
    headers = {"User-Agent": "BridgeBack/1.0 (loneliness-intervention-app)"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=5)
        data = r.json()
        if data:
            return {
                "lat": float(data[0]["lat"]),
                "lon": float(data[0]["lon"]),
                "display_name": data[0]["display_name"],
            }
    except Exception:
        pass
    return None


# ── Meetup API ─────────────────────────────────────────────────────────────────

_INTEREST_TO_TOPICS = {
    "board games": ["board-games", "games"],
    "hiking": ["hiking", "outdoors"],
    "reading": ["book-clubs", "literature"],
    "coding": ["tech", "software-development"],
    "yoga": ["yoga", "wellness"],
    "photography": ["photography"],
    "music": ["music"],
    "art": ["arts-culture"],
    "cooking": ["food-and-drink"],
    "running": ["running"],
    "language": ["language-learning"],
    "meditation": ["meditation", "mindfulness"],
    "volunteering": ["community", "volunteering"],
    "sports": ["sports-recreation"],
    "films": ["film", "cinema"],
    "travel": ["travel"],
}


def _get_meetup_events(lat: float, lon: float, topics: List[str]) -> List[Dict]:
    """Query Meetup API for upcoming local events."""
    if not MEETUP_API_KEY:
        return []

    url = "https://api.meetup.com/find/upcoming_events"
    all_events = []

    for topic in topics[:3]:  # limit API calls
        params = {
            "key": MEETUP_API_KEY,
            "lat": lat,
            "lon": lon,
            "radius": 10,  # km
            "topic_category": topic,
            "page": 5,
        }
        try:
            r = requests.get(url, params=params, timeout=8)
            data = r.json()
            events = data.get("events", [])
            all_events.extend(events)
        except Exception:
            continue

    return all_events


def _format_event(event: Dict) -> Dict:
    """Normalise a Meetup API event dict."""
    venue = event.get("venue", {})
    group = event.get("group", {})
    return {
        "name": event.get("name", "Community Event"),
        "group_name": group.get("name", ""),
        "date": event.get("local_date", ""),
        "time": event.get("local_time", ""),
        "venue": venue.get("name", ""),
        "city": venue.get("city", ""),
        "rsvp_count": event.get("yes_rsvp_count", 0),
        "registration_link": event.get("link", ""),
        "description": event.get("description", "")[:200],
    }


# ── Fallback mock events (when no API key) ────────────────────────────────────

_MOCK_EVENTS = [
    {
        "name": "Board Game Night",
        "group_name": "Local Board Gamers",
        "date": "This Thursday",
        "time": "7:00 PM",
        "venue": "Community Café",
        "city": USER_LOCATION or "your city",
        "rsvp_count": 12,
        "registration_link": "https://www.meetup.com",
        "description": "Casual board game evening. All skill levels welcome.",
    },
    {
        "name": "Weekend Hiking Group",
        "group_name": "City Hikers",
        "date": "This Sunday",
        "time": "8:00 AM",
        "venue": "Central Park / Nearest Trail",
        "city": USER_LOCATION or "your city",
        "rsvp_count": 8,
        "registration_link": "https://www.meetup.com",
        "description": "Easy 5km morning hike, perfect for meeting people.",
    },
    {
        "name": "Book Club Monthly Meeting",
        "group_name": "The Reading Circle",
        "date": "Next Saturday",
        "time": "4:00 PM",
        "venue": "Public Library",
        "city": USER_LOCATION or "your city",
        "rsvp_count": 6,
        "registration_link": "https://www.meetup.com",
        "description": "Low-key, friendly book discussion. New members welcome.",
    },
]


# ── Public API ────────────────────────────────────────────────────────────────


def find_events(
    interests: List[str],
    location: str = "",
    limit: int = 3,
) -> List[Dict]:
    """
    Find local community events matching given interests.
    Returns list of formatted event dicts.
    Falls back to mock events if API key missing or location unavailable.
    """
    location = location or USER_LOCATION
    if not location:
        return _MOCK_EVENTS[:limit]

    geo = geocode_location(location)
    if not geo:
        return _MOCK_EVENTS[:limit]

    topics = []
    for interest in interests:
        for key, vals in _INTEREST_TO_TOPICS.items():
            if key in interest.lower():
                topics.extend(vals)

    if not topics:
        topics = ["community", "social"]

    raw_events = _get_meetup_events(geo["lat"], geo["lon"], topics)
    if not raw_events:
        return _MOCK_EVENTS[:limit]

    return [_format_event(e) for e in raw_events[:limit]]
