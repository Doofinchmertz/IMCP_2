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

empty_dict = {"AMETHYSTS": 0, "STARFRUIT": 0, "ORCHIDS": 0, "GIFT_BASKET": 0, "CHOCOLATE": 0, "STRAWBERRIES":0, "ROSES": 0}


def def_value():
    return copy.deepcopy(empty_dict)

INF = int(1e9)

class Trader:

    position = copy.deepcopy(empty_dict)
    POSITION_LIMIT = {"AMETHYSTS": 20, "STARFRUIT": 20, "ORCHIDS": 100, "GIFT_BASKET": 60, "CHOCOLATE": 250, "STRAWBERRIES": 350, "ROSES": 60}
    volume_traded = copy.deepcopy(empty_dict)

    person_position = defaultdict(def_value)
    person_actvalof_position = defaultdict(def_value)

    cpnl = defaultdict(lambda : 0)
    bananas_cache = []
    coconuts_cache = []
    bananas_dim = 4
    coconuts_dim = 3
    steps = 0
    last_dolphins = -1
    buy_gear = False
    sell_gear = False
    buy_berries = False
    sell_berries = False
    close_berries = False
    last_dg_price = 0
    start_berries = 0
    first_berries = 0
    cont_buy_basket_unfill = 0
    cont_sell_basket_unfill = 0

    strawberries_cache = [0, 0, 0, 0]
    
    halflife_diff = 5
    alpha_diff = 1 - np.exp(-np.log(2)/halflife_diff)

    halflife_price = 5
    alpha_price = 1 - np.exp(-np.log(2)/halflife_price)

    halflife_price_dip = 20
    alpha_price_dip = 1 - np.exp(-np.log(2)/halflife_price_dip)
    
    begin_diff_dip = -INF
    begin_diff_bag = -INF
    begin_bag_price = -INF
    begin_dip_price = -INF

    std = 25
    basket_std = 76

    def get_next_strawberries_price(self):
        nxt_price = 0
        coeff = [0.16653176, -0.66600323, -0.16646411, -0.1668565]
        for i, val in enumerate(self.strawberries_cache):
            nxt_price += val * coeff[i]
        return nxt_price

    def compute_orders_basket(self, order_depth):

        orders = {'CHOCOLATE' : [], 'STRAWBERRIES': [], 'ROSES' : [], 'GIFT_BASKET' : []}
        prods = ['CHOCOLATE', 'STRAWBERRIES', 'ROSES', 'GIFT_BASKET']
        osell, obuy, best_sell, best_buy, worst_sell, worst_buy, mid_price, vol_buy, vol_sell = {}, {}, {}, {}, {}, {}, {}, {}, {}

        for p in prods:
            osell[p] = collections.OrderedDict(sorted(order_depth[p].sell_orders.items()))
            obuy[p] = collections.OrderedDict(sorted(order_depth[p].buy_orders.items(), reverse=True))

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

        res_buy = mid_price['GIFT_BASKET'] - mid_price['CHOCOLATE']*4 - mid_price['STRAWBERRIES']*6 - mid_price['ROSES'] - 375
        res_sell = mid_price['GIFT_BASKET'] - mid_price['CHOCOLATE']*4 - mid_price['STRAWBERRIES']*6 - mid_price['ROSES'] - 375

        trade_at = self.basket_std*0.5
        close_at = self.basket_std*(-1000)

        pb_pos = self.position['GIFT_BASKET']
        pb_neg = self.position['GIFT_BASKET']

        uku_pos = self.position['ROSES']
        uku_neg = self.position['ROSES']


        basket_buy_sig = 0
        basket_sell_sig = 0

        if self.position['GIFT_BASKET'] == self.POSITION_LIMIT['GIFT_BASKET']:
            self.cont_buy_basket_unfill = 0
        if self.position['GIFT_BASKET'] == -self.POSITION_LIMIT['GIFT_BASKET']:
            self.cont_sell_basket_unfill = 0

        do_bask = 0

        if res_sell > trade_at:
            vol = self.position['GIFT_BASKET'] + self.POSITION_LIMIT['GIFT_BASKET']
            self.cont_buy_basket_unfill = 0 # no need to buy rn
            assert(vol >= 0)
            if vol > 0:
                do_bask = 1
                basket_sell_sig = 1
                orders['GIFT_BASKET'].append(Order('GIFT_BASKET', worst_buy['GIFT_BASKET'], -vol)) 
                self.cont_sell_basket_unfill += 2
                pb_neg -= vol
                #uku_pos += vol
        elif res_buy < -trade_at:
            vol = self.POSITION_LIMIT['GIFT_BASKET'] - self.position['GIFT_BASKET']
            self.cont_sell_basket_unfill = 0 # no need to sell rn
            assert(vol >= 0)
            if vol > 0:
                do_bask = 1
                basket_buy_sig = 1
                orders['GIFT_BASKET'].append(Order('GIFT_BASKET', worst_sell['GIFT_BASKET'], vol))
                self.cont_buy_basket_unfill += 2
                pb_pos += vol

        ## checking chocolate and strawberries position
        choco_pos  = self.position['CHOCOLATE']
        straw_pos = self.position['STRAWBERRIES']
        
        # if self.position['GIFT_BASKET'] > 0:
            
        #     orders['CHOCOLATE'].append(Order('CHOCOLATE', best_sell['CHOCOLATE'], self.POSITION_LIMIT['CHOCOLATE'] - choco_pos))
        #     orders['STRAWBERRIES'].append(Order('STRAWBERRIES', best_sell['STRAWBERRIES'], self.POSITION_LIMIT['STRAWBERRIES'] - straw_pos))

        # if self.position['GIFT_BASKET'] < 0:
        #     orders['CHOCOLATE'].append(Order('CHOCOLATE', best_buy['CHOCOLATE'], -self.POSITION_LIMIT['CHOCOLATE'] - choco_pos))
        #     orders['STRAWBERRIES'].append(Order('STRAWBERRIES', best_buy['STRAWBERRIES'], -self.POSITION_LIMIT['STRAWBERRIES'] - straw_pos))

        # if int(round(self.person_position['Olivia']['ROSES'])) > 0:

        #     val_ord = self.POSITION_LIMIT['ROSES'] - uku_pos
        #     if val_ord > 0:
        #         orders['ROSES'].append(Order('ROSES', worst_sell['ROSES'], val_ord))
        # if int(round(self.person_position['Olivia']['ROSES'])) < 0:

        #     val_ord = -(self.POSITION_LIMIT['ROSES'] + uku_neg)
        #     if val_ord < 0:
        #         orders['ROSES'].append(Order('ROSES', worst_buy['ROSES'], val_ord))
        diff = mid_price['GIFT_BASKET'] - mid_price['CHOCOLATE']*4 - mid_price['STRAWBERRIES']*6 - mid_price['ROSES']

        self.strawberries_cache = [mid_price['GIFT_BASKET'], mid_price['CHOCOLATE'], mid_price['ROSES'], diff]
        straw_price = self.get_next_strawberries_price()
        logger.print(f"straw_price: {straw_price}, mid_price: {mid_price['STRAWBERRIES']}, diff: {straw_price - mid_price['STRAWBERRIES']}")

        if straw_price - mid_price['STRAWBERRIES'] > -1.36:
            orders['STRAWBERRIES'].append(Order('STRAWBERRIES', best_sell['STRAWBERRIES'], min(10, self.POSITION_LIMIT['STRAWBERRIES'] - straw_pos)))

        if straw_price - mid_price['STRAWBERRIES'] < -1.436:
            orders['STRAWBERRIES'].append(Order('STRAWBERRIES', best_buy['STRAWBERRIES'], max(-self.POSITION_LIMIT['STRAWBERRIES'] - straw_pos, 10)))

        return orders
    
    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        # Initialize the method output dict as an empty dict
        # result = {'PEARLS' : [], 'BANANAS' : [], 'COCONUTS' : [], 'PINA_COLADAS' : [], 'DIVING_GEAR' : [], 'BERRIES' : [], 'CHOCOLATE' : [], 'STRAWBERRIES' : [], 'ROSES' : [], 'GIFT_BASKET' : []}
        result = {'AMETHYSYTS': [], 'STARFRUIT': [], 'ORCHIDS': [], 'GIFT_BASKET': [], 'CHOCOLATE': [], 'STRAWBERRIES': [], 'ROSES': []}
        traderData = ""
        conversions = 1
        # Iterate over all the keys (the available products) contained in the order dephts
        for key, val in state.position.items():
            self.position[key] = val
        print()
        for key, val in self.position.items():
            print(f'{key} position: {val}')

        # assert abs(self.position.get('ROSES', 0)) <= self.POSITION_LIMIT['ROSES']

        timestamp = state.timestamp

        

        # for product in state.market_trades.keys():
        #     for trade in state.market_trades[product]:
        #         if trade.buyer == trade.seller:
        #             continue
        #         self.person_position[trade.buyer][product] = 1.5
        #         self.person_position[trade.seller][product] = -1.5
        #         self.person_actvalof_position[trade.buyer][product] += trade.quantity
        #         self.person_actvalof_position[trade.seller][product] += -trade.quantity

        

        orders = self.compute_orders_basket(state.order_depths)
        result['GIFT_BASKET'] += orders['GIFT_BASKET']
        result['CHOCOLATE'] += orders['CHOCOLATE']
        result['STRAWBERRIES'] += orders['STRAWBERRIES']
        # print(orders)
        # result['CHOCOLATE'] += orders['CHOCOLATE']
        # result['STRAWBERRIES'] += orders['STRAWBERRIES']
       
        # result['ROSES'] += orders['ROSES']
        logger.flush(state, result, conversions, traderData)

        return result, conversions, traderData