import asyncio
import json
import os
from typing import Dict, List

import httpx
import requests
from BaseFetcher import BaseFetcher
from decouple import config
from requests import Session

# from .BaseFetcher import BaseFetcher

# assert os.path.isfile(os.path.join(os.path.abspath(os.path.dirname(__file__)), ".env")), ".env file not found!"
assert os.path.isfile(".env"), ".env file not found!"


class LSFetcher(BaseFetcher):
    BASE_URL = "https://openapi.ls-sec.co.kr:8080"

    def __init__(self):
        self.headers = {"Content-Type": "application/x-www-form-urlencoded"}
        super().__init__(self.get_access_token())

    def fetch_data(self, url, headers={}, body={}):
        with Session() as session:
            try:
                response = session.request(
                    method="post",
                    url=f"{self.BASE_URL}/{url}",
                    headers=headers,
                    data=json.dumps(body),
                )
                return response
            except httpx.HTTPStatusError as e:
                print(
                    f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
                )
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

    def get_today_stock_infos(self, shcode: str) -> dict:
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.api_key}",
            "tr_cd": "t1102",
            "tr_cont": "N",
        }
        body = {"t1102InBlock": {"shcode": shcode}}

        response = self.fetch_data(url="stock/market-data", headers=headers, body=body)

        stocks = response.json()["t1102OutBlock"]
        return stocks

    def get_today_stock_hname(self, shcode: str) -> str:  # 한글명
        """
        Retrieves the Korean name of a stock from today's stock market data.

        Args:
            shcode (str): The stock code of the stock whose Korean name you want to fetch.

        Returns:
            str: The Korean name of the specific stock fetched from today's stock market data.
        """
        stock_infos = self.get_today_stock_infos(shcode=shcode)

        return stock_infos["hname"]

    def get_today_stock_price(self, shcode: str) -> int:  # 현재가
        """
        Retrieves the current price of a given stock.

        Args:
            shcode (str): The stock code of the stock the price of which should be returned.

        Returns:
            int: The current price of the provided stock.
        """
        stock_infos = self.get_today_stock_infos(shcode=shcode)

        return stock_infos["price"]

    def get_today_stock_diff(self, shcode: str) -> int:  # 등락율
        """
        Retrieves the price fluctuation rate of a given stock.

        Args:
            shcode (str): The stock code of the stock the fluctuation rate of which should be returned.

        Returns:
            int: The fluctuation rate of the provided stock.
        """
        stock_infos = self.get_today_stock_infos(shcode=shcode)

        return stock_infos["diff"]

    def get_today_stock_volume(self, shcode: str) -> int:  # 누적거래량
        """
        Retrieves the accumulated trading volume of a given stock.

        Args:
            shcode (str): The stock code of the stock the trading volume of which should be returned.

        Returns:
            int: The accumulated trading volume of the provided stock.
        """
        stock_infos = self.get_today_stock_infos(shcode=shcode)

        return stock_infos["volume"]

    def get_today_stock_open(self, shcode: str) -> int:  # 시가
        """
        Retrieves the opening price of a given stock of today.

        Args:
            shcode (str): The stock code of the stock the opening price of which should be returned.

        Returns:
            int: The opening price of the provided stock.
        """
        stock_infos = self.get_today_stock_infos(shcode=shcode)

        return stock_infos["open"]

    def get_today_stock_high(self, shcode: str) -> int:  # 고가
        """
        Retrieves the highest price of a given stock of today.

        Args:
            shcode (str): The stock code of the stock the highest price of which should be returned.

        Returns:
            int: The highest price of the provided stock.
        """
        stock_infos = self.get_today_stock_infos(shcode=shcode)

        return stock_infos["high"]

    def get_today_stock_low(self, shcode: str) -> int:  # 저가
        """
        Retrieves the lowest price of a given stock of today.

        Args:
            shcode (str): The stock code of the stock the lowest price of which should be returned.

        Returns:
            int: The lowest price of the provided stock.
        """
        stock_infos = self.get_today_stock_infos(shcode=shcode)

        return stock_infos["low"]

    def get_today_stock_per(self, shcode: str) -> int:  # PER
        """
        Retrieves the price-to-earnings ratio (PER) of a given stock of today.

        Args:
            shcode (str): The stock code of the stock the PER of which should be returned.

        Returns:
            int: The PER of the provided stock.
        """
        stock_infos = self.get_today_stock_infos(shcode=shcode)

        return stock_infos["per"]

    def get_today_stock_total(self, shcode: str) -> int:  # 시가 총액
        """
        Retrieves the market capitalization of a given stock of today.

        Args:
            shcode (str): The stock code of the stock the market capitalization of which should be returned.

        Returns:
            int: The market capitalization of the provided stock.
        """
        stock_infos = self.get_today_stock_infos(shcode=shcode)

        return stock_infos["total"]

    def get_stock_chart_info(
        self, shcode: str, ncnt: int, sdate: str = "", edate: str = ""
    ):  # 주식 차트
        """
        Retrieves the stock chart information for a given stock.

        Args:
            shcode (str): The stock code of the stock whose chart information you want to fetch.
            ncnt (int): The time unit for the chart data.
            sdate (str, optional): The start date for the chart data in 'YYYYMMDD' format. Defaults to "".
            edate (str, optional): The end date for the chart data in 'YYYYMMDD' format. Defaults to "".

        Returns:
            List[Dict]: The stock chart information.
        """
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.api_key}",
            "tr_cd": "t8412",
            "tr_cont": "N",
        }
        body = {
            "t8412InBlock": {
                "shcode": shcode,  # shortcut code
                "ncnt": ncnt,  # time unit
                "qrycnt": 0,
                "nday": "0",
                "sdate": sdate,  # "YYYYMMDD"
                "edate": edate,  # "YYYYMMDD"
                "cts_date": "",
                "cts_time": "",
                "comp_yn": "N",
            }
        }

        response = self.fetch_data(url="stock/chart", headers=headers, body=body)

        stocks = response.json()["t8412OutBlock1"]
        return stocks

    def get_investor_sale_trend(
        self,
        upcode: str,
        gubun2: str,
        gubun3: str,
        from_date: str,
        to_date: str,
    ) -> List[Dict]:
        """Fetches the investor sale trend for a given market and period.

        Args:
            market (str): The market identifier.
            upcode (str): The upcode of the stock.
            gubun2 (str): The second classification for the trend data.
            gubun3 (str): The third classification for the trend data.
            from_date (str): The start date for the trend data in 'YYYYMMDD' format.
            to_date (str): The end date for the trend data in 'YYYYMMDD' format.

        Returns:
            List[Dict]: The investor sale trend data.
        """
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.api_key}",
            "tr_cd": "t1665",
            "tr_cont": "N",
        }
        body = {
            "t1665InBlock": {
                "market": market,
                "upcode": upcode,
                "gubun2": gubun2,
                "gubun3": gubun3,
                "from_date": from_date,  # "YYYYMMDD"
                "to_date": to_date,  # "YYYYMMDD"
            }
        }

        response = self.fetch_data(url="stock/chart", headers=headers, body=body)

        sale_trends = response.json()["t1665OutBlock1"]
        return sale_trends

    def get_specific_investor_sale_trend(
        self,
        market: str,
        upcode: str,
        gubun2: str,
        gubun3: str,
        from_date: str,
        to_date: str,
        sv_code: str,
        sa_code: str,
    ) -> List[Dict]:
        total_investor_sale_trends = self.get_investor_sale_trend(
            upcode, gubun2, gubun3, from_date, to_date
        )

        specific_investor_sale_trend = []

        for temp_trend in total_investor_sale_trends:
            temp_date = temp_trend["date"]  # 일자
            temp_sale_volume = temp_trend[sv_code]  # 개인 매매 수량
            temp_sale_amount = temp_trend[sa_code]  # 개인 매매 금액

            specific_investor_sale_trend.append(
                {
                    "date": temp_date,
                    "sale_volume": temp_sale_volume,
                    "sale_amount": temp_sale_amount,
                }
            )

        return specific_investor_sale_trend

    def get_individual_investor_sale_trend(
        self,
        market: str,
        upcode: str,
        gubun2: str,
        gubun3: str,
        from_date: str,
        to_date: str,
    ) -> List[Dict]:
        """
        Fetches the sale trend of individual investors in the KOSPI.

        Args:
            market (str): The market identifier.
            upcode (str): The upcode of the stock.
            gubun2 (str): The second classification for the trend data.
            gubun3 (str): The third classification for the trend data.
            from_date (str): The start date for the trend data in 'YYYYMMDD' format.
            to_date (str): The end date for the trend data in 'YYYYMMDD' format.

        Returns:
            List[Dict]: The sale trend data for individual investors.
        """
        return self.get_specific_investor_sale_trend(
            upcode,
            gubun2,
            gubun3,
            from_date,
            to_date,
            sv_code="sv_08",
            sa_code="sa_08",
        )

    def get_foreign_investor_sale_trend(
        self,
        market: str,
        upcode: str,
        gubun2: str,
        gubun3: str,
        from_date: str,
        to_date: str,
    ) -> List[Dict]:
        """
        Fetches the sale trend of foreign investors in the KOSPI.

        Args:
            market (str): The market identifier.
            upcode (str): The upcode of the stock.
            gubun2 (str): The second classification for the trend data.
            gubun3 (str): The third classification for the trend data.
            from_date (str): The start date for the trend data in 'YYYYMMDD' format.
            to_date (str): The end date for the trend data in 'YYYYMMDD' format.

        Returns:
            List[Dict]: The sale trend data for foreign investors.
        """

        return self.get_specific_investor_sale_trend(
            upcode,
            gubun2,
            gubun3,
            from_date,
            to_date,
            sv_code="sv_17",
            sa_code="sa_17",
        )

    def get_institutional_investor_sale_trend(
        self,
        market: str,
        upcode: str,
        gubun2: str,
        gubun3: str,
        from_date: str,
        to_date: str,
    ) -> List[Dict]:
        """
        Fetches the sale trend of institutional investors in the KOSPI.

        Args:
            market (str): The market identifier.
            upcode (str): The upcode of the stock.
            gubun2 (str): The second classification for the trend data.
            gubun3 (str): The third classification for the trend data.
            from_date (str): The start date for the trend data in 'YYYYMMDD' format.
            to_date (str): The end date for the trend data in 'YYYYMMDD' format.

        Returns:
            List[Dict]: The sale trend data for institutional investors.
        """

        return self.get_specific_investor_sale_trend(
            upcode,
            gubun2,
            gubun3,
            from_date,
            to_date,
            sv_code="sv_18",
            sa_code="sa_18",
        )

    def get_etf_composition(self, shcode: str, date: str, sgb: str):
        """
        Fetches the ETF composition for a given stock.

        Args:
            shcode (str): The stock code of the ETF.
            date (str): The date for which to fetch the ETF composition in 'YYYYMMDD' format.
            sgb (str): The specific classification for the ETF composition data.

        Returns:
            List[Dict]: The ETF composition data.
        """
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.api_key}",
            "tr_cd": "t1904",
            "tr_cont": "N",
        }
        body = {
            "t1904InBlock": {
                "shcode": shcode,
                "date": date,
                "sgb": sgb,
            }
        }

        response = self.fetch_data(url="stock/etf", headers=headers, body=body)

        etf_comp_total = response.json()["t1904OutBlock1"]
        etf_comp_summary = []

        for etf_comp in etf_comp_total:
            hname = etf_comp["hname"]
            weight = etf_comp["weight"]

            etf_comp_summary.append(
                {
                    "hname": hname,
                    "weight": weight,
                }
            )

        return etf_comp_summary

    def get_high_fluctuation_item(self, amount: int, gubun2: str):
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.api_key}",
            "tr_cd": "t1441",
            "tr_cont": "N",
        }
        body = {
            "t1441InBlock": {
                "gubun1": "0",
                "gubun2": gubun2,  # 상승률: 0, 하락률: 1
                "gubun3": "1",
                "jc_num": 0,
                "sprice": 0,
                "eprice": 0,
                "volume": 0,
                "idx": 0,
                "jc_num2": 0,
            }
        }

        response = self.fetch_data(url="stock/high-item", headers=headers, body=body)

        print(response.json())
        high_items = response.json()["t1441OutBlock1"]
        result = []

        for high_item in high_items[:amount]:
            hname = high_item["hname"]
            increase_rate = high_item["jnildiff"]
            result.append(
                {
                    "hname": hname,
                    "increase_rate": increase_rate,
                }
            )
        return result

    def get_high_increase_rate_item(self, amount: int):  # 전일 상승률 상위 종목
        """
        Fetches the items with the highest increase rates from the previous day.

        Args:
            amount (int): The number of items to fetch.

        Returns:
            List[Dict]: The items with the highest increase rates.
        """
        return self.get_high_fluctuation_item(amount=amount, gubun2="0")

    def get_high_decrease_rate_item(self, amount: int):  # 전일 하락률 상위 종목
        """
        Fetches the items with the highest decrease rates from the previous day.

        Args:
            amount (int): The number of items to fetch.

        Returns:
            List[Dict]: The items with the highest decrease rates.
        """

        return self.get_high_fluctuation_item(amount=amount, gubun2="1")


if __name__ == "__main__":

    pass

    def main():
        fetcher = LSFetcher()
        response = fetcher.get_today_stock_per(shcode="078020")
        # response = fetcher.get_stock_chart_info(shcode="078020", ncnt=60, sdate="20240601", edate="20240710")
        # response = fetcher.get_institutional_investor_sale_trend(upcode="001", gubun2="1", gubun3="1", from_date="20240701", to_date="20240801")
        # response = fetcher.get_etf_composition(shcode="448330", date="20240104", sgb="1")
        # response = fetcher.get_high_decrease_rate_item(amount=5)

        print(response)
        # print(fetcher.get_high_decrease_rate_item.__doc__)

    main()
