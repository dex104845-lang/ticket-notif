import os
import json
import requests

NTFY_TOPIC = os.environ["NTFY_TOPIC"]
SCRAPERAPI_KEY = os.environ["SCRAPERAPI_KEY"]

DEFAULT_URL = "https://in.bookmyshow.com/cinemas/kolkata/pvr-mani-square-mall-kolkata/buytickets/MSMA/20261217"
BMS_URL = (os.environ.get("TEST_URL") or "").strip() or DEFAULT_URL
TARGET_DATE = (os.environ.get("TEST_DATE") or "").strip() or "20261217"

print("Checking URL:", BMS_URL)
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

# Theatre pages use venueShowtimesFunctionalApi; city movie pages use the main state
data_to_check = state.get("venueShowtimesFunctionalApi") or state
compact = json.dumps(data_to_check, separators=(",", ":")).lower()

has_date = (
    f'"showdatecode":"{TARGET_DATE}"' in compact
    or f'"showdatecode":{TARGET_DATE}' in compact
)
has_movie = "doomsday" in compact

if has_date and has_movie:
    print("MATCH FOUND! Sending ntfy alert...")
    is_test = BMS_URL != DEFAULT_URL
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=(
            f"[TEST] Doomsday is live for {TARGET_DATE}!"
            if is_test
            else f"Avengers: Doomsday tickets are open at PVR Mani Square (MSMA) for {TARGET_DATE}!"
        ),
        headers={
            "Title": "TEST: DOOMSDAY ALERT" if is_test else "DOOMSDAY TICKETS OPEN",
            "Priority": "urgent",
            "Tags": "ticket,rotating_light",
            "Click": BMS_URL,
        },
        timeout=15,
    ).raise_for_status()
    print("ntfy notification sent!")
else:
    print(f"Not open yet for {TARGET_DATE}.")
