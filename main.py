import json, requests, time, os
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
import pytz

LLM_API_KEY = os.getenv("AIzaSyDeVanapA5o28_mvG5fCW5ueQ74RPztYnA")
LLM_MODEL = "gemini-2.5-flash"

TELEGRAM_BOT_TOKEN = os.getenv("8078022746:AAG4A6d32u9sE13fhq_OAFYaqkncF_iRJ_A")
TELEGRAM_CHAT_ID = os.getenv("2009864654")

# Load JSON into memory
with open("gk_rag_final.json") as f:
    data = json.load(f)

# Build topic map
topics = {}
for item in data:
    topics.setdefault(item["topic"], []).append(item["text"])

TOPIC_ROTATION = [
    "superlatives_india", "superlatives_world", "first_in_world",
    "national_parks", "sports_terminology", "dances_india", "rivers_india",
    "dams_india", "stadiums_india", "mountain_peaks", "thermal_power_plants",
    "museums_india", "sea_ports", "waterfalls_india", "airports_india",
    "biosphere_reserves", "temples_india", "major_crops",
    "famous_personalities_nicknames", "sports_personalities_nicknames",
    "space_centres", "full_forms", "international_boundary_lines",
    "institutions_india", "countries_parliament", "important_awards",
    "inventions_inventors", "books_authors", "famous_gardens", "famous_forts",
    "military_exercises", "nobel_prize_2024"
]

INDEX_FILE = "topic_index.txt"

def get_topic_index():
    if not os.path.exists(INDEX_FILE):
        return 0
    return int(open(INDEX_FILE).read().strip())

def save_topic_index(i):
    with open(INDEX_FILE, "w") as f:
        f.write(str(i))

def llm(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{LLM_MODEL}:generateContent?key={LLM_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    for attempt in range(5):
        r = requests.post(url, json=payload).json()
        if "candidates" in r:
            return r["candidates"][0]["content"]["parts"][0]["text"]
        time.sleep(2)
    return "Gemini unavailable right now."

def generate_story(topic):
    text_block = "\n".join(topics[topic])
    prompt = f"""
You are an SSC CGL memory coach. Create a highly visual mnemonic story 
(8–12 lines) for the following facts:

{text_block}

Output ONLY the story.
"""
    return llm(prompt)

def send_to_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})

def daily_job():
    idx = get_topic_index()
    topic = TOPIC_ROTATION[idx % len(TOPIC_ROTATION)]
    story = generate_story(topic)
    send_to_telegram(f"📘 Daily SSC Memory Story: {topic}\n\n{story}")
    save_topic_index(idx + 1)

def weekly_revision():
    prompt = """
Summarize ALL major SSC GK topics into a single crisp revision mnemonic 
(15–20 lines). Highly visual, memory palace style. 
Do NOT include any jokes.
"""
    story = llm(prompt)
    send_to_telegram("📚 WEEKLY REVISION STORY:\n\n" + story)

IST = pytz.timezone("Asia/Kolkata")
scheduler = BlockingScheduler(timezone=IST)

scheduler.add_job(daily_job, "cron", hour=8, minute=0)  # Daily 8 AM
scheduler.add_job(weekly_revision, "cron", day_of_week="sun", hour=9, minute=0)

print("🚀 SSC GK Memory Server Started!")
scheduler.start()
