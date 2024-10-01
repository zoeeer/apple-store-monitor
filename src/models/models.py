from datetime import datetime
import re

from peewee import (
    AutoField, IntegerField, CharField, DateTimeField, BooleanField
)

from .base import db, Model
from common import logger
from api_helpers import (
    parse_inventory_from_product_details,
    try_parse_product_details,
)

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
    create_time = DateTimeField()
    update_time = DateTimeField()

    class Meta:
        database = db
        db_table = 'availability_history'
        indexes = (
            (('store_number', 'product_id'), False),
            (('store_number', 'part_number'), False),
        )

    @classmethod
    def set_nearly_unavailable(cls, available_products):
        query_other_products = \
                Product.select() \
                .where(Product.part_number.not_in(available_products))

        logger.warning(f"Except {available_products}, update all others to unavailable")
        product: Product
        store: Store
        for product in query_other_products:
            for store in Store.select():
                cls.update_or_insert(
                    store.store_number,
                    product,
                    False,
                    inventory=None
                )

    @classmethod
    def set_availability(cls, store_number, part_number, is_available, product_details=None):
        product_properties = try_parse_product_details(product_details)
        logger.info(f"Storing availability: store_number={store_number}, part_number={part_number}, is_available={is_available}")
        logger.info(product_properties.get("product_title", "no product_title"))
        product : Product
        product, _ = Product.get_or_create(
                        part_number=part_number,
                        defaults=product_properties
                    )
        if product.product_title is None:
            product.update_from_dict(product_properties)
            product.save()

        inventory = parse_inventory_from_product_details(product_details)

        cls.update_or_insert(store_number, product, is_available, inventory)

    @classmethod
    def update_or_insert(cls, store_number, product: Product, is_available: bool, inventory: int = None):
        store: Store = Store.get_by_id(store_number)

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

        current_time = datetime.now()
        if should_insert:
            AvailabilityHistory.create(
                store_number=store_number,
                part_number=product.part_number,
                product_id=product.id,
                is_available=is_available,
                inventory=inventory,
                update_time=current_time,
                create_time=current_time,
            )
            logger.info(f"AvailabilityHistory: inserted availability for {product.part_number} ({product.product_title}) at store {store_number} ({store.name})")
        else:
            current_record.update_time = current_time
            current_record.save()
            logger.info(f"AvailabilityHistory: updated availability for {product.part_number} ({product.product_title}) at store {store_number} ({store.name})")

    @classmethod
    def parse_inventory_from_product_details(cls, product_details):
        if not product_details:
            return None
        
        return product_details.get("buyability", {}).get("inventory", None)
