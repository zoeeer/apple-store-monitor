from datetime import datetime
import re

from peewee import (
    AutoField, IntegerField, CharField, DateTimeField, BooleanField
)

from .base import db, Model

class Store(Model):
    store_number = CharField(primary_key=True, max_length=10)
    name = CharField(max_length=100)
    country = CharField(max_length=2)
    city = CharField(max_length=50)
    address = CharField(max_length=255)
    address2 = CharField(max_length=255, null=True)
    address3 = CharField(max_length=255, null=True)

    class Meta:
        database = db
        db_table = 'stores'


class Product(Model):
    id = IntegerField(primary_key=True)  # Auto-incrementing ID
    part_number = CharField(max_length=10, unique=True)
    product_title = CharField(max_length=255, null=True)
    model = CharField(max_length=50, null=True)
    finish = CharField(max_length=50, null=True)
    capacity = CharField(max_length=10, null=True)

    class Meta:
        database = db
        db_table = 'products'
        indexes = (
            (('part_number',), True),  # Create an index on the part_number column
        )

    @classmethod
    def get_id_by_part_number(cls, part_number):
        try:
            product = cls.get(cls.part_number == part_number)
            return product.id
        except cls.DoesNotExist:
            return None

    @classmethod
    def parse_product_title(cls, product_title):
        # Regular expression to match the pattern
        match = re.search(r'^(.*?)\s+(\d+GB)\s+(.*)$', product_title)
        
        if match:
            model = match.group(1).strip()  # Text before capacity
            capacity = match.group(2).strip()  # Capacity itself
            finish = match.group(3).strip()  # Text after capacity
            return model, capacity, finish
        return None, None, None  # Return None if no match found

    @classmethod
    def try_parse_product_details(cls, details):
        try:
            message_types = details["messageTypes"]
            product_title = message_types["regular"]["storePickupProductTitle"]
            # messages = list(message_types.values())
            # product_title = messages[0]["storePickupProductTitle"]
        except:
            product_title = None

        if product_title:
            model, capacity, finish = cls.parse_product_title(product_title)
            return dict(
                product_title=product_title,
                model=model,
                capacity=capacity,
                finish=finish
            )
        else:
            return {}


class AvailabilityHistory(Model):
    """
    Rules for storing history:
    1. For each pair of store_number and product_id, the latest record represents the current availability state.
    2. We need to track the changing points (time) of availabilities, storing only the first and last occurrences for each state.
    3. When inserting a new record:
       - Retrieve the last 2 records of the product-store pair.
       - If the availability changes (is different from the current), insert it immediately.
       - If the availability is the same as the current state, check the second record:
         - If new_state == current_state == prev_state, update the "update_time" of the latest record to the current time.
         - If new_state == current_state and new_state != prev_state, insert the new state as another record.
    """
    id = AutoField(primary_key=True)  # Auto-increment is handled by Peewee
    store_number = CharField(max_length=10)
    part_number = CharField(max_length=10)
    product_id = IntegerField(null=True)
    is_available = BooleanField()
    inventory = IntegerField(null=True)
    update_time = DateTimeField()

    class Meta:
        database = db
        db_table = 'availability_history'
        indexes = (
            (('store_number', 'product_id'), False),
            (('store_number', 'part_number'), False),
        )

    @classmethod
    def nothing_available(cls):
        current_time = datetime.now()

        for product in Product.select():
            for store in Store.select():
                AvailabilityHistory.create(
                    store_number=store.store_number,
                    part_number=product.part_number,
                    product_id=product.product_id,
                    is_available=False,
                    update_time=datetime.now()
                )

    @classmethod
    def store_availability(cls, store_number, part_number, is_available, product_details=None):
        product_properties = Product.try_parse_product_details(product_details)
        print(f"Storing availability: store_number={store_number}, part_number={part_number}, is_available={is_available}")
        print(product_properties)
        product : Product
        product, _ = Product.get_or_create(
                        part_number=part_number,
                        defaults=product_properties
                    )
        if product.product_title is None:
            product.update_from_dict(product_properties)
            product.save()

        inventory = cls.parse_inventory_from_product_details(product_details)

        cls.update_availability(store_number, product, is_available, inventory)

        # AvailabilityHistory.create(
        #     store_number=store_number,
        #     part_number=part_number,
        #     product_id=product.id,
        #     is_available=is_available,
        #     inventory=inventory,
        #     update_time=datetime.now()
        # )

    @classmethod
    def update_availability(cls, store_number, product: Product, is_available: bool, inventory: int):
        # Retrieve the last two records for the given store and product
        select_latest_two_records = (
            AvailabilityHistory
            .select()
            .where((AvailabilityHistory.store_number == store_number) & 
                   (AvailabilityHistory.part_number == product.part_number))
            .order_by(AvailabilityHistory.update_time.desc())
            .limit(2)
        )

        last_records = list(select_latest_two_records)

        current_record: cls = last_records[0] if len(last_records) > 0 else None
        previous_record: cls = last_records[1] if len(last_records) > 1 else None

        should_insert = True
        if current_record and previous_record \
                and is_available == current_record.is_available \
                and is_available == previous_record.is_available \
                and inventory == current_record.inventory \
                and inventory == previous_record.inventory:
            should_insert = False

        if should_insert:
            AvailabilityHistory.create(
                store_number=store_number,
                part_number=product.part_number,
                product_id=product.id,
                is_available=is_available,
                inventory=inventory,
                update_time=datetime.now()
            )
        else:
            current_record.update_time = datetime.now()
            current_record.save()

    @classmethod
    def parse_inventory_from_product_details(cls, product_details):
        if not product_details:
            return None
        
        return product_details.get("buyability", {}).get("inventory", None)
