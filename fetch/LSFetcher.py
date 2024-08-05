import asyncio
import json
import os

import httpx
import requests
from BaseFetcher import BaseFetcher
from decouple import config

assert os.path.isfile(".env"), ".env file not found!"

class LSFetcher(BaseFetcher):
    BASE_URL = "https://openapi.ls-sec.co.kr:8080"

    def __init__(self):
        self.headers = {"Content-Type": "application/x-www-form-urlencoded"}
        super().__init__(self.get_access_token())

    async def fetch_data(self, url, payload={}):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url=url, data=json.dumps(payload))
                response.raise_for_status()  # Raise an error for bad responses
                return response.json()  # Assuming API returns JSON data
            except httpx.HTTPStatusError as e:
                print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                print(f"An error occurred: {e}")

        return None  # Return None if there was an error
    
    def get_access_token(self):
        APP_KEY = config("LS_API_KEY")
        APP_SECRET = config("LS_API_SECRET_KEY")

        param = {
            "grant_type": "client_credentials",
            "appkey": APP_KEY,
            "appsecretkey": APP_SECRET,
            "scope": "oob",
        }

        request = requests.post(
            f"{self.BASE_URL}/oauth2/token",
            verify=False,
            headers=self.headers,
            params=param,
        )

        try:
            assert request.status_code == 200
            return request.json()["access_token"]
        except AssertionError:
            print(
                f"\tThe request failed with status code {request.status_code}.\n\tRespuest text: {request.text}"
            )
            return None
        
    async def get_stock_infos(self, shcode: str) -> dict:
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.api_key}",
            "tr_cd": "t1102",
            "tr_cont": "Y",
        }
        body = {"t1102InBlock": {"shcode": shcode}}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/stock/market-data", headers=headers, data=json.dumps(body)
            )

        stocks = response.json()["t1102OutBlock"]
        return stocks
    
    async def get_stock_hname(self, shcode:str) -> str:
        stock_infos = await self.get_stock_infos(shcode=shcode)

        return stock_infos["hname"]
    
    async def get_stock_price(self, shcode: str) -> int:
        stock_infos = await self.get_stock_infos(shcode=shcode)

        return stock_infos["price"]
    
    async def get_stock_change(self, shcode: str) -> str:
        stock_infos = await self.get_stock_infos(shcode=shcode)

        return stock_infos["change"]
    

if __name__ == "__main__":

    async def main():
        fetcher = LSFetcher()
        response = await fetcher.get_stock_change("078020")

        print(response)

    asyncio.run(main())