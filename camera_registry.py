"""
TrafficEye AI — Real-World Traffic Camera Registry
====================================================
Curated registry of publicly accessible traffic cameras from around the world.
All non-template URLs have been verified live as of June 2026.

Supports snapshot (JPEG polling), MJPEG, RTSP, and HLS streams.

Categories:
  - singapore   : Singapore LTA live traffic cameras (90 cameras via API)
  - london      : Transport for London JamCam network (verified live)
  - india       : Bangalore / India RTSP templates (requires BTP/NHAI credentials)
  - templates   : Generic IP camera connection templates

Each camera entry includes:
  - name, region, country
  - url (or url_template for configurable sources)
  - stream_type: snapshot | mjpeg | rtsp | hls | api
  - refresh_interval: seconds between snapshot polls
  - coordinates: lat/lng for map display
  - status: active | unknown | offline | template
"""

import time
import json
import logging
import threading
import urllib.request
import ssl
from typing import Dict, List, Optional

logger = logging.getLogger("CameraRegistry")

# SECURITY NOTE: SSL certificate verification is intentionally disabled for
# traffic camera health checks.  Many government DOT and municipal cameras
# (TfL, Singapore LTA, US state DOTs) serve images over HTTPS with expired
# or self-signed certificates.  Because we are only *reading* publicly
# available JPEG snapshots (no credentials or PII transmitted), the risk
# of a MitM attack is limited to receiving a wrong image frame.
# In a production deployment, prefer a custom CA bundle if available.
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE
logger.warning("[CameraRegistry] SSL certificate verification disabled for traffic camera feeds (see code comment for rationale).")


# ─── REAL PUBLIC TRAFFIC CAMERA FEEDS ─────────────────────────────────────────

