from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import Any
import string
import json
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

class Trader:
    
    position = {"AMETHYSTS": 0, "STARFRUIT": 0, "ORCHIDS": 0, "GIFT_BASKET": 0, "CHOCOLATE": 0, "STRAWBERRIES":0, "ROSES": 0}
    POSITION_LIMIT = {"AMETHYSTS": 20, "STARFRUIT": 20, "ORCHIDS": 100, "GIFT_BASKET": 60, "CHOCOLATE": 250, "STRAWBERRIES": 350, "ROSES": 60}
    basket_std = 76
    cont_buy_basket_unfill = 0
    cont_sell_basket_unfill = 0
  
    def orders_mm_gb(self, order_depth):
        GB_POS_LIMIT = 60
        orders: list[Order] = []

        sell_orders = list(order_depth.sell_orders.items())
        buy_orders = list(order_depth.buy_orders.items())
        best_ask, best_ask_amount = sell_orders[0]
        best_bid, best_bid_amount = buy_orders[0]

        undercut_buy = best_bid + 1
        undercut_sell = best_ask - 1

        # bid_price = min(undercut_buy, acc_bid - 1)
        # ask_price = max(undercut_sell, acc_ask + 1)

        curr_pos = self.position["GIFT_BASKET"]

        if curr_pos < GB_POS_LIMIT:
            num = GB_POS_LIMIT - curr_pos
            num = num//5
            orders.append(Order("GIFT_BASKET", undercut_buy, num))
            orders.append(Order("GIFT_BASKET", undercut_buy + 1, num))
            orders.append(Order("GIFT_BASKET", undercut_buy + 2, num))
            orders.append(Order("GIFT_BASKET", undercut_buy + 3, num))
            orders.append(Order("GIFT_BASKET", undercut_buy + 4, num))

            curr_pos += num




        curr_pos = self.position["GIFT_BASKET"]

        if curr_pos > -GB_POS_LIMIT:
            num = -GB_POS_LIMIT - curr_pos
            num = num//5 + 1
            orders.append(Order("GIFT_BASKET", undercut_sell, num))
            orders.append(Order("GIFT_BASKET", undercut_sell - 1, num))
            orders.append(Order("GIFT_BASKET", undercut_sell - 2, num))
            orders.append(Order("GIFT_BASKET", undercut_sell - 3, num))
            orders.append(Order("GIFT_BASKET", undercut_sell - 4, num))

            curr_pos += num
        
        return orders
    
    def compute_orders_basket(self, order_depth, mid_price):

        orders = {'CHOCOLATE' : [], 'STRAWBERRIES': [], 'ROSES' : [], 'GIFT_BASKET' : []}
        prods = ['CHOCOLATE', 'STRAWBERRIES', 'ROSES', 'GIFT_BASKET']

        
        print("lengbth of mid_price", len(mid_price))
        print("type", type(mid_price))
        res_buy = mid_price[3] - mid_price[0]*4 - mid_price[1]*6 - mid_price[2] - 379
        res_sell = mid_price[3] - mid_price[0]*4 - mid_price[1]*6 - mid_price[2] - 379 

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
                orders['GIFT_BASKET'].append(Order('GIFT_BASKET', mid_price[3]-10, -vol)) 
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
                orders['GIFT_BASKET'].append(Order('GIFT_BASKET', mid_price[3]+10, vol))
                self.cont_buy_basket_unfill += 2
                pb_pos += vol

        return orders


    def run(self, state: TradingState):
        result = {'AMETHYSTS': [], 'STARFRUIT': [], 'ORCHIDS': [], 'GIFT_BASKET': [], 'CHOCOLATE': [], 'STRAWBERRIES': [], 'ROSES': []}
        # result = {'ORCHIDS': []}
        basket = ["CHOCOLATE", "STRAWBERRIES", "ROSES", "GIFT_BASKET"]
        mid = np.array([0, 0, 0, 0])

        traderData = ""
        conversions = 0

        for key, val in state.position.items():
            self.position[key] = val

        order_depth_gb = state.order_depths[Symbol("GIFT_BASKET")]
        buy_orders_gb = list(order_depth_gb.buy_orders.items())
        sell_orders_gb = list(order_depth_gb.sell_orders.items())

        i = 0
        ## calculate the mid_value for bsaket
        # for "ROSES" in basket:

        order_depth = state.order_depths[Symbol("CHOCOLATE")]
        buy_orders = list(order_depth.buy_orders.items())
        sell_orders = list(order_depth.sell_orders.items())
        best_bid, best_bid_amount = list(state.order_depths["CHOCOLATE"].buy_orders.items())[0]
        best_ask, best_ask_amount = list(state.order_depths["CHOCOLATE"].sell_orders.items())[0]
        mid[i] = (best_bid + best_ask)/2
        i += 1

        order_depth = state.order_depths[Symbol("STRAWBERRIES")]
        buy_orders = list(order_depth.buy_orders.items())
        sell_orders = list(order_depth.sell_orders.items())
        best_bid, best_bid_amount = list(state.order_depths["STRAWBERRIES"].buy_orders.items())[0]
        best_ask, best_ask_amount = list(state.order_depths["STRAWBERRIES"].sell_orders.items())[0]
        mid[i] = (best_bid + best_ask)/2
        i += 1

        order_depth = state.order_depths[Symbol("ROSES")]
        buy_orders = list(order_depth.buy_orders.items())
        sell_orders = list(order_depth.sell_orders.items())
        best_bid, best_bid_amount = list(state.order_depths["ROSES"].buy_orders.items())[0]
        best_ask, best_ask_amount = list(state.order_depths["ROSES"].sell_orders.items())[0]
        mid[i] = (best_bid + best_ask)/2
        i += 1

        order_depth = state.order_depths[Symbol("GIFT_BASKET")]
        buy_orders = list(order_depth.buy_orders.items())
        sell_orders = list(order_depth.sell_orders.items())
        best_bid, best_bid_amount = list(state.order_depths["GIFT_BASKET"].buy_orders.items())[0]
        best_ask, best_ask_amount = list(state.order_depths["GIFT_BASKET"].sell_orders.items())[0]
        mid[i] = (best_bid + best_ask)/2
        i += 1

        # result["GIFT_BASKET"] += self.orders_mm_orchids(order_depth, ducks_price_selling, ducks_price_buying)
        result["GIFT_BASKET"] += self.compute_orders_basket(order_depth_gb, mid)

        logger.flush(state, result, conversions, traderData)
        return result, conversions, traderData