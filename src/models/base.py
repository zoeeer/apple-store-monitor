from datetime import datetime, date
from json import JSONEncoder
import os
import uuid
from pathlib import Path, PurePath

from peewee import (
    SqliteDatabase, PostgresqlDatabase,
    Model as _Model,
    chunked,
)
from playhouse.shortcuts import model_to_dict, dict_to_model, update_model_from_dict

import logging
from common import config_logger

if os.environ.get('APP_DEBUG_ECHO_SQL'):
    logger = logging.getLogger('peewee')
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)

DB_Path = os.environ.get('APP_DB_PATH', ':memory:')
DB_HOST = os.environ.get('APP_DB_HOST')

logger = logging.getLogger(__name__)
config_logger(logger)

if DB_HOST:
    # Database: PostgreSQL
    db = PostgresqlDatabase(
        os.environ['APP_DB_NAME'],  # Required by Peewee.
        host=os.environ['APP_DB_HOST'],  # Will be passed directly to psycopg2.
        port=int(os.environ.get('APP_DB_PORT', 5432)),  # Ditto.
        user=os.environ['APP_DB_USER'],  # Ditto.
        password=os.environ['APP_DB_PASSWD'],  # Ditto.
        autorollback=True,
    )
    logger.info(f"Connected to Postgres at {db.connect_params["host"]}:{db.connect_params["port"]}")

# fall back to SQLite
else:
    # Database: SQLite
    db = SqliteDatabase(DB_Path)
    logger.info(f"Connected to SQLite at {DB_Path}")


class Model(_Model):
    """ Our Base Model """
    class Meta:
        database = db

    def model_to_dict(self, *args, extra_data=None, **kwargs):
        # from .user import User
        # # kwargs.setdefault('max_depth', 1)

        # # NOTE: 不要返回用户密码等私密信息
        # # 因为 peeewee 没有提供针对每个Model设置默认可序列化字段的方法，暂时在这里“全局”设置
        # kwargs.setdefault('exclude', set())
        # kwargs['exclude'].add(User.hashed_password)
        d = model_to_dict(self, *args, **kwargs)
        if isinstance(extra_data, dict):
            d.update(**extra_data)
        return d

    @classmethod
    def dict_to_model(cls, data, ignore_unknown=False):
        return dict_to_model(cls, data, ignore_unknown)

    def update_from_dict(self, data, ignore_unknown=False):
        return update_model_from_dict(self, data, ignore_unknown)

    @classmethod
    def chunked_insert_many(cls, rows, fields=(), *args, chunk_size=100, **kwargs):
        """
        Insert multiple rows in transaction, and divide data to batches.
        This allows huge number of rows to be inserted.
        """
        cnt = 0
        with cls._meta.database.atomic():
            for batch in chunked(rows, chunk_size):
                # NOTE: use returning() to disable returned data of PostgreSQL.
                #       see http://docs.peewee-orm.com/en/latest/peewee/api.html#Model.insert_many
                cnt += cls.insert_many(batch, fields) \
                          .returning() \
                          .execute()
        return cnt


class MyJsonEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return str(obj.strftime("%Y-%m-%d %H:%M:%S"))
        if isinstance(obj, date):
            return str(obj.strftime("%Y-%m-%d"))
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, PurePath):
            return str(obj)
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, Model):
            d = obj.model_to_dict()
            return d
        return JSONEncoder.default(self, obj)
