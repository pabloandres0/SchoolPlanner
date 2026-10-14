import json
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


ics_url = str(input("Visit your Canvas calendar page and look for 'Calendar Feed'.\nEnter your iCalendar (.ics) feed URL: "))
print(validate_ics_existence(ics_url))

ics_url = {
    "urlFeed": ics_url
}

with open("config.json", "w") as file:
    json.dump(ics_url, file, indent=4)