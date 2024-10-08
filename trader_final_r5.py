from typing import Dict, List
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import Any
import string
import json
import numpy as np
import collections
from collections import defaultdict
import random
import math
import copy
import numpy as np
import statistics 

class Logger:
    def __init__(self) -> None:
        self.logs = ""
        self.max_log_length = 3750

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]], conversions: int, trader_data: str) -> None:
        base_length = len(self.to_json([
            self.compress_state(state, ""),
            self.compress_orders(orders),
            conversions,
            "",
            "",
        ]))

        # We truncate state.traderData, trader_data, and self.logs to the same max. length to fit the log limit
        max_item_length = (self.max_log_length - base_length) // 3

        print(self.to_json([
            self.compress_state(state, self.truncate(state.traderData, max_item_length)),
            self.compress_orders(orders),
            conversions,
            self.truncate(trader_data, max_item_length),
            self.truncate(self.logs, max_item_length),
        ]))

        self.logs = ""

    def compress_state(self, state: TradingState, trader_data: str) -> list[Any]:
        return [
            state.timestamp,
            trader_data,
            self.compress_listings(state.listings),
            self.compress_order_depths(state.order_depths),
            self.compress_trades(state.own_trades),
            self.compress_trades(state.market_trades),
            state.position,
            self.compress_observations(state.observations),
        ]

    def compress_listings(self, listings: dict[Symbol, Listing]) -> list[list[Any]]:
        compressed = []
        for listing in listings.values():
            compressed.append([listing["symbol"], listing["product"], listing["denomination"]])

        return compressed

    def compress_order_depths(self, order_depths: dict[Symbol, OrderDepth]) -> dict[Symbol, list[Any]]:
        compressed = {}
        for symbol, order_depth in order_depths.items():
            compressed[symbol] = [order_depth.buy_orders, order_depth.sell_orders]

        return compressed

    def compress_trades(self, trades: dict[Symbol, list[Trade]]) -> list[list[Any]]:
        compressed = []
        for arr in trades.values():
            for trade in arr:
                compressed.append([
                    trade.symbol,
                    trade.price,
                    trade.quantity,
                    trade.buyer,
                    trade.seller,
                    trade.timestamp,
                ])

        return compressed

    def compress_observations(self, observations: Observation) -> list[Any]:
        conversion_observations = {}
        for product, observation in observations.conversionObservations.items():
            conversion_observations[product] = [
                observation.bidPrice,
                observation.askPrice,
                observation.transportFees,
                observation.exportTariff,
                observation.importTariff,
                observation.sunlight,
                observation.humidity,
            ]

        return [observations.plainValueObservations, conversion_observations]

    def compress_orders(self, orders: dict[Symbol, list[Order]]) -> list[list[Any]]:
        compressed = []
        for arr in orders.values():
            for order in arr:
                compressed.append([order.symbol, order.price, order.quantity])

        return compressed

    def to_json(self, value: Any) -> str:
        return json.dumps(value, cls=ProsperityEncoder, separators=(",", ":"))

    def truncate(self, value: str, max_length: int) -> str:
        if len(value) <= max_length:
            return value

        return value[:max_length - 3] + "..."

logger = Logger()

