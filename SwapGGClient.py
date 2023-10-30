import json
import requests
import time
from currency_converter import CurrencyConverter
import math
import threading
import copy

class SwapGG:
    def __init__(self, api_key):
        self.selling_fee = 0.05
        self.currency_conversion_fee = 0.03
        self.api_url = "https://market-api.swap.gg"
        self.prices = {}
        self.headers = {
            "Authorization": api_key
        }
        self.appId = 252490
        self.lock = threading.Lock()
    def updatePricesForAllItems(self):
        eurToUsd = CurrencyConverter().convert(1, "EUR", "USD")

        endpoint = "/v1/buyorders/summary"
        params = {'appId': self.appId}
        url = self.api_url + endpoint
        response = json.loads(requests.get(url, headers=self.headers, params=params).text)
        for item in response["result"].keys():
            self.lock.acquire()
            try:
                if item not in self.prices.keys():
                    self.prices[str(item)] = {}
                self.prices[str(item)]["sell"] = math.floor(eurToUsd * float(response["result"][item]['maxPrice']) * (1.0 - (self.selling_fee + self.currency_conversion_fee))) / 100
            except Exception as e:
                print("Swapgg p2 error: " + str(e))
            self.lock.release()

        endpoint = "/v1/pricing/lowest"
        params = {'appId': self.appId}
        url = self.api_url + endpoint
        response = json.loads(requests.get(url, headers=self.headers, params=params).text)
        for item in response["result"].keys():
            self.lock.acquire()
            try:
                if item not in self.prices.keys():
                    self.prices[str(item)] = {}
                self.prices[str(item)]["buy"] = math.floor(eurToUsd * float(response["result"][item]['price'])) / 100
            except Exception as e:
                print("Swapgg p2 error: " + str(e))
            self.lock.release()
    
        time.sleep(0.5)
    def getLatestPrices(self):
        self.lock.acquire()
        prices_copy = copy.deepcopy(self.prices)
        self.lock.release()
        return prices_copy
    def buyItemAtPrice(self, item, price):
        pass
    def sellItemAtPrice(self, item, price):
        pass
    def withdrawItems(self, items):
        pass
    def depositItems(self, items):
        pass