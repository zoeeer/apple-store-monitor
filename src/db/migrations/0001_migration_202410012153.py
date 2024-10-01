# auto-generated snapshot
from peewee import *
import datetime
import peewee


snapshot = Snapshot()


@snapshot.append
class AvailabilityHistory(peewee.Model):
    store_number = CharField(max_length=10)
    part_number = CharField(max_length=10)
    product_id = IntegerField(null=True)
    is_available = BooleanField()
    inventory = IntegerField(null=True)
    create_time = DateTimeField()
    update_time = DateTimeField()
    class Meta:
        table_name = "availability_history"
        indexes = (
            (('store_number', 'product_id'), False),
            (('store_number', 'part_number'), False),
            )


@snapshot.append
class Product(peewee.Model):
    id = IntegerField(primary_key=True)
    part_number = CharField(max_length=10, unique=True)
    product_title = CharField(max_length=255, null=True)
    model = CharField(max_length=50, null=True)
    finish = CharField(max_length=50, null=True)
    capacity = CharField(max_length=10, null=True)
    class Meta:
        table_name = "products"
        indexes = (
            (('part_number',), True),
            )


@snapshot.append
class Store(peewee.Model):
    store_number = CharField(max_length=10, primary_key=True)
    name = CharField(max_length=100)
    country = CharField(max_length=2)
    city = CharField(max_length=50)
    address = CharField(max_length=255)
    address2 = CharField(max_length=255, null=True)
    address3 = CharField(max_length=255, null=True)
    class Meta:
        table_name = "stores"


def migrate_forward(op, old_orm, new_orm):
    op.create_table(new_orm.availabilityhistory)
    op.create_table(new_orm.product)
    op.create_table(new_orm.store)
    op.run_data_migration()


def migrate_backward(op, old_orm, new_orm):
    op.run_data_migration()
    op.drop_table(old_orm.store)
    op.drop_table(old_orm.product)
    op.drop_table(old_orm.availabilityhistory)
