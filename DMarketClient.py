import json
import time
from datetime import datetime
from nacl.bindings import crypto_sign
import requests
import math
from furl import furl

class DMarket:
    def __init__(self, public_key, secret_key):
        self.public_key = public_key
        self.secret_key = secret_key
        self.selling_fee = 0.07
        self.api_url = "https://api.dmarket.com"
        self.latest_prices = {}
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
    def getPricesForItems(self, items):
        all_prices = {}
        items_per_request = 50
        for i in range(math.ceil(len(items)/items_per_request)):
            try:
                method = "GET"
                endpoint = "/price-aggregator/v1/aggregated-prices"
                params = {'Titles': items[i*items_per_request:(i+1)*items_per_request]}
                headers = self.generate_headers(method, endpoint, params)
                url = self.api_url + endpoint
                response = json.loads(requests.get(url, headers=headers, params=params).text)
                for aggr in response["AggregatedTitles"]:
                    all_prices[aggr["MarketHashName"]] = {}
                    all_prices[aggr["MarketHashName"]]["buy"] = 9999999999 if float(aggr["Offers"]['BestPrice']) <= 0 else math.floor(100 * float(aggr["Offers"]['BestPrice'])) / 100
                    all_prices[aggr["MarketHashName"]]["sell"] = math.floor(100 * float(aggr["Orders"]['BestPrice']) * (1.0 - self.selling_fee)) / 100
            except Exception as e:
                print("DMarket price fetch exception: " + str(e))
                continue
            print("Getting DMarket prices... {}%                                            ".format(100*i/math.ceil(len(items)/items_per_request)), end='\r')
            time.sleep(0.35)
        self.latest_prices.update(all_prices)
        return all_prices
    def buyItemAtBestPrice(self, item):
        pass
    def sellItemAtBestPrice(self, item):
        pass
    def withdrawItems(self, items):
        pass
    def depositItems(self, items):
        pass