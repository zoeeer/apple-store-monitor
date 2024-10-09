import re


def parse_product_title(product_title):
    """
    Parse product_title string to (model, capacity, finish)

    Uses a regular expression to capture the `capacity` in the middle. Anything
    before it becomes `model`, and anything after it becomes `finish`.
    """
    # This regular expression means:
    # - (.*?): Any text before the capacity (non-greedy).
    # - (\d+(?:GB|TB)): The capacity, which comes in "GB" or "TB".
    # - (.*): Any text after the capacity.
    match = re.search(r'^(.*?)\s+(\d+(?:GB|TB))\s+(.*)$', product_title)

    if match:
        model = match.group(1).strip()
        capacity = match.group(2).strip()
        finish = match.group(3).strip()
        return model, capacity, finish
    return None, None, None  # Return None if no match found


def try_parse_product_details(details):
    try:
        message_types = details["messageTypes"]
        product_title = message_types["regular"]["storePickupProductTitle"]
        # messages = list(message_types.values())
        # product_title = messages[0]["storePickupProductTitle"]
    except:
        product_title = None

    if product_title:
        model, capacity, finish = parse_product_title(product_title)
        return dict(
            product_title=product_title,
            model=model,
            capacity=capacity,
            finish=finish
        )
    else:
        return {}


def parse_inventory_from_product_details(product_details):
    if not product_details:
        return None
    
    return product_details.get("buyability", {}).get("inventory", None)
