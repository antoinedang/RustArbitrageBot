import json
import requests
import time
from currency_converter import CurrencyConverter
import math

class SwapGG:
    def __init__(self, api_key):
        self.selling_fee = 0.05
        self.api_url = "https://market-api.swap.gg"
        self.latest_prices = {}
        self.headers = {
            "Authorization": api_key
        }
        self.appId = 252490
    def getPricesForAllItems(self):
        eurToUsd = CurrencyConverter().convert(1, "EUR", "USD")
        all_prices = {}
        endpoint = "/v1/buyorders/summary"
        params = {'appId': self.appId}
        url = self.api_url + endpoint
        response = json.loads(requests.get(url, headers=self.headers, params=params).text)
        for item in response["result"].keys():
            all_prices[str(item)] = {}
            all_prices[str(item)]["sell"] = math.floor(eurToUsd * float(response["result"][item]['maxPrice']) * (1.0 - self.selling_fee)) / 100
        time.sleep(0.35)

        endpoint = "/v1/pricing/lowest"
        params = {'appId': self.appId}
        url = self.api_url + endpoint
        response = json.loads(requests.get(url, headers=self.headers, params=params).text)
        for item in response["result"].keys():
            if item not in all_prices.keys():
                all_prices[str(item)] = {}
            all_prices[str(item)]["buy"] = math.floor(eurToUsd * float(response["result"][item]['price'])) / 100
    
        self.latest_prices.update(all_prices)
        time.sleep(0.35)
        return all_prices
    def buyItemAtBestPrice(self, item):
        pass
    def sellItemAtBestPrice(self, item):
        pass
    def withdrawItems(self, items):
        pass
    def depositItems(self, items):
        pass