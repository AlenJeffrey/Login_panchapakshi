"""
Pancha-Pakshi app (MOON-nakshatra based)
All Pancha-Pakshi outputs are derived from MOON Nakshatra
"""

from flask import Flask, request, render_template_string, jsonify
from flask_cors import CORS

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
import swisseph as swe
import datetime

from astral import LocationInfo
from astral.sun import sun

# ---------------- APP INIT ----------------
app = Flask(__name__)
CORS(app)

# Swiss Ephemeris (Lahiri)
swe.set_sid_mode(swe.SIDM_LAHIRI)

# ---------------- CONSTANTS ----------------
RAASI_NAMES = [
    "Mesham","Rishabam","Mithunam","Kadagam","Simmam","Kanni",
    "Thulam","Viruchigam","Dhanusu","Magaram","Kumbam","Meenam"
]

NAKSHATRA_NAMES = [
 "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya","Ashlesha",
 "Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati","Vishakha","Anuradha",
 "Jyeshta","Moola","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishta","Shatabhisha",
 "Purva Bhadrapada","Uttara Bhadrapada","Revati"
]

PANCHA_PAKSHI_MAP = [
    ("Vulture","Peacock"),("Vulture","Peacock"),("Vulture","Peacock"),
    ("Vulture","Peacock"),("Vulture","Peacock"),
    ("Owl","Cock"),("Owl","Cock"),("Owl","Cock"),("Owl","Cock"),
    ("Owl","Cock"),("Owl","Cock"),
    ("Crow","Crow"),("Crow","Crow"),("Crow","Crow"),("Crow","Crow"),("Crow","Crow"),
    ("Cock","Owl"),("Cock","Owl"),("Cock","Owl"),("Cock","Owl"),("Cock","Owl"),("Cock","Owl"),
    ("Peacock","Vulture"),("Peacock","Vulture"),("Peacock","Vulture"),
    ("Peacock","Vulture"),("Peacock","Vulture")
]

BIRD_ORDER = ["Vulture","Owl","Crow","Cock","Peacock"]
ACTIVITIES = ["Ruling","Eating","Walking","Sleeping","Dying"]

FRIENDS_ENEMIES = {
    "Vulture": {"friends":["Peacock","Owl"], "enemies":["Crow","Cock"]},
    "Owl": {"friends":["Vulture","Crow"], "enemies":["Cock","Peacock"]},
    "Crow": {"friends":["Owl","Cock"], "enemies":["Vulture","Peacock"]},
    "Cock": {"friends":["Crow","Peacock"], "enemies":["Vulture","Owl"]},
    "Peacock": {"friends":["Vulture","Cock"], "enemies":["Owl","Crow"]}
}

# ---------------- UTILITIES ----------------
def geocode_place(place):
    geo = Nominatim(user_agent="pancha_app")
    loc = geo.geocode(place)
    if not loc:
        raise ValueError("Place not found")
    return loc.latitude, loc.longitude, loc.address

def get_timezone(lat, lon):
    tf = TimezoneFinder()
    tz = tf.timezone_at(lat=lat, lng=lon)
    if not tz:
        raise ValueError("Timezone not found")
    return tz

def to_utc(y,m,d,hh,mm,ss,tzname):
    tz = pytz.timezone(tzname)
    dt = tz.localize(datetime.datetime(y,m,d,hh,mm,ss))
    return dt.astimezone(pytz.utc)

def jd(dt):
    return swe.julday(dt.year,dt.month,dt.day,
        dt.hour + dt.minute/60 + dt.second/3600)

# ---------------- CORE LOGIC ----------------
def compute_chart(lat,lon,dt_utc):
    jd_ut = jd(dt_utc)
    ayan = swe.get_ayanamsa_ut(jd_ut)

    moon = swe.calc_ut(jd_ut,swe.MOON)[0][0]
    sun = swe.calc_ut(jd_ut,swe.SUN)[0][0]

    moon_sid = (moon - ayan) % 360
    sun_sid = (sun - ayan) % 360

    nak_index = int(moon_sid // (360/27))
    moon_nak = NAKSHATRA_NAMES[nak_index]
    moon_rasi = RAASI_NAMES[int(moon_sid//30)]

    tithi = ((moon_sid - sun_sid) % 360) / 12
    paksha = "Shukla" if tithi <= 15 else "Krishna"

    bird = PANCHA_PAKSHI_MAP[nak_index][0 if paksha=="Shukla" else 1]

    return moon_rasi, moon_nak, nak_index, bird, paksha, tithi

# ---------------- API ----------------
@app.route("/api/panchapakshi", methods=["POST"])
def panchapakshi_api():
    data = request.json

    y,m,d = map(int,data["dob"].split("-"))
    hh,mm,ss = map(int,data["tob"].split(":"))

    lat,lon,address = geocode_place(data["place"])
    tzname = get_timezone(lat,lon)
    dt_utc = to_utc(y,m,d,hh,mm,ss,tzname)

    moon_rasi, moon_nak, nak_i, bird, paksha, tithi = compute_chart(lat,lon,dt_utc)
    fe = FRIENDS_ENEMIES[bird]

    return jsonify({
        "name": data["name"],
        "address": address,
        "moon_rasi": moon_rasi,
        "moon_nakshatra": moon_nak,
        "pancha_bird": bird,
        "paksha": paksha,
        "tithi": round(tithi,2),
        "friends": fe["friends"],
        "enemies": fe["enemies"]
    })

# ---------------- HOME ----------------
@app.route("/")
def home():
    return "Pancha Pakshi API is running"
