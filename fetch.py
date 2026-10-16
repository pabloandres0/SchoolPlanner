import json
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from paths import CONFIG_PATH, EVENTS_PATH, FILES_DIR, ICS_PATH
from Process import procesar_calendario_canvas
from sample_data import build_sample_calendar


def load_saved_url():
    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(
            "Calendar URL is not configured. Choose 'Set up Canvas calendar URL' first."
        )

    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        config = json.load(config_file)

    if not isinstance(config, dict) or not isinstance(config.get("urlFeed"), str):
        raise ValueError("config.json must contain a string value named 'urlFeed'.")

    url = config["urlFeed"].strip()
    if not url:
        raise ValueError("The calendar URL in config.json is empty.")
    return url


def download_calendar(url):
    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError("The saved calendar URL must be a valid HTTP or HTTPS URL.")

    request = Request(url, headers={"User-Agent": "SchoolPlanner/1.0"})
    with urlopen(request, timeout=30) as response:
        calendar_data = response.read()

    if not calendar_data.strip():
        raise ValueError("The calendar feed returned an empty response.")

    FILES_DIR.mkdir(parents=True, exist_ok=True)
    ICS_PATH.write_bytes(calendar_data)


def fetch_calendar():
    url = load_saved_url()

    print("Downloading calendar feed...")
    download_calendar(url)

    print("Processing calendar events...")
    count = procesar_calendario_canvas(ICS_PATH, EVENTS_PATH)
    print(f"{count} events saved to: {EVENTS_PATH}")
    return count


def use_sample_calendar():
    """Build a demo calendar (no Canvas account needed) and process it."""
    build_sample_calendar(ICS_PATH)
    count = procesar_calendario_canvas(ICS_PATH, EVENTS_PATH)
    print(f"Sample calendar loaded: {count} events saved to: {EVENTS_PATH}")
    return count


if __name__ == "__main__":
    try:
        fetch_calendar()
    except (FileNotFoundError, json.JSONDecodeError, OSError, URLError, ValueError) as error:
        raise SystemExit(f"Could not fetch or process the calendar: {error}") from error
