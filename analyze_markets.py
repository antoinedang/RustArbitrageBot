import time
import pickle
from DMarketClient import *
from SwapGGClient import *

def saveToFile(filename, obj):
    with open(filename, 'wb') as file:
        pickle.dump(obj, file)

def loadFromFile(filename):
    try:
        with open(filename, 'rb') as file:
            obj = pickle.load(file)
            return obj
    except:
        return {}


dmarket = DMarket(public_key="43361c690ccddfd9e9bde83be42dd2cb27d3d3841c5496dbc95db0a609cc955e", secret_key="abedafd4b528dbf6e26436e223417d760496f7763a9a64ece9953464226f44ad43361c690ccddfd9e9bde83be42dd2cb27d3d3841c5496dbc95db0a609cc955e")
swapgg = SwapGG(api_key="40672ac2-5b00-4609-92fe-d260498a1f7c")

# with open("./data/rust_skins.txt") as f:
#     skins = [skin[:-1] for skin in f.readlines() if '$' not in skin]
    # print(dmarket.getPricesForItems(skins))

analysis_data_file = "market_data.pkl"

current_opportunities = None
market_analysis_start = time.time()
total_new_opportunities = 0
optimistic_estimated_profit = 0

market_stats = loadFromFile(analysis_data_file)
avg_opportunity_duration = market_stats.get("avg_opportunity_duration", 0)
avg_roi = market_stats.get("avg_roi", 0)
total_opportunities_detected = market_stats.get("total_opportunities_detected", 0)
sum_durations_item_opportunities = market_stats.get("sum_durations_item_opportunities", 0)
num_ended_item_opportunities = market_stats.get("num_ended_item_opportunities", 0)

while True:

    new_opportunities = {}

    swapgg_prices = swapgg.getPricesForAllItems()
    dmarket_prices = dmarket.getPricesForItems([str(item) for item in swapgg_prices.keys()])

    for item in swapgg_prices.keys():
        best_buy_price = min(dmarket_prices[item].get("buy",9999999), swapgg_prices[item].get("buy",9999999))
        best_sell_price = max(dmarket_prices[item].get("sell",0), swapgg_prices[item].get("sell",0))
        profit = math.floor((best_sell_price-best_buy_price) * 100) / 100
        if profit > 0:
            if best_buy_price == dmarket_prices[item].get("buy",9999999):
                buy_market = "DMarket"
                sell_market = "SwapGG"
            else:
                buy_market = "SwapGG"
                sell_market = "DMarket"
            new_opportunities[item] = (best_buy_price, best_sell_price, time.time())
            
            print("ARBITRAGE OPPORTUNITY -> {} -> buy on {} for ${}, sell on {} for ${} -> ${} profit".format(item, buy_market, best_buy_price, sell_market, best_sell_price, profit))

    if current_opportunities is None: current_opportunities = new_opportunities

    num_new_opportunities = 0
    roi_sum = 0
    for item in new_opportunities.keys():
        if item not in current_opportunities.keys() or (current_opportunities[item][0] != new_opportunities[item][0] and current_opportunities[item][1] != new_opportunities[item][1]): 
            num_new_opportunities += 1
            profit = math.floor((new_opportunities[item][1] - new_opportunities[item][0]) * 100) / 100
            roi = profit / new_opportunities[item][0]
            roi_sum += roi
            avg_roi = (avg_roi * total_opportunities_detected + roi) / (total_opportunities_detected + 1)
            total_opportunities_detected += 1
            optimistic_estimated_profit += profit
    new_ended_item_opportunities = 0
    for item in current_opportunities.keys():
        if item not in new_opportunities.keys() or (current_opportunities[item][0] != new_opportunities[item][0] and current_opportunities[item][1] != new_opportunities[item][1]):
            duration_of_item_opportunity =  time.time() - current_opportunities[item][2]
            sum_durations_item_opportunities += duration_of_item_opportunity
            num_ended_item_opportunities += 1
            new_ended_item_opportunities += 1


    current_opportunities = new_opportunities

    total_new_opportunities += num_new_opportunities
    time_since_analysis_start = time.time() - market_analysis_start

    try:
        print("Average ROI: {}%".format(100*(roi_sum/num_new_opportunities)))
    except:
        print("Average ROI: 0%")
    print("New opportunities: {}".format(num_new_opportunities))
    print("Lost opportunities: {}".format(new_ended_item_opportunities))
    print("Running average ROI: {}%".format(100 * avg_roi))
    try:
        print("Running average opportunity duration: {}s".format(sum_durations_item_opportunities/num_ended_item_opportunities))
    except:
        print("Running average opportunity duration: [N/A]s")
    print("Total opportunities detected: {}".format(total_opportunities_detected))
    print("Avg. new opportunities per hour: {}".format(3600 * total_new_opportunities / time_since_analysis_start))
    print("Estimated cumulative profit (assuming no failures, limitless funds): ${} USD".format(optimistic_estimated_profit))
    print("Estimated cumulative profit per hour (assuming no failures, limitless funds): ${} USD / hour".format(3600 * optimistic_estimated_profit / time_since_analysis_start))

    saveToFile(analysis_data_file, {
        "avg_opportunity_duration": avg_opportunity_duration,
        "avg_roi": avg_roi,
        "total_opportunities_detected": total_opportunities_detected,
        "sum_durations_item_opportunities": sum_durations_item_opportunities,
        "num_ended_item_opportunities": num_ended_item_opportunities })