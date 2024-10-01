from .base import db, Model, MyJsonEncoder
from .models import (
    Product, Store, AvailabilityHistory,
    LatestAvailability,  # view
)

all_models = (
    Store,
    Product,
    AvailabilityHistory,
)

db.create_tables(all_models)