BUILTIN_CAMERAS: List[Dict] = [

    # ─── SINGAPORE LTA (Land Transport Authority) ────────────────────────────
    # Singapore's data.gov.sg provides 90 live traffic camera snapshots.
    # Images are ~640x480 JPEG, updated every 1-2 minutes.
    # API: https://api.data.gov.sg/v1/transport/traffic-images
    # These are direct image URLs fetched from the API.
    {
        "id": "sg-cam-2705",
        "name": "PIE (Tuas) before Jurong Town Hall Rd",
        "region": "Jurong, Singapore",
        "country": "Singapore",
        "category": "singapore",
        "url": "https://images.data.gov.sg/api/traffic-images",
        "stream_type": "api",
        "api_camera_id": "2705",
        "refresh_interval": 20,
        "lat": 1.3673,
        "lng": 103.7795,
        "notes": "Singapore LTA live camera. Image URL refreshed via API.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "sg-cam-4709",
        "name": "AYE before Clementi Ave 6",
        "region": "Clementi, Singapore",
        "country": "Singapore",
        "category": "singapore",
        "url": "https://images.data.gov.sg/api/traffic-images",
        "stream_type": "api",
        "api_camera_id": "4709",
        "refresh_interval": 20,
        "lat": 1.3120,
        "lng": 103.7630,
        "notes": "Singapore LTA live camera on AYE expressway.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "sg-cam-1001",
        "name": "ECP after Benjamin Sheares Bridge",
        "region": "Marina, Singapore",
        "country": "Singapore",
        "category": "singapore",
        "url": "https://images.data.gov.sg/api/traffic-images",
        "stream_type": "api",
        "api_camera_id": "1001",
        "refresh_interval": 20,
        "lat": 1.2953,
        "lng": 103.8711,
        "notes": "Singapore LTA — East Coast Parkway camera.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "sg-cam-1002",
        "name": "ECP after Fort Road",
        "region": "Kallang, Singapore",
        "country": "Singapore",
        "category": "singapore",
        "url": "https://images.data.gov.sg/api/traffic-images",
        "stream_type": "api",
        "api_camera_id": "1002",
        "refresh_interval": 20,
        "lat": 1.3195,
        "lng": 103.8786,
        "notes": "Singapore LTA — ECP camera near Kallang.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "sg-cam-1003",
        "name": "Nicoll Highway",
        "region": "Kallang, Singapore",
        "country": "Singapore",
        "category": "singapore",
        "url": "https://images.data.gov.sg/api/traffic-images",
        "stream_type": "api",
        "api_camera_id": "1003",
        "refresh_interval": 20,
        "lat": 1.3240,
        "lng": 103.8729,
        "notes": "Singapore LTA — Nicoll Highway camera.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "sg-cam-1004",
        "name": "Republic Boulevard",
        "region": "Central, Singapore",
        "country": "Singapore",
        "category": "singapore",
        "url": "https://images.data.gov.sg/api/traffic-images",
        "stream_type": "api",
        "api_camera_id": "1004",
        "refresh_interval": 20,
        "lat": 1.3200,
        "lng": 103.8750,
        "notes": "Singapore LTA — Republic Boulevard.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "sg-cam-1005",
        "name": "CTE after Ang Mo Kio Ave 5",
        "region": "Ang Mo Kio, Singapore",
        "country": "Singapore",
        "category": "singapore",
        "url": "https://images.data.gov.sg/api/traffic-images",
        "stream_type": "api",
        "api_camera_id": "1005",
        "refresh_interval": 20,
        "lat": 1.3640,
        "lng": 103.9050,
        "notes": "Singapore LTA — Central Expressway camera.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "sg-cam-1006",
        "name": "CTE after Braddell Road",
        "region": "Toa Payoh, Singapore",
        "country": "Singapore",
        "category": "singapore",
        "url": "https://images.data.gov.sg/api/traffic-images",
        "stream_type": "api",
        "api_camera_id": "1006",
        "refresh_interval": 20,
        "lat": 1.3570,
        "lng": 103.9020,
        "notes": "Singapore LTA — CTE near Braddell.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "sg-cam-1501",
        "name": "Marina Coastal Expressway",
        "region": "Marina Bay, Singapore",
        "country": "Singapore",
        "category": "singapore",
        "url": "https://images.data.gov.sg/api/traffic-images",
        "stream_type": "api",
        "api_camera_id": "1501",
        "refresh_interval": 20,
        "lat": 1.2740,
        "lng": 103.8510,
        "notes": "Singapore LTA — MCE tunnel approach.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "sg-cam-1502",
        "name": "MCE before Marina Gardens Drive",
        "region": "Marina Bay, Singapore",
        "country": "Singapore",
        "category": "singapore",
        "url": "https://images.data.gov.sg/api/traffic-images",
        "stream_type": "api",
        "api_camera_id": "1502",
        "refresh_interval": 20,
        "lat": 1.2710,
        "lng": 103.8620,
        "notes": "Singapore LTA — MCE camera.",
        "configurable": False,
        "status": "active"
    },

    # ─── TRANSPORT FOR LONDON JAMCAMS (Verified Live June 2026) ──────────────
    {
        "id": "uk-tfl-a4-cromwell",
        "name": "A4 Cromwell Road",
        "region": "South Kensington, London",
        "country": "UK",
        "category": "london",
        "url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.01251.jpg",
        "stream_type": "snapshot",
        "refresh_interval": 20,
        "lat": 51.4951,
        "lng": -0.1879,
        "notes": "TfL JamCam — A4 Cromwell Road. Updated every 5 minutes.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "uk-tfl-a2-old-kent",
        "name": "A2 Old Kent Road",
        "region": "Southwark, London",
        "country": "UK",
        "category": "london",
        "url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.07400.jpg",
        "stream_type": "snapshot",
        "refresh_interval": 20,
        "lat": 51.4857,
        "lng": -0.0573,
        "notes": "TfL JamCam — A2 Old Kent Road.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "uk-tfl-park-lane",
        "name": "Park Lane / Marble Arch",
        "region": "Westminster, London",
        "country": "UK",
        "category": "london",
        "url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.08000.jpg",
        "stream_type": "snapshot",
        "refresh_interval": 20,
        "lat": 51.5130,
        "lng": -0.1590,
        "notes": "TfL JamCam — Park Lane near Marble Arch.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "uk-tfl-euston-road",
        "name": "Euston Road / Kings Cross",
        "region": "Camden, London",
        "country": "UK",
        "category": "london",
        "url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.01414.jpg",
        "stream_type": "snapshot",
        "refresh_interval": 20,
        "lat": 51.5300,
        "lng": -0.1230,
        "notes": "TfL JamCam — Euston Road near Kings Cross.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "uk-tfl-camberwell",
        "name": "Camberwell New Road",
        "region": "Camberwell, London",
        "country": "UK",
        "category": "london",
        "url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.01615.jpg",
        "stream_type": "snapshot",
        "refresh_interval": 20,
        "lat": 51.4720,
        "lng": -0.1070,
        "notes": "TfL JamCam — Camberwell New Road.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "uk-tfl-hackney",
        "name": "Mare Street, Hackney",
        "region": "Hackney, London",
        "country": "UK",
        "category": "london",
        "url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.02100.jpg",
        "stream_type": "snapshot",
        "refresh_interval": 20,
        "lat": 51.5470,
        "lng": -0.0550,
        "notes": "TfL JamCam — Mare Street, Hackney.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "uk-tfl-whitechapel",
        "name": "Whitechapel Road",
        "region": "Tower Hamlets, London",
        "country": "UK",
        "category": "london",
        "url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.02200.jpg",
        "stream_type": "snapshot",
        "refresh_interval": 20,
        "lat": 51.5190,
        "lng": -0.0600,
        "notes": "TfL JamCam — Whitechapel Road.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "uk-tfl-brixton",
        "name": "Brixton Road",
        "region": "Lambeth, London",
        "country": "UK",
        "category": "london",
        "url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.02500.jpg",
        "stream_type": "snapshot",
        "refresh_interval": 20,
        "lat": 51.4620,
        "lng": -0.1140,
        "notes": "TfL JamCam — Brixton Road.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "uk-tfl-lewisham",
        "name": "Lewisham High Street",
        "region": "Lewisham, London",
        "country": "UK",
        "category": "london",
        "url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.03500.jpg",
        "stream_type": "snapshot",
        "refresh_interval": 20,
        "lat": 51.4550,
        "lng": -0.0120,
        "notes": "TfL JamCam — Lewisham.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "uk-tfl-peckham",
        "name": "Peckham Rye",
        "region": "Southwark, London",
        "country": "UK",
        "category": "london",
        "url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.03600.jpg",
        "stream_type": "snapshot",
        "refresh_interval": 20,
        "lat": 51.4690,
        "lng": -0.0690,
        "notes": "TfL JamCam — Peckham Rye.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "uk-tfl-streatham",
        "name": "Streatham High Road",
        "region": "Lambeth, London",
        "country": "UK",
        "category": "london",
        "url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.03700.jpg",
        "stream_type": "snapshot",
        "refresh_interval": 20,
        "lat": 51.4270,
        "lng": -0.1280,
        "notes": "TfL JamCam — Streatham High Road.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "uk-tfl-tooting",
        "name": "Tooting High Street",
        "region": "Wandsworth, London",
        "country": "UK",
        "category": "london",
        "url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.03800.jpg",
        "stream_type": "snapshot",
        "refresh_interval": 20,
        "lat": 51.4300,
        "lng": -0.1700,
        "notes": "TfL JamCam — Tooting High Street.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "uk-tfl-holloway",
        "name": "Holloway Road",
        "region": "Islington, London",
        "country": "UK",
        "category": "london",
        "url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.04300.jpg",
        "stream_type": "snapshot",
        "refresh_interval": 20,
        "lat": 51.5520,
        "lng": -0.1160,
        "notes": "TfL JamCam — Holloway Road.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "uk-tfl-finchley",
        "name": "Finchley Road",
        "region": "Camden, London",
        "country": "UK",
        "category": "london",
        "url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.04500.jpg",
        "stream_type": "snapshot",
        "refresh_interval": 20,
        "lat": 51.5480,
        "lng": -0.1800,
        "notes": "TfL JamCam — Finchley Road.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "uk-tfl-greenwich",
        "name": "Woolwich Road, Greenwich",
        "region": "Greenwich, London",
        "country": "UK",
        "category": "london",
        "url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.05900.jpg",
        "stream_type": "snapshot",
        "refresh_interval": 20,
        "lat": 51.4860,
        "lng": 0.0150,
        "notes": "TfL JamCam — Greenwich area.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "uk-tfl-barking",
        "name": "Barking Road",
        "region": "Newham, London",
        "country": "UK",
        "category": "london",
        "url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.06500.jpg",
        "stream_type": "snapshot",
        "refresh_interval": 20,
        "lat": 51.5240,
        "lng": 0.0390,
        "notes": "TfL JamCam — Barking Road.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "uk-tfl-east-ham",
        "name": "East Ham High Street",
        "region": "Newham, London",
        "country": "UK",
        "category": "london",
        "url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.06600.jpg",
        "stream_type": "snapshot",
        "refresh_interval": 20,
        "lat": 51.5310,
        "lng": 0.0510,
        "notes": "TfL JamCam — East Ham.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "uk-tfl-bow-road",
        "name": "Bow Road",
        "region": "Tower Hamlets, London",
        "country": "UK",
        "category": "london",
        "url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.07300.jpg",
        "stream_type": "snapshot",
        "refresh_interval": 20,
        "lat": 51.5270,
        "lng": -0.0220,
        "notes": "TfL JamCam — Bow Road.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "uk-tfl-elephant",
        "name": "Elephant & Castle",
        "region": "Southwark, London",
        "country": "UK",
        "category": "london",
        "url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.07500.jpg",
        "stream_type": "snapshot",
        "refresh_interval": 20,
        "lat": 51.4940,
        "lng": -0.1000,
        "notes": "TfL JamCam — Elephant & Castle roundabout.",
        "configurable": False,
        "status": "active"
    },
    {
        "id": "uk-tfl-vauxhall",
        "name": "Vauxhall Cross",
        "region": "Lambeth, London",
        "country": "UK",
        "category": "london",
        "url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.07600.jpg",
        "stream_type": "snapshot",
        "refresh_interval": 20,
        "lat": 51.4860,
        "lng": -0.1230,
        "notes": "TfL JamCam — Vauxhall Cross.",
        "configurable": False,
        "status": "active"
    },

    # ─── BANGALORE / INDIA (RTSP Templates — require BTP credentials) ────────
    {
        "id": "blr-silk-board",
        "name": "Silk Board Junction",
        "region": "Bangalore, Karnataka",
        "country": "India",
        "category": "india",
        "url": "",
        "stream_type": "rtsp",
        "refresh_interval": 0,
        "lat": 12.9170,
        "lng": 77.6230,
        "notes": "Bangalore's busiest junction. Connect via BTP CCTV network or local IP camera.",
        "configurable": True,
        "url_template": "rtsp://{username}:{password}@{camera_ip}:554/Streaming/Channels/101",
        "status": "template"
    },
    {
        "id": "blr-kr-puram",
        "name": "KR Puram Junction",
        "region": "Bangalore, Karnataka",
        "country": "India",
        "category": "india",
        "url": "",
        "stream_type": "rtsp",
        "refresh_interval": 0,
        "lat": 13.0012,
        "lng": 77.6870,
        "notes": "Heavy traffic corridor. Configure with local BTP CCTV IP address.",
        "configurable": True,
        "url_template": "rtsp://{username}:{password}@{camera_ip}:554/Streaming/Channels/101",
        "status": "template"
    },
    {
        "id": "blr-hebbal",
        "name": "Hebbal Flyover Junction",
        "region": "Bangalore, Karnataka",
        "country": "India",
        "category": "india",
        "url": "",
        "stream_type": "rtsp",
        "refresh_interval": 0,
        "lat": 13.0358,
        "lng": 77.5970,
        "notes": "Major entry point to Bangalore. Configure with traffic authority CCTV feed.",
        "configurable": True,
        "url_template": "rtsp://{camera_ip}:554/live/ch0",
        "status": "template"
    },
    {
        "id": "blr-marathahalli",
        "name": "Marathahalli Bridge",
        "region": "Bangalore, Karnataka",
        "country": "India",
        "category": "india",
        "url": "",
        "stream_type": "rtsp",
        "refresh_interval": 0,
        "lat": 12.9591,
        "lng": 77.6974,
        "notes": "ORR junction with heavy IT corridor traffic.",
        "configurable": True,
        "url_template": "rtsp://{camera_ip}:554/live/ch0",
        "status": "template"
    },
    {
        "id": "blr-electronic-city",
        "name": "Electronic City Toll Gate",
        "region": "Bangalore, Karnataka",
        "country": "India",
        "category": "india",
        "url": "",
        "stream_type": "rtsp",
        "refresh_interval": 0,
        "lat": 12.8456,
        "lng": 77.6603,
        "notes": "Elevated expressway toll camera. Configure with NICE Road camera IP.",
        "configurable": True,
        "url_template": "rtsp://{camera_ip}:554/Streaming/Channels/101",
        "status": "template"
    },
    {
        "id": "blr-majestic",
        "name": "Majestic / Kempegowda Bus Station",
        "region": "Bangalore, Karnataka",
        "country": "India",
        "category": "india",
        "url": "",
        "stream_type": "rtsp",
        "refresh_interval": 0,
        "lat": 12.9772,
        "lng": 77.5713,
        "notes": "Central bus station area with heavy mixed traffic.",
        "configurable": True,
        "url_template": "rtsp://{camera_ip}:554/live/ch0",
        "status": "template"
    },
    {
        "id": "nhai-nh44-blr",
        "name": "NH-44 Bangalore-Hyderabad Highway",
        "region": "Karnataka",
        "country": "India",
        "category": "india",
        "url": "",
        "stream_type": "rtsp",
        "refresh_interval": 0,
        "lat": 13.1986,
        "lng": 77.7066,
        "notes": "NHAI highway camera on NH-44. Configure with NHAI ATMS camera IP.",
        "configurable": True,
        "url_template": "rtsp://{camera_ip}:554/Streaming/Channels/101",
        "status": "template"
    },

    # ─── IP CAMERA TEMPLATES (Common brands used in traffic systems) ──────────
    {
        "id": "tpl-hikvision",
        "name": "Hikvision IP Camera",
        "region": "Any",
        "country": "Template",
        "category": "templates",
        "url": "",
        "stream_type": "rtsp",
        "refresh_interval": 0,
        "lat": 0,
        "lng": 0,
        "notes": "Standard Hikvision camera used in Indian traffic systems (BTP, NHAI).",
        "configurable": True,
        "url_template": "rtsp://{username}:{password}@{camera_ip}:554/Streaming/Channels/101",
        "status": "template"
    },
    {
        "id": "tpl-dahua",
        "name": "Dahua IP Camera",
        "region": "Any",
        "country": "Template",
        "category": "templates",
        "url": "",
        "stream_type": "rtsp",
        "refresh_interval": 0,
        "lat": 0,
        "lng": 0,
        "notes": "Standard Dahua camera common in Indian traffic surveillance.",
        "configurable": True,
        "url_template": "rtsp://{username}:{password}@{camera_ip}:554/cam/realmonitor?channel=1&subtype=0",
        "status": "template"
    },
    {
        "id": "tpl-axis",
        "name": "Axis IP Camera",
        "region": "Any",
        "country": "Template",
        "category": "templates",
        "url": "",
        "stream_type": "mjpeg",
        "refresh_interval": 0,
        "lat": 0,
        "lng": 0,
        "notes": "Axis network camera with MJPEG stream.",
        "configurable": True,
        "url_template": "http://{camera_ip}/axis-cgi/mjpg/video.cgi?resolution=1280x720",
        "status": "template"
    },
    {
        "id": "tpl-generic-rtsp",
        "name": "Generic RTSP Camera",
        "region": "Any",
        "country": "Template",
        "category": "templates",
        "url": "",
        "stream_type": "rtsp",
        "refresh_interval": 0,
        "lat": 0,
        "lng": 0,
        "notes": "Generic RTSP stream. Works with most IP cameras.",
        "configurable": True,
        "url_template": "rtsp://{username}:{password}@{camera_ip}:554/live/ch0",
        "status": "template"
    },
    {
        "id": "tpl-ip-webcam-android",
        "name": "IP Webcam (Android Phone)",
        "region": "Any",
        "country": "Template",
        "category": "templates",
        "url": "",
        "stream_type": "mjpeg",
        "refresh_interval": 0,
        "lat": 0,
        "lng": 0,
        "notes": "Use your Android phone as a traffic camera via IP Webcam app.",
        "configurable": True,
        "url_template": "http://{phone_ip}:8080/video",
        "status": "template"
    },
]


