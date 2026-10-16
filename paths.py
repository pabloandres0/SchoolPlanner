from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
FILES_DIR = PROJECT_DIR / "files"
DATA_DIR = PROJECT_DIR / "data"

CONFIG_PATH = FILES_DIR / "config.json"         
ICS_PATH = FILES_DIR / "calendar.ics"           
EVENTS_PATH = FILES_DIR / "events.json"         
PRIORITIES_PATH = FILES_DIR / "priorities.json" 
BUSY_HOURS_PATH = FILES_DIR / "busy_hours.csv"  
SCHEDULE_PATH = FILES_DIR / "schedule.csv"      

KEYWORDS_PATH = DATA_DIR / "duration_keywords.csv"
