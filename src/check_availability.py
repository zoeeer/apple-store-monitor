import argparse
import json
import requests
import random
import time
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs

from models import AvailabilityHistory, Product, LatestAvailability
from common import logger
from notify import send_text


models = {
    "desert-256g": "MYLV3ZA/A",
    # "desert-512g": "MYM23ZA/A",
    "white-256g": "MYLU3ZA/A",
    "black-128g": "MYLN3ZA/A"
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


session = None


def check_fulfillment_availability(data) -> list[str]:
    data = json.loads(data)
    available_stores = []

    # Iterate through the stores
    for store in data['body']['content']['pickupMessage']['stores']:
        parts_availability = store['partsAvailability']

        for part_number, details in parts_availability.items():
            is_available = details["pickupDisplay"] == "available"
            if is_available:
                available_stores.append(store['storeName'])  # Save the store's name

            AvailabilityHistory.set_availability(
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

    return available_stores


def check_recommendations_availability(data) -> list[str]:
    data = json.loads(data)
    recommended_products = set()

    for store in data['body']['PickupMessage']['stores']:
        # Check if partsAvailability is not empty
        parts_availability = store['partsAvailability']

        for part_number, details in parts_availability.items():
            AvailabilityHistory.set_availability(
                store["storeNumber"],
                part_number,
                True,
                product_details=details
            )
            recommended_products.add(part_number)

    # Check if more than one store is available
    if recommended_products:
        print("Similar iPhone available:", recommended_products)
    else:
        print("No similar iPhone available")
        # AvailabilityHistory.nothing_available()
    return recommended_products


def request_fulfillment(product, cookie_jar=None, update_cookie_jar=False, har_save_path=None) -> list[str]:
    url_template = apple_store_urls["fulfillment-messages"]["format"]
    url = url_template.format(part_number=product)

    logger.info(f"Requesting fulfillment for {product}")
    logger.debug(url)

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

    # Update cookie jar if requested
    if update_cookie_jar and cookie_jar:
        with open(cookie_jar, 'w') as f:
            json.dump(session.cookies.get_dict(), f)

    return check_fulfillment_availability(response.content.decode())


def request_recommendations(product, cookie_jar=None, update_cookie_jar=False, har_save_path=None) -> list[str]:
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

    # Update cookie jar if requested
    if update_cookie_jar and cookie_jar:
        with open(cookie_jar, 'w') as f:
            json.dump(session.cookies.get_dict(), f)

    return check_recommendations_availability(response.content.decode())


def check_product_availability(product: Product | str, recursive=False) -> tuple[bool, bool]:
    if isinstance(product, str):
        product: Product = Product.get(Product.part_number == product)
    prev_availability = LatestAvailability.is_product_available(product)

    time.sleep(0.1)
    available_stores = bool(request_fulfillment(product.part_number))
    time.sleep(0.1)
    recommended_products = request_recommendations(product.part_number)

    if prev_availability != bool(available_stores):
        logger.info(f"Availability of {product.part_number} ({product.product_title}) changed!")
        # send notification
        if available_stores:
            send_text(f"Congratulations! {product.part_number} {product.capacity}-{product.finish} is available.")
        else:
            send_text(f"Sorry. {product.part_number} {product.capacity}-{product.finish} sold out.")

    if len(recommended_products) < 3:
        # update availability for recommended_products
        for p in recommended_products:
            time.sleep(0.1)
            request_fulfillment(p)

        # update all other products to not available
        all_available_products = recommended_products.copy()
        if available_stores:
            all_available_products.add(product.part_number)
        AvailabilityHistory.set_nearly_unavailable(all_available_products)

    if not recursive or len(recommended_products) < 3:
        return (available_stores, recommended_products)

    for p in recommended_products:
        check_product_availability(p)

    return None, None


def check_availability(product=None, pick_mode=None, recursive=False):

    if product:
        check_product_availability(product, recursive)
    elif pick_mode == "random":
        # Randomly select a known product
        product_count = Product.select().count()
        random_offset = random.randrange(product_count)
        logger.debug(f"random product offset {random_offset} from {product_count} products")
        product: Product = Product.select().offset(random_offset).first()
        logger.info(f"Checking availability for {product.part_number} ({product.product_title})")
        check_product_availability(product, recursive)
    elif pick_mode == "oldest":
        # Select the (roughly) least recently updated product
        # Note: here we simply select the oldest updated record, but this product at other store
        # could have been updated more recently
        oldest_updated = LatestAvailability.select().order_by(LatestAvailability.update_time).first()
        product: Product = Product.select().where(Product.part_number == oldest_updated.part_number).first()
        logger.info(f"Checking availability for {product.part_number} ({product.product_title})")
        check_product_availability(product, recursive)
    elif pick_mode == "all":
        for part_number in models.values():
            check_product_availability(part_number, recursive)
            time.sleep(3 + random.uniform(0.1, 2.5))
        return
    else:
        logger.warning("No product is checked.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Save HTTP request and response in HAR format.")
    parser.add_argument("--product", help="Product part number.")
    parser.add_argument("--random", action="store_true", help="Check availability for a random product.")
    parser.add_argument("--oldest", action="store_true", help="Check availability for the least recently updated product.")
    parser.add_argument("--check-all", action="store_true", help="Check availability for all products.")
    parser.add_argument("-r", "--recursive", action="store_true", help="Recursively check availability if recommendations are available.")
    parser.add_argument("--url", help="URL to send the request to.", default=recommendations_url)
    parser.add_argument("--har-save-path", type=str, help="File path to save HAR to.")
    parser.add_argument("--cookie-jar", type=str, help="Input cookie jar file path.")
    parser.add_argument("--update-cookies", action="store_true", help="Update input cookie jar file with cookies from response.")

    args = parser.parse_args()

    pick_mode = None

    if args.random:
        pick_mode = "random"
    elif args.oldest:
        pick_mode = "oldest"
    elif args.check_all:
        pick_mode = "all"

    check_availability(args.product, pick_mode, args.recursive)
