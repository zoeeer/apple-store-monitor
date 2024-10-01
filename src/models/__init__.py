from .base import db, Model, MyJsonEncoder
from .models import Product, Store, AvailabilityHistory

all_models = (
    Store,
    Product,
    AvailabilityHistory,
)

db.create_tables(all_models)
