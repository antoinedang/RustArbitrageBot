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

def scan_for_opportunities():
    global current_opportunities
    while scanning_active:
        for item in swapgg.getLatestPrices().keys():
            if not scanning_active: return
            dmarket_prices = dmarket.getLatestPrices()
            swapgg_prices = swapgg.getLatestPrices()
            try:
                best_buy_price = min(dmarket_prices[item].get("buy",9999999), swapgg_prices[item].get("buy",9999999))
                best_sell_price = max(dmarket_prices[item].get("sell",0), swapgg_prices[item].get("sell",0))
            except KeyError: continue
            profit = math.floor((best_sell_price-best_buy_price) * 100) / 100
            if profit > 0:
                if best_buy_price == dmarket_prices[item].get("buy",9999999):
                    buy_market = "DMarket"
                    sell_market = "SwapGG"
                else:
                    buy_market = "SwapGG"
                    sell_market = "DMarket"
                if not current_opportunities_lock.acquire(timeout=lock_timeout):
                    print("Likely deadlock on current_opportunities_lock")
                try:
                    if item not in current_opportunities.keys(): 
                        # New opportunity
                        current_opportunities[item] = (best_buy_price, best_sell_price, time.time(), buy_market, sell_market)
                    elif current_opportunities[item][0] != best_buy_price and current_opportunities[item][1] != best_sell_price:
                        # Opportunity changed but is still profitable
                        #TODO: handle this as previous opportunity ending as well?
                        register_opportunity_end(item)
                        current_opportunities[item] = (best_buy_price, best_sell_price, time.time(), buy_market, sell_market)
                except Exception as e:
                    print("scan_for_opportunities error: {}".format(e))
                current_opportunities_lock.release()
        print("Finished scan...              ", end='\r')
            
def log(msg):
    if not log_lock.acquire(timeout=lock_timeout):
        print("Likely deadlock on log_lock")
    try:
        with open(analysis_output_file, 'a') as file: file.write(msg + '\n')
        print(msg)
    except Exception as e:
        print("log error: {}".format(e))
    log_lock.release()

def update_market_stats(profit, roi, duration):
    global optimistic_estimated_profit
    global avg_roi
    global avg_profit
    global avg_opportunity_duration
    global min_opportunity_duration
    global max_opportunity_duration
    global total_opportunities_detected
    
    if not market_stats_lock.acquire(timeout=lock_timeout):
        print("Likely deadlock on market_stats_lock")
        
    try:
        optimistic_estimated_profit += profit
        avg_roi = (avg_roi * total_opportunities_detected + roi) / (total_opportunities_detected + 1)
        avg_profit = (avg_profit * total_opportunities_detected + profit) / (total_opportunities_detected + 1)
        avg_opportunity_duration = (avg_opportunity_duration * total_opportunities_detected + duration) / (total_opportunities_detected + 1)
        min_opportunity_duration = min(duration, min_opportunity_duration)
        max_opportunity_duration = max(duration, max_opportunity_duration)
        total_opportunities_detected += 1
    except Exception as e:
        print("update_market_stats error: {}".format(e))
    market_stats_lock.release()

    log("Running average ROI: {}%".format(100 * avg_roi))
    log("Running average profit per opportunity: ${} USD".format(avg_profit))
    log("Running average opportunity duration: {}s".format(avg_opportunity_duration))
    log("Max. opportunity duration: {}s".format(max_opportunity_duration))
    log("Min. opportunity duration: {}s".format(min_opportunity_duration))
    log("Total opportunities detected: {}".format(total_opportunities_detected))
    log("Avg. new opportunities per hour: {}".format(3600 * total_opportunities_detected / total_time_elapsed_during_analysis))
    log("Estimated cumulative profit (assuming no failures, limitless funds): ${} USD".format(optimistic_estimated_profit))
    log("Estimated cumulative profit per hour (assuming no failures, limitless funds): ${} USD / hour".format(3600 * optimistic_estimated_profit / total_time_elapsed_during_analysis))
    log("")

def register_opportunity_end(item):
    global current_opportunities
    duration = time.time()-current_opportunities[item][2]
    profit = current_opportunities[item][1]-current_opportunities[item][0]
    roi = (current_opportunities[item][1]-current_opportunities[item][0])/current_opportunities[item][0]
    #Opportunity no longer available
    log("ARBITRAGE OPPORTUNITY ENDED -> {} -> buy on {} for ${}, sell on {} for ${}".format(item, current_opportunities[item][3], current_opportunities[item][0], current_opportunities[item][4], current_opportunities[item][1]))
    log("Profit: ${} USD".format(profit))
    log("ROI: {}%".format(roi))
    log("Duration: {}s".format(duration))
    log("")
    update_market_stats(profit, roi, duration)
    del current_opportunities[item]

def update_swapgg_prices():
    while update_market_prices:
        swapgg.updatePricesForAllItems()

