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

empty_dict = {"AMETHYSTS": 0, "STARFRUIT": 0, "ORCHIDS": 0, "GIFT_BASKET": 0, "CHOCOLATE": 0, "STRAWBERRIES":0, "ROSES": 0, "COCONUT": 0, "COCONUT_COUPON": 0}


def def_value():
    return copy.deepcopy(empty_dict)

INF = int(1e9)

class Trader:

    position = copy.deepcopy(empty_dict)
    POSITION_LIMIT = {"AMETHYSTS": 20, "STARFRUIT": 20, "ORCHIDS": 100, "GIFT_BASKET": 60, "CHOCOLATE": 250, "STRAWBERRIES": 350, "ROSES": 60, "COCONUT": 300, "COCONUT_COUPON": 600}
    volume_traded = copy.deepcopy(empty_dict)
    timestamp_curr = 0

    person_position = defaultdict(def_value)
    person_actvalof_position = defaultdict(def_value)

    cpnl = defaultdict(lambda : 0)
    
    volatility = 0.16276186774619497
    std = 25
    basket_std = 76
    
    def black_scholes_price(self, K, T, r, sigma, S = 10000):
        
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        option_price = S * statistics.NormalDist().cdf(d1) - K * math.exp(-r * T) * statistics.NormalDist().cdf(d2)
        return option_price
    
    def co_coco_coupon(self, order_depth):

        orders = {'COCONUT' : [], 'COCONUT_COUPON': []}
        prods = ['COCONUT', 'COCONUT_COUPON']
        osell, obuy, best_sell, best_buy, worst_sell, worst_buy, mid_price = {}, {}, {}, {}, {}, {}, {}

        for p in prods:
            osell[p] = collections.OrderedDict(sorted(order_depth[p].sell_orders.items()))
            obuy[p] = collections.OrderedDict(sorted(order_depth[p].buy_orders.items(), reverse=True))

            best_sell[p] = next(iter(osell[p]))
            best_buy[p] = next(iter(obuy[p]))

            worst_sell[p] = next(reversed(osell[p]))
            worst_buy[p] = next(reversed(obuy[p]))

            mid_price[p] = (best_sell[p] + best_buy[p]) / 2
            
        # Calculating the bs price
        bs_price = self.black_scholes_price(mid_price['COCONUT'], 1, 0.0, self.volatility, 10000)
        logger.print(f"bs_price: {bs_price}, mid_price: {mid_price['COCONUT_COUPON']}, diff: {bs_price - mid_price['COCONUT_COUPON']}")
        diff = mid_price['COCONUT_COUPON'] - bs_price

        curr_pos = self.position['COCONUT_COUPON']

        if diff < -65:
            vol = min(100, self.POSITION_LIMIT['COCONUT_COUPON'] - curr_pos)
            orders['COCONUT_COUPON'].append(Order('COCONUT_COUPON', best_sell['COCONUT_COUPON'], vol))

        if diff > 45:
            orders['COCONUT_COUPON'].append(Order('COCONUT_COUPON', best_buy['COCONUT_COUPON'], -self.POSITION_LIMIT['COCONUT_COUPON'] - curr_pos))

        return orders

    def co_coconut(self, order_depth):

        orders = {'COCONUT' : [], 'COCONUT_COUPON': []}
        prods = ['COCONUT', 'COCONUT_COUPON']
        osell, obuy, best_sell, best_buy, worst_sell, worst_buy, mid_price = {}, {}, {}, {}, {}, {}, {}

        for p in prods:
            osell[p] = collections.OrderedDict(sorted(order_depth[p].sell_orders.items()))
            obuy[p] = collections.OrderedDict(sorted(order_depth[p].buy_orders.items(), reverse=True))

            best_sell[p] = next(iter(osell[p]))
            best_buy[p] = next(iter(obuy[p]))

            worst_sell[p] = next(reversed(osell[p]))
            worst_buy[p] = next(reversed(obuy[p]))

            mid_price[p] = (best_sell[p] + best_buy[p]) / 2
            
        # theo_price = 10000 + np.sin(2 * np.pi * self.timestamp_curr / 4000000 + 2 * np.pi * 0.75) * 130
        theo_price = 10000 + np.sin(2 * np.pi * self.timestamp_curr / 3400000 - np.pi * 0.1 + 2*np.pi * (3000000/3400000)) * 120
        curr_pos = self.position['COCONUT']
        if theo_price - mid_price['COCONUT'] > 50:
            vol = min(100, self.POSITION_LIMIT['COCONUT'] - curr_pos)
            orders['COCONUT'].append(Order('COCONUT', best_sell['COCONUT'], vol))

        if theo_price - mid_price['COCONUT'] < -50:
            vol = max(-100, -self.POSITION_LIMIT['COCONUT'] - curr_pos)
            orders['COCONUT'].append(Order('COCONUT', best_buy['COCONUT'], vol))

        return orders

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        # Initialize the method output dict as an empty dict
        # result = {'PEARLS' : [], 'BANANAS' : [], 'COCONUTS' : [], 'PINA_COLADAS' : [], 'DIVING_GEAR' : [], 'BERRIES' : [], 'CHOCOLATE' : [], 'STRAWBERRIES' : [], 'ROSES' : [], 'GIFT_BASKET' : []}
        result = {'AMETHYSYTS': [], 'STARFRUIT': [], 'ORCHIDS': [], 'GIFT_BASKET': [], 'CHOCOLATE': [], 'STRAWBERRIES': [], 'ROSES': [], 'COCONUT' :[], 'COCONUT_COUPON': []}
        traderData = ""
        conversions = 1
        # Iterate over all the keys (the available products) contained in the order dephts
        for key, val in state.position.items():
            self.position[key] = val
        print()
        for key, val in self.position.items():
            print(f'{key} position: {val}')

        # assert abs(self.position.get('ROSES', 0)) <= self.POSITION_LIMIT['ROSES']

        self.timestamp_curr = state.timestamp

        # orders = self.co_coco_coupon(state.order_depths)
        # result['COCONUT_COUPON'] += orders['COCONUT_COUPON']

        orders = self.co_coconut(state.order_depths)
        result['COCONUT'] += orders['COCONUT']
        
        logger.flush(state, result, conversions, traderData)

        return result, conversions, traderData