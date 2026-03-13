import requests
from bs4 import BeautifulSoup
import time
import re
import csv
import math
from datetime import datetime

# =========================
# TELEGRAM
# =========================

TOKEN = "8705089258:AAHIeqsrgQhv1-rzHr9zamgvTYsSXW0BgoA"
CHAT_ID = "8554750866"

def send_telegram(msg):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": msg
    }

    requests.post(url, data=data)


# =========================
# NOAA METAR
# =========================

def get_metar():

    url = "https://tgftp.nws.noaa.gov/data/observations/metar/stations/VTUL.TXT"

    try:

        r = requests.get(url, timeout=60)

        metar = r.text.split("\n")[1]

        return metar

    except:

        return None


# =========================
# VISIBILITY
# =========================

def get_visibility(metar):

    vis = re.search(r" (\d{4}) ", metar)

    if vis:
        return int(vis.group(1))

    return None


# =========================
# WIND
# =========================

def get_wind(metar):

    wind = re.search(r"(\d{3})(\d{2})KT", metar)

    if wind:

        direction = int(wind.group(1))
        speed = int(wind.group(2))

        return direction, speed

    return None, None


# =========================
# CROSSWIND
# =========================

def crosswind(wind_dir, wind_speed):

    runway = 180

    angle = abs(runway - wind_dir)

    cross = wind_speed * math.sin(math.radians(angle))

    return round(cross,1)


# =========================
# RISK ANALYSIS
# =========================

def analyze_risk(metar):

    risk = "GREEN"

    visibility = get_visibility(metar)

    if visibility:

        if visibility < 5000:
            risk = "YELLOW"

        if visibility < 3000:
            risk = "RED"

    if "TS" in metar:
        risk = "RED"

    wind_dir, wind_speed = get_wind(metar)

    if wind_speed:

        if wind_speed > 20:
            risk = "YELLOW"

        if wind_speed > 30:
            risk = "RED"

    return risk


# =========================
# TMD SPECI
# =========================

def check_tmd_speci():

    url = "http://metcom.tmd.go.th"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:

        r = requests.get(url, headers=headers, timeout=60)

        soup = BeautifulSoup(r.text,"html.parser")

        text = soup.get_text()

        if "SPECI VTUL" in text:
            return True

    except:
        pass

    return False


# =========================
# SAVE CSV
# =========================

def save_csv(metar,risk):

    with open("metar_log.csv","a",newline="") as f:

        writer = csv.writer(f)

        writer.writerow([
            datetime.now(),
            metar,
            risk
        ])


# =========================
# MAIN
# =========================

last_metar = ""

def main():

    global last_metar

    send_telegram("✈️ VTUL Aviation Weather Monitor Started")

    while True:

        try:

            metar = get_metar()

            if metar and metar != last_metar:

                last_metar = metar

                risk = analyze_risk(metar)

                vis = get_visibility(metar)

                wind_dir, wind_speed = get_wind(metar)

                cw = None

                if wind_dir:
                    cw = crosswind(wind_dir, wind_speed)

                msg = f"""
VTUL METAR

{metar}

Visibility : {vis} m
Wind : {wind_dir}/{wind_speed} kt
Crosswind : {cw} kt

Risk Level : {risk}
"""

                send_telegram(msg)

                save_csv(metar,risk)

            if check_tmd_speci():

                send_telegram("🚨 SPECI VTUL DETECTED")

        except Exception as e:

            print(e)

        time.sleep(300)


if __name__ == "__main__":
    main()