def update_dmarket_prices():
    while update_market_prices:
        dmarket.updatePricesForItems(list(swapgg.getLatestPrices().keys()))
        print("Updated DMarket prices...                   ", end='\r')

def update_market_data():
    global total_time_elapsed_during_analysis
    while update_market_data_active:
        if not market_stats_lock.acquire(timeout=lock_timeout):
            print("Likely deadlock on market_stats_lock")
        try:
            total_time_elapsed_during_analysis = market_stats.get("total_time_elapsed_during_analysis", 0) + (time.time() - analysis_start_time)
            saveToFile(analysis_data_file, {
                "optimistic_estimated_profit": optimistic_estimated_profit,
                "total_opportunities_detected": total_opportunities_detected,
                "avg_opportunity_duration": avg_opportunity_duration,
                "min_opportunity_duration": min_opportunity_duration,
                "max_opportunity_duration": max_opportunity_duration,
                "avg_roi": avg_roi,
                "avg_profit": avg_profit,
                "total_time_elapsed_during_analysis": total_time_elapsed_during_analysis })
        except Exception as e:
            print("update_market_data error: {}".format(e))
        market_stats_lock.release()
    
def check_current_opportunities():
    while checking_active:
        if not current_opportunities_lock.acquire(timeout=lock_timeout):
            print("Likely deadlock on current_opportunities_lock")
        try: items = [str(k) for k in current_opportunities.keys()]
        except Exception as e: print("check_current_opportunities p1 error: {}".format(e))
        current_opportunities_lock.release()
        for item in items:
            if not checking_active: return
            dmarket_price = dmarket.getLatestPrices()[item]
            swapgg_price = swapgg.getLatestPrices()[item]

            best_buy_price = min(dmarket_price.get("buy",9999999), swapgg_price.get("buy",9999999))
            best_sell_price = max(dmarket_price.get("sell",0), swapgg_price.get("sell",0))
            profit = math.floor((best_sell_price-best_buy_price) * 100) / 100

            if not current_opportunities_lock.acquire(timeout=lock_timeout):
                print("Likely deadlock on current_opportunities_lock")
            try:
                if profit < 0: register_opportunity_end(item)
            except Exception as e:
                print("check_current_opportunities p2 error: {}".format(e))
            current_opportunities_lock.release()


analysis_data_file = "data/market_data.pkl"
analysis_output_file = "data/analysis_result.txt"

log_lock = threading.Lock()
market_stats = loadFromFile(analysis_data_file)
market_stats_lock = threading.Lock()
analysis_start_time = time.time()
current_opportunities = {}
current_opportunities_lock = threading.Lock()
optimistic_estimated_profit = market_stats.get("optimistic_estimated_profit", 0)
total_opportunities_detected = market_stats.get("total_opportunities_detected", 0)
avg_opportunity_duration = market_stats.get("avg_opportunity_duration", 0)
min_opportunity_duration = market_stats.get("min_opportunity_duration", 0)
max_opportunity_duration = market_stats.get("max_opportunity_duration", 999999999)
avg_roi = market_stats.get("avg_roi", 0)
avg_profit = market_stats.get("avg_profit", 0)
lock_timeout = 10

dmarket = DMarket(public_key="43361c690ccddfd9e9bde83be42dd2cb27d3d3841c5496dbc95db0a609cc955e", secret_key="abedafd4b528dbf6e26436e223417d760496f7763a9a64ece9953464226f44ad43361c690ccddfd9e9bde83be42dd2cb27d3d3841c5496dbc95db0a609cc955e")
swapgg = SwapGG(api_key="40672ac2-5b00-4609-92fe-d260498a1f7c")

update_market_data_thread = threading.Thread(target=update_market_data)
market_price_threads = [threading.Thread(target=update_dmarket_prices), threading.Thread(target=update_swapgg_prices)]
scanner_thread = threading.Thread(target=scan_for_opportunities)
checking_thread = threading.Thread(target=check_current_opportunities)

try:
    update_market_data_active = True
    update_market_prices = True
    scanning_active = True
    checking_active = True
    print("Starting analysis...", end='\r')
    update_market_data_thread.start()
    for m in market_price_threads: m.start()
    scanner_thread.start()
    checking_thread.start()
    while True:
        pass
except KeyboardInterrupt:
    print("Ending scan...")
    scanning_active = False
    scanner_thread.join()
    print("Ending checking...")
    checking_active = False
    checking_thread.join()
    print("Ending market updates...")
    update_market_data_active = False
    update_market_prices = False
    update_market_data_thread.join()
    for m in market_price_threads: m.join()
    print("Ending ongoing opportunities...")
    items = [str(k) for k in current_opportunities.keys()]
    log("======= OPPORTUNITIES ENDED PREMATURELY =======")
    for item in items:
        # Artificially "end" all ongoing opportunities for logging/debugging purposes
        register_opportunity_end(item)
    log("===============================================")
    print("Done.")