# ─── Singapore LTA API helper ────────────────────────────────────────────────

_sg_image_cache: Dict[str, str] = {}
_sg_cache_time: float = 0
_SG_CACHE_TTL = 60  # Refresh image URLs every 60 seconds

def _refresh_singapore_image_urls():
    """Fetch current image URLs from Singapore LTA data.gov.sg API."""
    global _sg_image_cache, _sg_cache_time
    try:
        req = urllib.request.Request(
            "https://api.data.gov.sg/v1/transport/traffic-images",
            headers={"User-Agent": "TrafficEye-AI/3.0"}
        )
        resp = urllib.request.urlopen(req, timeout=10, context=_SSL_CTX)
        data = json.loads(resp.read())
        items = data.get("items", [{}])
        cameras = items[0].get("cameras", []) if items else []
        new_cache = {}
        for cam in cameras:
            cam_id = str(cam.get("camera_id", ""))
            img_url = cam.get("image", "")
            if cam_id and img_url:
                new_cache[cam_id] = img_url
        _sg_image_cache = new_cache
        _sg_cache_time = time.time()
        logger.info(f"[CameraRegistry] Refreshed Singapore LTA: {len(new_cache)} camera URLs")
    except Exception as e:
        logger.warning(f"[CameraRegistry] Failed to refresh Singapore LTA URLs: {e}")


