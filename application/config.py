import os
from flask import current_app as application

db_driver = 'postgresql+psycopg2'
db_host = 'ac-development.cimgucyve7tg.us-east-1.rds.amazonaws.com'
db_username = 'asylum_connect'
db_password = ''

dev_db_name = 'postgres'
development_conn_string = (
    f"{db_driver}://{db_username}:{db_password}"
    f"@{db_host}/{dev_db_name}?application_name=westpark_app"
)


class Config(object):
    SQLALCHEMY_DATABASE_URI = development_conn_string
