import requests
import os
import logging
import json
import pause
from datetime import datetime
import functions_framework

gym = os.getenv("GYM")
subscription_key = os.getenv("SUB_KEY")

default_headers = {
    'authority': f'api.{gym}fitness.com',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9',
    'Content-type': 'application/json',
    'ocp-apim-subscription-key': subscription_key,
    'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'cross-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'origin': f'https://my.{gym}.life',
    'referer': f'https://my.{gym}.life/'
}

def auth(username):
    password = os.getenv("PASSWORD")
    url = f"https://api.{gym}fitness.com/auth/v2/login"

    payload = json.dumps({"username": username, "password": password})

    response = requests.post(url, headers=default_headers, data=payload)

    if response.status_code == 200:
        return response.json()
    else:
        logging.exception(f"{response.status_code}, when accessing Auth")

def generate_reservation(token, sso, event_id, member_id):
    url = f'https://api.{gym}fitness.com/sys/registrations/V3/ux/event'
    headers = default_headers
    headers["x-ltf-profile"] = token
    headers['x-ltf-ssoid'] = sso

    payload= json.dumps({"eventId": event_id, "memberId": [member_id]})

    response = requests.post(url, headers=headers, data=payload)

    if response.status_code == 200:
        return response.json()["regId"]
    else:
        logging.exception(f"{response.status_code}, when creating reservation")

def complete_reservation(token, sso, regId, member_id):
    url = f"https://api.{gym}fitness.com/sys/registrations/V3/ux/event/{regId}/complete"
    headers = default_headers
    headers["x-ltf-profile"] = token
    headers['x-ltf-ssoid'] = sso

    payload = json.dumps({"memberId":[member_id],"acceptedDocuments":[60]})

    response = requests.put(url, headers=headers, data=payload)

    if response.status_code == 200:
        logging.info("Success Confirming Registration")
    else:
        logging.exception(f"{response.status_code}, when confirming Registration")

def create_reservation(event_id, trigger_time, member_id, username):
    logging.info(f"Beginning Reservation for {event_id}")

    r = auth(username)
    logging.info(r)
    token = r["token"]
    sso = r["ssoId"]
    logging.info(f"Successful Authentication")

    target = trigger_time.split(":")
    # handling Auth before reservation window opens up to minimize latency
    # using pause library rather than sleep because of more accurate clock time
    now = datetime.now()
    pause.until(datetime(now.year, now.month, now.day, int(target[0]), int(target[1])))

    logging.info(f"Generating Registration ID")
    regId = generate_reservation(token, sso, event_id, member_id)

    logging.info(f"Confirming Registration")
    complete_reservation(token, sso, regId, member_id)

    return "Success"

@functions_framework.http
def handler(request):
    request_json = request.get_json(silent=True)
    request_args = request.args

    required_headers = ['event_id', 'trigger_time', 'member_id', 'username']

    # currently accepting event_id and trigger_time
    # will add more args to support more users later on
    if request_json and set((required_headers)).issubset(set(request_json)):
        return create_reservation(request_json["event_id"], request_json["trigger_time"],request_json["member_id"], request_json["username"])
    elif request_args and required_headers.issubset(request_args):
        return create_reservation(request_args["event_id"], request_args["trigger_time"], request_args["member_id"], request_args["username"])
    else:
        return "Improper Arguments"
    