class Trader:
    
    basket_std = 78

    POSITION_LIMIT = {"AMETHYSTS": 20, "STARFRUIT": 20, "ORCHIDS": 100, "GIFT_BASKET": 60, "CHOCOLATE": 250, "STRAWBERRIES": 350, "ROSES": 60, "COCONUT": 300, "COCONUT_COUPON": 600}

    position = {"AMETHYSTS": 0, "STARFRUIT": 0, "ORCHIDS": 0, "CHOCOLATE": 0, "STRAWBERRIES": 0, "ROSES": 0, "GIFT_BASKET": 0, "COCONUT": 0, "COCONUT_COUPON": 0}
    spread_cache = []
    spread_cache_size = 200
    starfruit_cache = []
    starfruit_dim = 4
    cont_buy_basket_unfill = 0
    cont_sell_basket_unfill = 0
    timestamp_curr = 0

    def get_prices(self, state: TradingState, symbol: Symbol):
        buy_orders = list(state.order_depths[symbol].buy_orders.items())
        sell_orders = list(state.order_depths[symbol].sell_orders.items())
        best_bid, best_bid_volume = buy_orders[0]
        best_ask, best_ask_volume = sell_orders[0]
        return best_bid, best_ask, (best_bid + best_ask) / 2, best_bid_volume, best_ask_volume

    def calc_next_price_starfruit(self):
        coeff = [0.18895127, 0.20771801, 0.26114406, 0.34171985]
        intercept = 2.3552758852292754
        nxt_price = intercept
        for i, val in enumerate(self.starfruit_cache):
            nxt_price += val * coeff[i]
        return int(round(nxt_price))

    def compute_orders_sf(self, order_depth, acc_bid, acc_ask):
        STARFRUIT_POS_LIMIT = 20
        orders: list[Order] = []

        sell_orders = list(order_depth.sell_orders.items())
        buy_orders = list(order_depth.buy_orders.items())
        best_ask, best_ask_amount = sell_orders[0]
        best_bid, best_bid_amount = buy_orders[0]

        curr_pos = self.position["STARFRUIT"]

        for ask, vol in sell_orders:
            if ((ask <= acc_bid) or ((self.position["STARFRUIT"] < 0) and (ask == acc_bid + 1))) and curr_pos < STARFRUIT_POS_LIMIT: ## Try adding (self.position[product]<0) and (ask == acc_bid+1) to the condition
                order_for = min(-vol, STARFRUIT_POS_LIMIT - curr_pos)
                curr_pos += order_for
                assert(order_for >= 0)
                orders.append(Order("STARFRUIT", ask, order_for))

        if best_bid + 1 <= acc_bid:
            if curr_pos < STARFRUIT_POS_LIMIT:
                num = STARFRUIT_POS_LIMIT - curr_pos
                orders.append(Order("STARFRUIT", best_bid + 1, num))
                curr_pos += num


        curr_pos = self.position["STARFRUIT"]

        for bid, vol in buy_orders:
            if ((bid >= acc_ask) or ((self.position["STARFRUIT"] > 0) and (bid == acc_ask - 1))) and curr_pos > -STARFRUIT_POS_LIMIT: ## Try adding (self.position[product]>0) and (bid == acc_ask-1) to the condition
                order_for = max(-vol, -STARFRUIT_POS_LIMIT-curr_pos)
                curr_pos += order_for
                assert(order_for <= 0)
                orders.append(Order("STARFRUIT", bid, order_for))

        if best_ask - 1 >= acc_ask:
            if curr_pos > -STARFRUIT_POS_LIMIT:
                num = -STARFRUIT_POS_LIMIT-curr_pos
                orders.append(Order("STARFRUIT", best_ask - 1, num))
                curr_pos += num

        return orders

    def compute_orders_amethysts(self, order_depth, acc_bid, acc_ask):
        AMETHYSTS_POS_LIMIT = 20
        orders: list[Order] = []

        sell_orders = list(order_depth.sell_orders.items())
        buy_orders = list(order_depth.buy_orders.items())
        best_ask, best_ask_amount = sell_orders[0]
        best_bid, best_bid_amount = buy_orders[0]

        undercut_buy = best_bid + 1
        undercut_sell = best_ask - 1

        bid_price = min(undercut_buy, acc_bid - 1)
        ask_price = max(undercut_sell, acc_ask + 1)

        curr_pos = self.position["AMETHYSTS"]

        for ask, vol in sell_orders:
            if ((ask < acc_bid) or ((self.position["AMETHYSTS"] < 0) and (ask == acc_bid))) and curr_pos < AMETHYSTS_POS_LIMIT:
                order_for = min(-vol, AMETHYSTS_POS_LIMIT - curr_pos)
                curr_pos += order_for
                assert(order_for >= 0)
                orders.append(Order("AMETHYSTS", ask, order_for))
        
        if curr_pos < AMETHYSTS_POS_LIMIT:
            num = AMETHYSTS_POS_LIMIT - curr_pos
            orders.append(Order("AMETHYSTS", bid_price, num))
            curr_pos += num
        
        curr_pos = self.position["AMETHYSTS"]

        for bid, vol in buy_orders:
            if ((bid > acc_ask) or ((self.position["AMETHYSTS"] > 0) and (bid == acc_ask))) and curr_pos > -AMETHYSTS_POS_LIMIT:
                order_for = max(-vol, -AMETHYSTS_POS_LIMIT-curr_pos)
                curr_pos += order_for
                assert(order_for <= 0)
                orders.append(Order("AMETHYSTS", bid, order_for))

        if curr_pos > -AMETHYSTS_POS_LIMIT:
            num = -AMETHYSTS_POS_LIMIT-curr_pos
            orders.append(Order("AMETHYSTS", ask_price, num))
            curr_pos += num

        return orders

    def get_orders_basket(self, state: TradingState):
        GIFT_BASKET_POS_LIMIT = 60
        gift_basket = []
        chocolate = []
        strawberries = []
        roses = []

        best_bid_basket, best_ask_basket, mid_price_basket, best_bid_volume_basket, best_ask_volume_basket = self.get_prices(state, "GIFT_BASKET")
        best_bid_chocolate, best_ask_chocolate, mid_price_chocolate, best_bid_volume_chocolate, best_ask_volume_chocolate = self.get_prices(state, "CHOCOLATE")
        best_bid_strawberries, best_ask_strawberries, mid_price_strawberries, best_bid_volume_strawberries, best_ask_volume_strawberries = self.get_prices(state, "STRAWBERRIES")
        best_bid_roses, best_ask_roses, mid_price_roses, best_bid_volume_roses, best_ask_volume_roses = self.get_prices(state, "ROSES")

        # spread = mid_price_basket - 4*mid_price_chocolate - 6*mid_price_strawberries - mid_price_roses
        # if len(self.spread_cache) == self.spread_cache_size:
        #     self.spread_cache.pop(0)
        # self.spread_cache.append(spread)

        # avg_spread = np.mean(np.array(self.spread_cache))
        # std_spread = np.std(np.array(self.spread_cache))
        # curr_pos = self.position["GIFT_BASKET"]

        # if (len(self.spread_cache) > 3):
        #     spread_3 = np.mean(np.array(self.spread_cache[-3:]))
        #     if (spread_3 > avg_spread + 2*std_spread):
        #         gift_basket.append(Order("GIFT_BASKET", best_ask_basket, min(GIFT_BASKET_POS_LIMIT - curr_pos, -best_ask_volume_basket)))
        #     elif (spread_3 < avg_spread - 2*std_spread):
        #         gift_basket.append(Order("GIFT_BASKET", best_bid_basket, max(-GIFT_BASKET_POS_LIMIT-curr_pos, -best_bid_volume_basket)))
        orders = {'CHOCOLATE' : [], 'STRAWBERRIES': [], 'ROSES' : [], 'GIFT_BASKET' : []}
        prods = ['CHOCOLATE', 'STRAWBERRIES', 'ROSES', 'GIFT_BASKET']
        osell, obuy, best_sell, best_buy, worst_sell, worst_buy, mid_price, vol_buy, vol_sell = {}, {}, {}, {}, {}, {}, {}, {}, {}

        for p in prods:
            osell[p] = collections.OrderedDict(sorted(state.order_depths[p].sell_orders.items()))
            obuy[p] = collections.OrderedDict(sorted(state.order_depths[p].buy_orders.items(), reverse=True))

            best_sell[p] = next(iter(osell[p]))
            best_buy[p] = next(iter(obuy[p]))

            worst_sell[p] = next(reversed(osell[p]))
            worst_buy[p] = next(reversed(obuy[p]))

            mid_price[p] = (best_sell[p] + best_buy[p])/2
            vol_buy[p], vol_sell[p] = 0, 0
            for price, vol in obuy[p].items():
                vol_buy[p] += vol 
                if vol_buy[p] >= self.POSITION_LIMIT[p]/10:
                    break
            for price, vol in osell[p].items():
                vol_sell[p] += -vol 
                if vol_sell[p] >= self.POSITION_LIMIT[p]/10:
                    break

        res_buy = mid_price_basket - mid_price_chocolate*4 - mid_price_strawberries*6 - mid_price_roses - 376
        res_sell = mid_price_basket - mid_price_chocolate*4 - mid_price_strawberries*6 - mid_price_roses - 376

        trade_at = self.basket_std*0.5
        close_at = self.basket_std*(-1000)

        pb_pos = self.position['GIFT_BASKET']
        pb_neg = self.position['GIFT_BASKET']

        if self.position['GIFT_BASKET'] == self.POSITION_LIMIT['GIFT_BASKET']:
            self.cont_buy_basket_unfill = 0
        if self.position['GIFT_BASKET'] == -self.POSITION_LIMIT['GIFT_BASKET']:
            self.cont_sell_basket_unfill = 0

        do_bask = 0

        if res_sell < -trade_at:
            vol = self.position['GIFT_BASKET'] + self.POSITION_LIMIT['GIFT_BASKET']
            self.cont_buy_basket_unfill = 0 # no need to buy rn
            assert(vol >= 0)
            if vol > 0:
                do_bask = 1
                basket_sell_sig = 1
                gift_basket.append(Order('GIFT_BASKET', worst_buy['GIFT_BASKET'], -vol)) 
                self.cont_sell_basket_unfill += 2
                pb_neg -= vol
                #uku_pos += vol
        elif res_buy > trade_at:
            vol = self.POSITION_LIMIT['GIFT_BASKET'] - self.position['GIFT_BASKET']
            self.cont_sell_basket_unfill = 0 # no need to sell rn
            assert(vol >= 0)
            if vol > 0:
                do_bask = 1
                basket_buy_sig = 1
                gift_basket.append(Order('GIFT_BASKET', worst_sell['GIFT_BASKET'], vol))
                self.cont_buy_basket_unfill += 2
                pb_pos += vol

        if Symbol("ROSES") in state.market_trades and len(state.market_trades[Symbol("ROSES")]) > 0:
            trades = state.market_trades[Symbol("ROSES")]
            buy_orders = list(state.order_depths[Symbol("ROSES")].buy_orders.items())
            sell_orders = list(state.order_depths[Symbol("ROSES")].sell_orders.items())
            best_buy, best_buy_volume = buy_orders[0]
            best_sell, best_sell_volume = sell_orders[0]
            limit = self.POSITION_LIMIT["ROSES"]
            curr_pos = self.position["ROSES"]
            for trade in trades:
                if trade.seller == "Vinnie" and trade.timestamp == state.timestamp - 100:
                    roses.append(Order(Symbol("ROSES"), best_buy , max(-best_buy_volume, -limit - curr_pos)))
                elif trade.buyer == "Vinnie" and trade.timestamp == state.timestamp - 100:
                    roses.append(Order(Symbol("ROSES"), best_sell , min(-best_sell_volume, limit - curr_pos)))

        return gift_basket, chocolate, strawberries, roses

    def orders_mm_orchids(self, order_depth, ducks_price_sell, ducks_price_buy, import_tariff):
        ORCHIDS_POS_LIMIT = 100
        orders: list[Order] = []

        sell_orders = list(order_depth.sell_orders.items())
        buy_orders = list(order_depth.buy_orders.items())
        best_ask, best_ask_amount = sell_orders[0]
        best_bid, best_bid_amount = buy_orders[0]

        undercut_buy = best_bid + 1
        undercut_sell = best_ask - 1

        curr_pos = self.position["ORCHIDS"]
        overhead = 2
        if (import_tariff > -4):
            overhead = 1
        num_sell_bins = int(undercut_sell) - int(ducks_price_sell) - (overhead - 1)
        if num_sell_bins > 0:
            weights_bin = [0] * num_sell_bins
            weights_bin[0] = 1

            for i in range(1, num_sell_bins):
                weights_bin[i] = 0.3*weights_bin[i-1]

            ## normalise the weights:
            sum_weights = sum(weights_bin)
            volume_bins = [int((x/sum_weights)*(-ORCHIDS_POS_LIMIT - curr_pos)) for x in weights_bin]

            i = 0
            for price in range(int(ducks_price_sell) + overhead, int(undercut_sell) + 1):
                orders.append(Order("ORCHIDS", price, volume_bins[i]))
                i+=1
        
                curr_pos = self.position["ORCHIDS"]
        ## for orders with value, duck - 1, to undercut_buy
        num_buy_bins = int(ducks_price_buy) - int(undercut_buy)
        if num_buy_bins > 0:
            weights_bin = [0] * num_buy_bins
            weights_bin[0] = 1

            for i in range(1, num_buy_bins):
                weights_bin[i] = 0.3*weights_bin[i-1]

            ## normalise the weights:
            sum_weights = sum(weights_bin)
            volume_bins = [int((x/sum_weights)*(ORCHIDS_POS_LIMIT - curr_pos)) for x in weights_bin]

            # num_of_orders = undercut_buy - ducks_price_buy
            # vol_of_orders = int((100 + curr_pos)/num_of_orders)
            i = 0
            for price in range(int(ducks_price_buy) - 1, int(undercut_buy) ,-1):
                orders.append(Order("ORCHIDS", price, volume_bins[i]))
                i+=1

        return orders
    
    def black_scholes_price(self, S, T, r, sigma, K = 10000):
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        return S * statistics.NormalDist().cdf(d1) - K * np.exp(-r * T) * statistics.NormalDist().cdf(d2)
    
    def get_order_coupon(self, state: TradingState):
        order = []
        COUPON_POS_LIMIT = 600
        mid_price, best_bid, best_bid_volume, best_ask, best_ask_volume = {}, {}, {}, {}, {}
        for prod in ["COCONUT", "COCONUT_COUPON"]:
            buy_orders = list(state.order_depths[prod].buy_orders.items())
            sell_orders = list(state.order_depths[prod].sell_orders.items())
            best_bid[prod], best_bid_volume[prod] = buy_orders[0]
            best_ask[prod], best_ask_volume[prod] = sell_orders[0]
            mid_price[prod] = (best_bid[prod] + best_ask[prod]) / 2
        r = 0.01
        bs_price = self.black_scholes_price(mid_price["COCONUT"], 245/365, r, 0.191)
        logger.print("BS Price: ", bs_price, "Mid Price: ", mid_price["COCONUT_COUPON"])
        diff = mid_price["COCONUT_COUPON"] - bs_price
        curr_pos  = self.position["COCONUT_COUPON"]
        thres = 1
        if diff > thres:
            vol = max(-best_bid_volume["COCONUT_COUPON"], -COUPON_POS_LIMIT - curr_pos)
            order.append(Order("COCONUT_COUPON", best_bid["COCONUT_COUPON"], vol))
        if diff < -thres:
            vol = min(-best_ask_volume["COCONUT_COUPON"], COUPON_POS_LIMIT - curr_pos)
            order.append(Order("COCONUT_COUPON", best_ask["COCONUT_COUPON"], vol))

        return order
    
    def co_coconut(self, state):
        orders = []
        if Symbol("COCONUT") in state.market_trades and len(state.market_trades[Symbol("COCONUT")]) > 0:
            trades = state.market_trades[Symbol("COCONUT")]
            buy_orders = list(state.order_depths[Symbol("COCONUT")].buy_orders.items())
            sell_orders = list(state.order_depths[Symbol("COCONUT")].sell_orders.items())
            best_buy, best_buy_volume = buy_orders[0]
            best_sell, best_sell_volume = sell_orders[0]
            limit = self.POSITION_LIMIT["COCONUT"]
            curr_pos = self.position["COCONUT"]
            for trade in trades:
                if trade.seller == "Raj" and trade.timestamp == state.timestamp - 100:
                    orders.append(Order(Symbol("COCONUT"), best_buy , max(-best_buy_volume, -limit - curr_pos)))
                elif trade.buyer == "Raj" and trade.timestamp == state.timestamp - 100:
                    orders.append(Order(Symbol("COCONUT"), best_sell , min(-best_sell_volume, limit - curr_pos)))

        return orders

    def run(self, state: TradingState):
        result = {'AMETHYSTS': [], 'STARFRUIT': [], 'ORCHIDS': [], 'GIFT_BASKET': [], 'CHOCOLATE': [], 'STRAWBERRIES': [], 'ROSES': [], 'COCONUT': [], 'COCONUT_COUPON': []}
        
        traderData = ""
        conversions = 0

        for key, val in state.position.items():
            self.position[key] = val

        if len(self.starfruit_cache) == self.starfruit_dim:
            self.starfruit_cache.pop(0)

        best_bid_sf, best_bid_amount_sf = list(state.order_depths["STARFRUIT"].buy_orders.items())[0]
        best_ask_sf, best_ask_amount_sf = list(state.order_depths["STARFRUIT"].sell_orders.items())[0]

        self.starfruit_cache.append((best_bid_sf + best_ask_sf)/2)

        INF = 1e9
        starfruit_lb = 1
        starfruit_ub = 10000

        if len(self.starfruit_cache) == self.starfruit_dim:
            next_price = self.calc_next_price_starfruit()
            starfruit_lb = next_price-1
            starfruit_ub = next_price+1
            traderData = f"Next price: {next_price}"
        
        result["STARFRUIT"] += self.compute_orders_sf(state.order_depths["STARFRUIT"], starfruit_lb, starfruit_ub)

        amethysts_lb = 10000
        amethysts_ub = 10000

        result["AMETHYSTS"] += self.compute_orders_amethysts(state.order_depths["AMETHYSTS"], amethysts_lb, amethysts_ub)

        result["GIFT_BASKET"], result["CHOCOLATE"], result["STRAWBERRIES"], result["ROSES"] = self.get_orders_basket(state)

        self.timestamp_curr = state.timestamp
        order_depth = state.order_depths[Symbol("ORCHIDS")]
        buy_orders = list(order_depth.buy_orders.items())
        sell_orders = list(order_depth.sell_orders.items())
        best_ask, best_ask_amount = sell_orders[0]
        best_bid, best_bid_amount = buy_orders[0]
        undercut_buy = best_bid + 1
        undercut_sell = best_ask - 1
        ducks_price_selling = state.observations.conversionObservations["ORCHIDS"].askPrice + state.observations.conversionObservations["ORCHIDS"].importTariff + state.observations.conversionObservations["ORCHIDS"].transportFees
        ducks_price_buying = state.observations.conversionObservations["ORCHIDS"].bidPrice - state.observations.conversionObservations["ORCHIDS"].exportTariff - state.observations.conversionObservations["ORCHIDS"].transportFees 
        import_tariff = state.observations.conversionObservations["ORCHIDS"].importTariff
        result["ORCHIDS"] += self.orders_mm_orchids(state.order_depths["ORCHIDS"], ducks_price_selling, ducks_price_buying, import_tariff)
        curr_pos = self.position["ORCHIDS"]
        if undercut_sell > state.observations.conversionObservations["ORCHIDS"].askPrice + state.observations.conversionObservations["ORCHIDS"].importTariff + state.observations.conversionObservations["ORCHIDS"].transportFees and curr_pos < 0:
            # orders.append(Order("ORCHIDS", best_ask, -best_ask_amount))
            conversions = -curr_pos  
        curr_pos = self.position["ORCHIDS"]
        if undercut_buy < state.observations.conversionObservations["ORCHIDS"].bidPrice - state.observations.conversionObservations["ORCHIDS"].exportTariff - state.observations.conversionObservations["ORCHIDS"].transportFees and curr_pos > 0:
            # orders.append(Order("ORCHIDS", best_bid, -best_bid_amount))
            conversions = -curr_pos
        
        result["COCONUT_COUPON"] += self.get_order_coupon(state)
        
        result["COCONUT"] += self.co_coconut(state)

        logger.flush(state, result, conversions, traderData)
        return result, conversions, traderData