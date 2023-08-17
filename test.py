import time
from DMarketClient import *
from SwapGGClient import *

dmarket = DMarket(public_key="43361c690ccddfd9e9bde83be42dd2cb27d3d3841c5496dbc95db0a609cc955e", secret_key="abedafd4b528dbf6e26436e223417d760496f7763a9a64ece9953464226f44ad43361c690ccddfd9e9bde83be42dd2cb27d3d3841c5496dbc95db0a609cc955e")
swapgg = SwapGG(api_key="40672ac2-5b00-4609-92fe-d260498a1f7c")

# with open("./data/rust_skins.txt") as f:
#     skins = [skin[:-1] for skin in f.readlines() if '$' not in skin]
    # print(dmarket.getPricesForItems(skins))

while True:

    swapgg_prices = swapgg.getPricesForAllItems()
    dmarket_prices = dmarket.getPricesForItems([str(item) for item in swapgg_prices.keys()])

    for item in swapgg_prices.keys():
        best_buy_price = min(dmarket_prices[item].get("buy",9999999), swapgg_prices[item].get("buy",9999999))
        best_sell_price = max(dmarket_prices[item].get("sell",0), swapgg_prices[item].get("sell",0))
        profit = math.floor((best_sell_price-best_buy_price) * 100) / 100
        if profit > 0:
            if best_buy_price == dmarket_prices[item].get("buy",9999999):
                buyMarket = "DMarket"
                sellMarket = "SwapGG"
            else:
                buyMarket = "SwapGG"
                sellMarket = "DMarket"
            print("ARBITRAGE OPPORTUNITY -> {} -> buy on {} for ${}, sell on {} for ${} -> ${} profit".format(item, buyMarket, best_buy_price, sellMarket, best_sell_price, profit))