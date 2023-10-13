from os import environ

from dotenv import load_dotenv

load_dotenv()

INFLUX_URL = environ["INFLUX_URL"]
INFLUX_USERNAME = environ["INFLUX_USERNAME"]
INFLUX_PASSWORD = environ["INFLUX_PASSWORD"]
INFLUX_ORG = environ["INFLUX_ORG"]
INFLUX_BUCKET = environ["INFLUX_BUCKET"]

LOG_LEVEL = environ.get('LOG_LEVEL', 'INFO')
