import requests
import os

from common import logger

push_url = os.environ.get("PUSHDEER_URL")
push_key = os.environ.get("PUSHDEER_KEY")


if not push_url or not push_key:
    logger.error("PushDeer URL or key not set in environment variables")


def send_text(text):
    if not push_url or not push_key:
        logger.error("PushDeer URL or key not set in environment variables")

    params = {
        "pushkey": push_key,
        "text": text
    }
    try:
        response = requests.get(push_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error sending notification: {e}")


if __name__ == "__main__":
    send_text("hello, test")
