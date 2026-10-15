import json
from pathlib import Path
import urllib.request
from urllib.parse import urlparse


def validate_ics_existence(url):  # Take .ics url and test if it's available
    parsed_url = urlparse(url)
    if not all([parsed_url.scheme, parsed_url.netloc]):
        return False

    # Create a request object forced to use the HEAD method
    req = urllib.request.Request(url, method='HEAD')
    
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                return True
    except Exception:
        return False
    return False


ics_url = str(input("\nVisit your Canvas calendar page and look for 'Calendar Feed'.\nEnter your iCalendar (.ics) feed URL: "))
print(validate_ics_existence(ics_url))

config = {"urlFeed": ics_url}
files_dir = Path(__file__).resolve().parent / "files"
files_dir.mkdir(parents=True, exist_ok=True)
config_path = files_dir / "config.json"

with config_path.open("w", encoding="utf-8") as file:
    json.dump(config, file, indent=4)
