import json
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from Process import procesar_calendario_canvas


PROJECT_DIR = Path(__file__).resolve().parent
FILES_DIR = PROJECT_DIR / "files"
CONFIG_PATH = FILES_DIR / "config.json"
ICS_PATH = FILES_DIR / "calendar.ics"
EVENTS_PATH = FILES_DIR / "events.json"


def download_calendar(url):
    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError("The saved calendar URL must be a valid HTTP or HTTPS URL.")

    request = Request(url, headers={"User-Agent": "SchoolPlanner/1.0"})
    with urlopen(request, timeout=30) as response:
        calendar_data = response.read()

    if not calendar_data.strip():
        raise ValueError("The calendar feed returned an empty response.")

    ICS_PATH.write_bytes(calendar_data)


def main():
    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(
            "Calendar URL is not configured. Choose 'Setup .ics URL' first."
        )

    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        config = json.load(config_file)

    if not isinstance(config, dict) or not isinstance(config.get("urlFeed"), str):
        raise ValueError("config.json must contain a string value named 'urlFeed'.")

    calendar_url = config["urlFeed"].strip()
    if not calendar_url:
        raise ValueError("The calendar URL in config.json is empty.")

    print("Downloading calendar feed...")
    FILES_DIR.mkdir(parents=True, exist_ok=True)
    download_calendar(calendar_url)

    print("Processing calendar events...")
    procesar_calendario_canvas(ICS_PATH, EVENTS_PATH)
    print(f"Calendar events are saved to: {EVENTS_PATH}")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, json.JSONDecodeError, OSError, URLError, ValueError) as error:
        raise SystemExit(f"Could not fetch or process the calendar: {error}") from error
