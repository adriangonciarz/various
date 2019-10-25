import asyncio
import json
import logging
import sys
import time

import aiohttp
from faker import Faker

"""
An idea of how to benchmark API processing ability using asynchronous HTTP client. 
The idea is to measure how much data (in kilobytes) can API process within a given period of time.  
Example generated output:

INFO:root:total size sent: 22.01 kilobytes
INFO:root:Batch size: 20
Total batches: 10
Total items: 200
Executed in 0.35 seconds
"""


fake = Faker()

# Configuration
URI = 'http://myapi.example.com/api'
PARALLEL_NUM = 20
TOTAL_BATCHES = 10
BATCH_SIZE = 20

logging.basicConfig(filename='example.log', level=logging.INFO)


def _payload():
    """Just and example generated JSON payload"""
    return {
        "email": fake.email(),
        "name": fake.name(),
        "uuid": fake.uuid4()
    }


def _batch(size):
    """Create batch of payload entities"""
    return [_payload() for _ in range(size)]


async def send_request(session):
    """Asynchronous request send"""
    b = _batch(BATCH_SIZE)
    async with session.post(URI, json=b) as response:
        await response.text()
        logging.debug(f'Status Code: {response.status}')
        return sys.getsizeof(json.dumps(b)) / 1024


async def bound_fetch(sem, session):
    """Limits maximum concurrent requests"""
    async with sem:
        return await send_request(session)


async def main():
    """Main method sending requests using AIOHttp client session"""
    tasks = []
    sem = asyncio.Semaphore(PARALLEL_NUM)
    async with aiohttp.ClientSession() as session:
        for i in range(TOTAL_BATCHES):
            task = asyncio.create_task(bound_fetch(sem, session))
            tasks.append(task)
        sizes = await asyncio.gather(*tasks)
        logging.info(f'total size sent: {sum(sizes):0.2f} kilobytes')


if __name__ == "__main__":
    s = time.perf_counter()
    asyncio.run(main())
    elapsed = time.perf_counter() - s
    logging.info(
        f"Batch size: {BATCH_SIZE}\nTotal batches: {TOTAL_BATCHES}\nTotal items: {TOTAL_BATCHES * BATCH_SIZE}\nExecuted in {elapsed:0.2f} seconds")
