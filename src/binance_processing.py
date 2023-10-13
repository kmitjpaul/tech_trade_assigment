import asyncio
import logging

from binance import BinanceSocketManager, AsyncClient

from src.constants import BINANCE_SYMBOLS_LIST
from src.influx import AsyncRepository
from src.settings import LOG_LEVEL

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


class BinanceDataProcessor:
    def __init__(self):
        self._binance_client = None
        self._repo = None

    def process(self):
        asyncio.run(self._process())

    async def _process(self):
        self._binance_client = await AsyncClient.create()
        bm = BinanceSocketManager(self._binance_client)

        streams = [f"{symbol.lower()}@depth" for symbol in BINANCE_SYMBOLS_LIST]

        async with bm.multiplex_socket(streams) as dscm, AsyncRepository() as repo:
            self._repo = repo
            logger.info(f"Started asynchronous processing")

            while True:
                msg = await dscm.recv()

                if 'e' in msg:
                    logger.warning(f"Received error {msg}")
                    raise BinanceDataProcessorException(f"Error in received binance message: {msg}")

                data = msg.get('data', None)

                if data is None:
                    raise BinanceDataProcessorException(f"Error in received binance message: {msg}")

                await asyncio.gather(
                    self._insert_data(data['a'], 'ask', data['s']),
                    self._insert_data(data['b'], 'bid', data['s']),
                )

    async def _insert_data(self, data: list, type_tag: str, symbol: str):
        coroutines = []
        for item in data:
            price = float(item[0])
            quantity = float(item[1])

            if quantity == 0:
                logger.debug(f"Quantity is 0.0")
                continue

            price_per_unit = price / quantity

            coroutines.append(self._repo.insert_data(price_per_unit, type_tag, symbol))

        await asyncio.gather(*coroutines)

    def __del__(self):
        if self._binance_client:
            asyncio.run(self._binance_client.close_connection())


class BinanceDataProcessorException(Exception):
    pass
