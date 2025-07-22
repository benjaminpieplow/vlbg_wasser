# Test a function in the vowis_api
import aiohttp
import asyncio
from vowis_api import VowisApi

async def main():
    async with aiohttp.ClientSession() as session:
        api = VowisApi(session)
        response = await api.test_connection() # The function to test
        print(response)

asyncio.run(main())