import asyncio
import json
import os
from typing import Dict, List

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
        
    async def get_today_stock_infos(self, shcode: str) -> dict:
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.api_key}",
            "tr_cd": "t1102",
            "tr_cont": "N",
        }
        body = {"t1102InBlock": {"shcode": shcode}}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/stock/market-data", headers=headers, data=json.dumps(body)
            )

        stocks = response.json()["t1102OutBlock"]
        return stocks
    
    async def get_today_stock_hname(self, shcode:str) -> str: # 한글명
        stock_infos = await self.get_stock_infos(shcode=shcode)

        return stock_infos["hname"]
    
    async def get_today_stock_price(self, shcode: str) -> int: # 현재가
        stock_infos = await self.get_stock_infos(shcode=shcode)

        return stock_infos["price"]
    
    async def get_today_tock_diff(self, shcode: str) -> int: # 등락율
        stock_infos = await self.get_stock_infos(shcode=shcode)

        return stock_infos["diff"]
    
    async def get_today_stock_volume(self, shcode: str) -> int: # 누적거래량
        stock_infos = await self.get_stock_infos(shcode=shcode)

        return stock_infos["volume"]
    
    async def get_stock_chart_info(self, shcode: str, ncnt: int, sdate: str = "", edate: str = ""): # 주식 차트
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.api_key}",
            "tr_cd": "t8412",
            "tr_cont": "N",
        }
        body = {"t8412InBlock": {
            "shcode": shcode, # shortcut code
            "ncnt": ncnt, # time unit
            "qrycnt": 0,
            "nday": "0",
            "sdate": sdate, # example: "20240101"
            "edate": edate, # example: "20241231"
            "cts_date": "",
            "cts_time": "",
            "comp_yn": "N",
        }}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/stock/chart", headers=headers, data=json.dumps(body)
            )

        stocks = response.json()["t8412OutBlock1"]
        return stocks
    
    async def get_investor_sale_trend(self, market: str, upcode: str, gubun2: str, gubun3: str, from_date: str, to_date: str) -> List[Dict]:
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.api_key}",
            "tr_cd": "t1665",
            "tr_cont": "N",
        }
        body = {"t1665InBlock": {
            "market": market, 
            "upcode": upcode,
            "gubun2": gubun2,
            "gubun3": gubun3,
            "from_date": from_date, # example: "20240101"
            "to_date": to_date, # example: "20241231"
        }}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/stock/chart", headers=headers, data=json.dumps(body)
            )

        stocks = response.json()["t1665OutBlock1"]
        return stocks
    
    async def get_specific_investor_sale_trend(self, market: str, upcode: str, gubun2: str, gubun3: str, from_date: str, to_date: str, sv_code: str, sa_code: str) -> List[Dict]:
        total_investor_sale_trends = await self.get_investor_sale_trend(market, upcode, gubun2, gubun3, from_date, to_date)

        specific_investor_sale_trend = []

        for temp_trend in total_investor_sale_trends:
            temp_date = temp_trend["date"] # 일자
            temp_sale_volume = temp_trend[sv_code] # 개인 매매 수량
            temp_sale_amount = temp_trend[sa_code] # 개인 매매 금액

            specific_investor_sale_trend.append({
                "date": temp_date,
                "sale_volume" : temp_sale_volume,
                "sale_amount" : temp_sale_amount,
            })

        return specific_investor_sale_trend
    
    async def get_individual_investor_sale_trend(self, market: str, upcode: str, gubun2: str, gubun3: str, from_date: str, to_date: str) -> List[Dict]:
        return await self.get_specific_investor_sale_trend(market, upcode, gubun2, gubun3, from_date, to_date, sv_code="sv_08", sa_code="sa_08")
    
    async def get_foreign_investor_sale_trend(self, market: str, upcode: str, gubun2: str, gubun3: str, from_date: str, to_date: str) -> List[Dict]:
        return await self.get_specific_investor_sale_trend(market, upcode, gubun2, gubun3, from_date, to_date, sv_code="sv_17", sa_code="sa_17")
    
    async def get_institutional_investor_sale_trend(self, market: str, upcode: str, gubun2: str, gubun3: str, from_date: str, to_date: str) -> List[Dict]:
        return await self.get_specific_investor_sale_trend(market, upcode, gubun2, gubun3, from_date, to_date, sv_code="sv_18", sa_code="sa_18")

if __name__ == "__main__":

    async def main():
        fetcher = LSFetcher()
        # response = await fetcher.get_today_stock_infos(shcode="078020")
        # response = await fetcher.get_stock_chart_info(shcode="078020", ncnt=60, sdate="20240601", edate="20240710")
        response = await fetcher.get_institutional_investor_sale_trend(market="1", upcode="001", gubun2="1", gubun3="1", from_date="20240701", to_date="20240801")

        print(response)

    asyncio.run(main())