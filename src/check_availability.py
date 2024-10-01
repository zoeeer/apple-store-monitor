import argparse
import requests
import json
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs

from models import AvailabilityHistory

models = {
    "desert-256g": "MYLV3ZA/A",
    # "desert-512g": "MYM23ZA/A",
    # "white-256g": "MYLU3ZA/A",
    # "black-128g": "MYLN3ZA/A"
}

apple_store_urls = {
    "pickup-message-recommendations": {
        "decoded": "https://www.apple.com/hk-zh/shop/pickup-message-recommendations?mts.0=regular&mts.1=compact&cppart=UNLOCKED/WW&location=香港&product=MYM23ZA/A",
        "base_url": "https://www.apple.com/hk-zh/shop/",
        "endpoint": "pickup-message-recommendations",
        "query": {},
        "format": "https://www.apple.com/hk-zh/shop/pickup-message-recommendations?mts.0=regular&mts.1=compact&cppart=UNLOCKED/WW&location=香港&product={product}",
    },
    "fulfillment-messages": {
        "encoded": "https://www.apple.com/hk-zh/shop/fulfillment-messages?pl=true&mts.0=regular&mts.1=compact&cppart=UNLOCKED/WW&parts.0=MYLU3ZA/A&location=%E9%A6%99%E6%B8%AF",
        "base_url": "https://www.apple.com/hk-zh/shop/",
        "endpoint": "fulfillment-messages",
        "query": {},
        "format": "https://www.apple.com/hk-zh/shop/fulfillment-messages?pl=true&mts.0=regular&mts.1=compact&cppart=UNLOCKED/WW&parts.0={part_number}&location=%E9%A6%99%E6%B8%AF",
    }
}


recommendations_url = apple_store_urls["pickup-message-recommendations"]["decoded"]
fulfillment_url = apple_store_urls["fulfillment-messages"]["encoded"]


def check_fulfillment_availability(data) -> int:
    data = json.loads(data)
    available_stores = []

    # Iterate through the stores
    for store in data['body']['content']['pickupMessage']['stores']:
        parts_availability = store['partsAvailability']

        for part_number, details in parts_availability.items():
            is_available = details["pickupDisplay"] == "available"
            if is_available:
                available_stores.append(store['storeName'])  # Save the store's name

            AvailabilityHistory.store_availability(
                store["storeNumber"],
                part_number,
                is_available,
                product_details=details
            )

    # Check if more than one store is available
    if available_stores:
        print("Your iPhone is available at:", available_stores)
    else:
        print("Your iPhone is not available")

    return len(available_stores)


def check_recommendations_availability(data):
    data = json.loads(data)
    available_stores = []

    for store in data['body']['PickupMessage']['stores']:
        # Check if partsAvailability is not empty
        parts_availability = store['partsAvailability']

        if parts_availability:
            available_stores.append(store['storeName'])  # Save the store's name

        for part_number, details in parts_availability.items():
            AvailabilityHistory.store_availability(
                store["storeNumber"],
                part_number,
                True,
                product_details=details
            )

    # Check if more than one store is available
    if available_stores:
        print("Similar iPhone is available at:", available_stores)
    else:
        print("No similar iPhone available")
        AvailabilityHistory.nothing_available()


def request_fulfillment(product=None, cookie_jar=None, update_cookie_jar=False, har_save_path=None) -> int:
    if product is None:
        for part_number in models.values():
            request_fulfillment(product=part_number)
        return

    url_template = apple_store_urls["fulfillment-messages"]["format"]
    url = url_template.format(part_number=product)

    print(url)

    # Step 1: Create a session and load cookies if provided
    session = requests.Session()
    if cookie_jar:
        with open(cookie_jar, 'r') as f:
            cookies = json.load(f)
            session.cookies.update(cookies)

    # Step 2: Send HTTP request
    response = session.get(url)

    # Step 3: Parse response
    if response.status_code != 200:
        print("failed")
        return

    return check_fulfillment_availability(response.content.decode())


def request_recommendations(product=None, cookie_jar=None, update_cookie_jar=False, har_save_path=None):
    url_template = apple_store_urls["pickup-message-recommendations"]["format"]

    if product is None:
        for part_number in models.values():
            request_recommendations(product=part_number)
        return

    url = url_template.format(product=product)

    print(url)

    # Step 1: Create a session and load cookies if provided
    session = requests.Session()
    if cookie_jar:
        with open(cookie_jar, 'r') as f:
            cookies = json.load(f)
            session.cookies.update(cookies)

    # Step 2: Send HTTP request
    response = session.get(url)

    # Step 3: Parse response
    if response.status_code != 200:
        print("failed")
        return

    check_recommendations_availability(response.content.decode())


def request_check_availability(url, cookie_jar=None, update_cookie_jar=False, har_save_path=None):
    # Step 1: Create a session and load cookies if provided
    session = requests.Session()
    if cookie_jar:
        with open(cookie_jar, 'r') as f:
            cookies = json.load(f)
            session.cookies.update(cookies)

    # Step 2: Send HTTP request
    response = session.get(url)

    # Step 3: Parse response
    if response.status_code != 200:
        print("failed")
        return

    check_recommendations_availability(response.content.decode())


    # Update cookie jar if requested
    if update_cookie_jar and cookie_jar:
        with open(cookie_jar, 'w') as f:
            json.dump(session.cookies.get_dict(), f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Save HTTP request and response in HAR format.")
    parser.add_argument("--url", help="URL to send the request to.", default=recommendations_url)
    parser.add_argument("--har-save-path", type=str, help="File path to save HAR to.")
    parser.add_argument("--cookie-jar", type=str, help="Input cookie jar file path.")
    parser.add_argument("--update-cookies", action="store_true", help="Update input cookie jar file with cookies from response.")

    args = parser.parse_args()

    request_fulfillment()
    request_recommendations()
    # request_check_availability(args.url, args.cookie_jar, args.update_cookies, args.har_save_path)
