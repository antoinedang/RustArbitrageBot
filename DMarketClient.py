import json
import time
from datetime import datetime
from nacl.bindings import crypto_sign
import requests
import math
from furl import furl
import threading
import copy

class DMarket:
    def __init__(self, public_key, secret_key):
        self.public_key = public_key
        self.secret_key = secret_key
        self.selling_fee = 0.07
        self.currency_conversion_fee = 0.03
        self.api_url = "https://api.dmarket.com"
        self.prices = {}
        self.lock = threading.Lock()
    def generate_headers(self, method, endpoint, params, body={}):
        nonce = str(round(datetime.now().timestamp()))
        string_to_sign = method + endpoint
        string_to_sign = str(furl(string_to_sign).add(params))
        if body:
            string_to_sign += json.dumps(body)
        string_to_sign += nonce
        signature_prefix = "dmar ed25519 "
        encoded = string_to_sign.encode('utf-8')
        secret_bytes = bytes.fromhex(self.secret_key)
        signature_bytes = crypto_sign(encoded, secret_bytes)
        signature = signature_bytes[:64].hex()
        headers = {
            "X-Api-Key": self.public_key,
            "X-Request-Sign": signature_prefix + signature,
            "X-Sign-Date": nonce
        }
        return headers
    def updatePricesForItems(self, items):
        items_per_request = 100
        for i in range(math.ceil(len(items)/items_per_request)):
            method = "GET"
            endpoint = "/price-aggregator/v1/aggregated-prices"
            params = {'Titles': items[i*items_per_request:(i+1)*items_per_request]}
            headers = self.generate_headers(method, endpoint, params)
            url = self.api_url + endpoint
            response = json.loads(requests.get(url, headers=headers, params=params).text)
            for aggr in response["AggregatedTitles"]:
                self.lock.acquire()
                try:
                    if aggr["MarketHashName"] not in self.prices.keys(): self.prices[aggr["MarketHashName"]] = {}
                    self.prices[aggr["MarketHashName"]]["buy"] = 9999999999 if float(aggr["Offers"]['BestPrice']) <= 0 else math.floor(100 * float(aggr["Offers"]['BestPrice'])) / 100
                    self.prices[aggr["MarketHashName"]]["sell"] = math.floor(100 * float(aggr["Orders"]['BestPrice']) * (1.0 - (self.selling_fee + self.currency_conversion_fee))) / 100
                except Exception as e:
                    print("DMarket error: " + str(e))
                self.lock.release()
            time.sleep(0.35)
            # print("Getting DMarket prices... {}%                                            ".format(100*(i+1)/math.ceil(len(items)/items_per_request)), end='\r')

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