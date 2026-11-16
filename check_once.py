import os
import json
import requests

NTFY_TOPIC = os.environ["NTFY_TOPIC"]
SCRAPERAPI_KEY = os.environ["SCRAPERAPI_KEY"]

BMS_URL = "https://in.bookmyshow.com/cinemas/kolkata/pvr-mani-square-mall-kolkata/buytickets/MSMA/20261217"
TARGET_DATE = "20261217"

resp = requests.get(
    "https://api.scraperapi.com/",
    params={
        "api_key": SCRAPERAPI_KEY,
        "url": BMS_URL,
        "country_code": "in",
    },
    timeout=65,
)
print("HTTP status:", resp.status_code)
resp.raise_for_status()

marker = "window.__INITIAL_STATE__"
idx = resp.text.find(marker)
if idx == -1:
    raise RuntimeError("Missing __INITIAL_STATE__ (possible Cloudflare challenge)")

brace_idx = resp.text.find("{", idx)
state, _ = json.JSONDecoder().raw_decode(resp.text, brace_idx)

venue_api = state.get("venueShowtimesFunctionalApi")
if not venue_api:
    raise RuntimeError("venueShowtimesFunctionalApi not found")

compact = json.dumps(venue_api, separators=(",", ":")).lower()
has_date = (
    f'"showdatecode":"{TARGET_DATE}"' in compact
    or f'"showdatecode":{TARGET_DATE}' in compact
)
has_movie = "doomsday" in compact

if has_date and has_movie:
    print("MATCH FOUND! Sending ntfy alert...")
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data="Avengers: Doomsday tickets are open at PVR Mani Square (MSMA) for Dec 17!",
        headers={
            "Title": "DOOMSDAY TICKETS OPEN",
            "Priority": "urgent",
            "Tags": "ticket,rotating_light",
            "Click": BMS_URL,
        },
        timeout=15,
    ).raise_for_status()
else:
    print(f"Not open yet for {TARGET_DATE}.")
