import json
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from paths import CONFIG_PATH, FILES_DIR


def normalize_url(url):
    url = url.strip()
    if url.lower().startswith("webcal://"):
        url = "https://" + url[len("webcal://"):]
    return url


def validate_ics_url(url):
    parsed_url = urlparse(url)
    if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
        return False

    request = Request(url, headers={"User-Agent": "SchoolPlanner/1.0"})
    try:
        with urlopen(request, timeout=10) as response:
            first_bytes = response.read(512)   #
    except Exception:
        return False 
    return b"BEGIN:VCALENDAR" in first_bytes


def save_url(url):
    
    FILES_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w", encoding="utf-8") as config_file:
        json.dump({"urlFeed": url}, config_file, indent=4)


def setup_url():
    
    print("\nVisit your Canvas calendar page and look for 'Calendar Feed'.")
    url = normalize_url(input("Enter your iCalendar (.ics) feed URL: "))

    if not url:
        print("No URL entered. Nothing was saved.")
        return False

    print("Checking the link...")
    if validate_ics_url(url):
        print("The link works and looks like a calendar.")
    else:
        print("Warning: could not verify that link (typo, no internet, or not an .ics feed).")
        answer = input("Save it anyway? (y/n): ").strip().lower()
        if answer != "y":
            print("Nothing was saved.")
            return False

    save_url(url)
    print(f"URL saved to: {CONFIG_PATH}")
    return True


if __name__ == "__main__":
    setup_url()