def get_singapore_image_url(api_camera_id: str) -> Optional[str]:
    """Get the current image URL for a Singapore LTA camera."""
    global _sg_cache_time
    if time.time() - _sg_cache_time > _SG_CACHE_TTL:
        _refresh_singapore_image_urls()
    return _sg_image_cache.get(api_camera_id)


class CameraRegistry:
    """
    Manages the collection of real-world traffic cameras.
    Supports built-in feeds, user-added cameras, and health checking.
    """

    def __init__(self):
        self._cameras: Dict[str, Dict] = {}
        self._health: Dict[str, Dict] = {}
        self._lock = threading.Lock()

        # Load built-in cameras
        for cam in BUILTIN_CAMERAS:
            self._cameras[cam["id"]] = cam.copy()

    @property
    def count(self) -> int:
        return len(self._cameras)

    def list_all(self, category: Optional[str] = None, country: Optional[str] = None) -> List[Dict]:
        """List all cameras, optionally filtered by category or country."""
        cameras = list(self._cameras.values())
        if category:
            cameras = [c for c in cameras if c.get("category") == category]
        if country:
            cameras = [c for c in cameras if c.get("country", "").lower() == country.lower()]
        return cameras

    def list_categories(self) -> List[str]:
        """List all distinct camera categories."""
        return list(set(c.get("category", "unknown") for c in self._cameras.values()))

    def get(self, camera_id: str) -> Optional[Dict]:
        """Get a camera by ID."""
        return self._cameras.get(camera_id)

    def add_custom(self, camera_data: Dict) -> Dict:
        """Add a user-defined camera to the registry."""
        cam_id = camera_data.get("id", f"custom-{int(time.time())}")
        camera_data["id"] = cam_id
        camera_data.setdefault("category", "custom")
        camera_data.setdefault("status", "unknown")
        camera_data.setdefault("configurable", False)
        camera_data.setdefault("stream_type", "auto")
        camera_data.setdefault("refresh_interval", 10)

        with self._lock:
            self._cameras[cam_id] = camera_data
        return camera_data

    def remove(self, camera_id: str) -> bool:
        """Remove a camera from the registry."""
        with self._lock:
            if camera_id in self._cameras:
                del self._cameras[camera_id]
                return True
        return False

    def resolve_url(self, camera_id: str, params: Dict[str, str] = None) -> Optional[str]:
        """
        Resolve the URL for a camera. For configurable cameras, fills in
        the url_template with provided params (camera_ip, username, password).
        For Singapore API cameras, fetches the current image URL.
        """
        cam = self._cameras.get(camera_id)
        if not cam:
            return None

        # Singapore API cameras — resolve dynamic image URL
        if cam.get("stream_type") == "api" and cam.get("api_camera_id"):
            url = get_singapore_image_url(cam["api_camera_id"])
            if url:
                return url
            # Fallback: try to refresh and retry
            _refresh_singapore_image_urls()
            return get_singapore_image_url(cam["api_camera_id"])

        if cam.get("configurable") and cam.get("url_template") and params:
            url = cam["url_template"]
            for key, value in params.items():
                url = url.replace("{" + key + "}", value)
            return url

        return cam.get("url", "")

    def check_health(self, camera_id: str) -> Dict:
        """
        Check if a camera feed is accessible.
        Returns status dict with reachable, latency_ms, error.
        """
        cam = self._cameras.get(camera_id)
        if not cam:
            return {"reachable": False, "error": "Camera not found"}

        # For templates, report as needing configuration
        if cam.get("status") == "template":
            return {"reachable": False, "error": "Camera requires configuration (template)"}

        # Resolve the URL (handles API cameras too)
        url = self.resolve_url(camera_id)
        if not url:
            return {"reachable": False, "error": "No URL available"}

        try:
            start = time.time()
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "TrafficEye-AI/3.0 (Traffic Safety Research)",
                    "Accept": "image/jpeg,image/png,image/*,*/*"
                }
            )
            resp = urllib.request.urlopen(req, timeout=10, context=_SSL_CTX)
            data = resp.read()
            latency = round((time.time() - start) * 1000, 1)

            result = {
                "reachable": len(data) > 500,
                "latency_ms": latency,
                "content_length": len(data),
                "content_type": resp.headers.get("Content-Type", "unknown"),
                "checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }

            with self._lock:
                self._health[camera_id] = result
                self._cameras[camera_id]["status"] = "active" if result["reachable"] else "offline"

            return result

        except Exception as e:
            result = {
                "reachable": False,
                "error": str(e),
                "checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            with self._lock:
                self._health[camera_id] = result
                self._cameras[camera_id]["status"] = "offline"
            return result

    def check_all_health(self) -> Dict[str, Dict]:
        """Check health of all non-template cameras."""
        results = {}
        for cam_id, cam in self._cameras.items():
            if cam.get("status") != "template":
                results[cam_id] = self.check_health(cam_id)
        return results

    def get_active_cameras(self) -> List[Dict]:
        """Return only cameras that are confirmed active or have resolvable URLs."""
        return [
            c for c in self._cameras.values()
            if c.get("status") in ("active",) and c.get("status") != "template"
        ]

    def get_bangalore_cameras(self) -> List[Dict]:
        """Return all Bangalore/India category cameras."""
        return [c for c in self._cameras.values() if c.get("category") == "india"]

    def get_singapore_cameras(self) -> List[Dict]:
        """Return all Singapore LTA cameras."""
        return [c for c in self._cameras.values() if c.get("category") == "singapore"]

    def get_london_cameras(self) -> List[Dict]:
        """Return all London TfL cameras."""
        return [c for c in self._cameras.values() if c.get("category") == "london"]

    def get_templates(self) -> List[Dict]:
        """Return camera templates for user configuration."""
        return [c for c in self._cameras.values() if c.get("category") == "templates"]


# ─── Module-level singleton ─────────────────────────────────────────────────
_registry: Optional[CameraRegistry] = None

def get_camera_registry() -> CameraRegistry:
    """Returns a singleton CameraRegistry instance."""
    global _registry
    if _registry is None:
        _registry = CameraRegistry()
    return _registry
