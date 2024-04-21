from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import Any
import string
import json
import numpy as np
import statistics
from math import log, sqrt, exp

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
    
    position = {'COCONUT': 0, 'COCONUT_COUPON': 0}

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
        r = 0
        bs_price = self.black_scholes_price(mid_price["COCONUT"], 246/365, r, 0.19)
        logger.print("BS Price: ", bs_price, "Mid Price: ", mid_price["COCONUT_COUPON"])
        diff = mid_price["COCONUT_COUPON"] - bs_price
        curr_pos  = self.position["COCONUT_COUPON"]
        thres = 2.5
        if diff > thres:
            vol = max(-best_bid_volume["COCONUT_COUPON"], -COUPON_POS_LIMIT - curr_pos)
            order.append(Order("COCONUT_COUPON", best_bid["COCONUT_COUPON"], vol))
        if diff < -thres:
            vol = min(-best_ask_volume["COCONUT_COUPON"], COUPON_POS_LIMIT - curr_pos)
            order.append(Order("COCONUT_COUPON", best_ask["COCONUT_COUPON"], vol))

        return order

    def run(self, state: TradingState):
        result = {'COCONUT': [], 'COCONUT_COUPON': []}
        traderData = ""
        conversions = 0

        for key, val in state.position.items():
            self.position[key] = val

        result["COCONUT_COUPON"] += self.get_order_coupon(state)

        logger.flush(state, result, conversions, traderData)
        return result, conversions, traderData