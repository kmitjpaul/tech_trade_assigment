from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

from src.constants import INFLUX_MEASUREMENT
from src.settings import INFLUX_BUCKET, INFLUX_ORG, INFLUX_PASSWORD, INFLUX_USERNAME, INFLUX_URL

_params = {
    'url': INFLUX_URL,
    'username': INFLUX_USERNAME,
    'password': INFLUX_PASSWORD,
    'org': INFLUX_ORG,
}


class Data:
    def __init__(self):
        self.prices = []
        self.times = []
        self.types = []


class Repository:

    def __init__(self):
        self._influx_client = InfluxDBClient(**_params)

    def get_prices_and_times_by_time_range_start(self, range_start: str, symbol: str):
        query_api = self._influx_client.query_api()
        query = f"""from(bucket: "{INFLUX_BUCKET}")
                          |> range(start: {range_start}, stop: now())
                          |> filter(fn: (r) => r["_measurement"] == "{INFLUX_MEASUREMENT}")
                          |> filter(fn: (r) => r["symbol"] == "{symbol}")
                          |> aggregateWindow(every: 1m, fn: last, createEmpty: false)
                          |> yield(name: "last")"""

        tables = query_api.query(query)

        data = Data()
        for table in tables:
            for record in table.records:
                vals = record.values
                if vals['_field'] == 'price':
                    data.prices.append(float(vals['_value']))
                    data.times.append(vals['_time'])
                    data.types.append(vals['type'])

        return data

    def __del__(self):
        self._influx_client.close()


class AsyncRepository:
    def __init__(self):
        self._influx_client = None
        self._write_api = None

    async def insert_data(self, price_per_unit: str, type_tag: str, symbol: str):
        if not self._influx_client:
            raise AsyncRepositoryException('Should be used withing async context')

        point = Point(INFLUX_MEASUREMENT).tag('type', type_tag) \
            .tag('symbol', symbol) \
            .field("price", price_per_unit)

        await self._write_api.write(bucket=INFLUX_BUCKET, record=point)

    async def __aenter__(self):
        self._influx_client = InfluxDBClientAsync(**_params)
        self._write_api = self._influx_client.write_api()

        return self

    async def __aexit__(self, *_excinfo):
        await self._influx_client.close()


class AsyncRepositoryException(Exception):
    pass
