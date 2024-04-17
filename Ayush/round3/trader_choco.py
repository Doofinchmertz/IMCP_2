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
    
    z_score_chocolate = 0
    zs_choco_dim = 3
    is_choco_trade = False
    
    trade_std = 100
    trade_max_choco = 1e9
    trade_min_choco = 0


    def compute_orders_chocolate(self, order_depth, diff):

        CHOCO_POSITION_LIMIT = self.POSITION_LIMIT['CHOCOLATE'] 
        orders: list[Order] = []

        sell_orders = list(order_depth.sell_orders.items())
        buy_orders = list(order_depth.buy_orders.items())   
        best_ask, best_ask_amount = sell_orders[0]
        best_bid, best_bid_amount = buy_orders[0]

        undercut_buy = best_bid + 1
        overcut_sell = best_ask - 1

        curr_pos = self.position['CHOCOLATE']

        # Entrry point based on z-score of choco
        # Z-score coming down is an indicator that the trend is reversing
        # Z-score hitting 2 means that bohot trend lag chuka hai already
        # In reverse trending the score might drop, diff will confirm if its due to mean correction or what
        if self.z_score_chocolate[0] > 2 and self.z_score_chocolate[1] > 2 and self.z_score_chocolate[2] < 2:
            
            ## Checking for redundancy with diff
            if diff < -self.trade:
                
            ## Entering a position for chocolate (shorting)
                if self.is_choco_trade == False:

                    self.is_choco_trade = True
                    curr_pos = self.position['CHOCOLATE'] 
                    vol = -self.POSITION_LIMIT['CHOCOLATE'] - curr_pos
                    orders.append(Order(symbol="CHOCOLATE", price=best_bid, quantity = vol))
                    self.trade_price_choco = best_bid
                    self.trade_price_max = best_bid
                    self.trade_price_min = best_bid

                if self.is_choco_trade == True:
                    vol = -self.POSITION_LIMIT['CHOCOLATE'] - curr_pos
                    orders.append(Order(symbol="CHOCOLATE", price=best_bid, quantity = vol))
                    self.trade_price_choco = best_bid
                    self.trade_price_max = best_bid
                    self.trade_price_min = best_bid

        if self.z_score_chocolate[0] < -2 and self.z_score_chocolate[1] < -2 and self.z_score_chocolate[2] > -2:
                
            ## Checking for redundancy with diff
            if diff > self.trade:
                
            ## Entering a position for chocolate (longing)
                if self.is_choco_trade == False:

                    self.is_choco_trade = True
                    curr_pos = self.position['CHOCOLATE'] 
                    vol = self.POSITION_LIMIT['CHOCOLATE'] - curr_pos
                    orders.append(Order(symbol="CHOCOLATE", price=best_ask, quantity = vol))
                    self.trade_price_choco = best_ask
                    self.trade_price_max = best_ask
                    self.trade_price_min = best_ask

                if self.is_choco_trade == True:
                    vol = self.POSITION_LIMIT['CHOCOLATE'] - curr_pos
                    orders.append(Order(symbol="CHOCOLATE", price=best_ask, quantity = vol))
                    self.trade_price_choco = best_ask
                    self.trade_price_max = best_ask
                    self.trade_price_min = best_ask

        ## WRITING EXIT LOGIC

        if self.is_choco_trade == True:
            ## Checking for long or short
            if self.position['CHOCOLATE'] > 0:

                self.choco_trade_max = max(self.trade_price_max, best_bid)
                self.choco_trade_min = min(self.trade_price_min, best_bid)
                
                if best_bid - self.trade_price_choco > 0 and self.choco_trade_max - best_bid > 10:
                    orders.append(Order(symbol="CHOCOLATE", price=best_bid, quantity = -self.position['CHOCOLATE']))
                    self.is_choco_trade = False


                if best_bid > self.trade_price_choco + self.trade_std:
                    orders.append(Order(symbol="CHOCOLATE", price=best_bid, quantity = -self.position['CHOCOLATE']))
                    self.is_choco_trade = False

        return orders

    def run(self, state: TradingState):
        result = {'AMETHYSTS': [], 'STARFRUIT': [], 'ORCHIDS': [], 'GIFT_BASKET': [], 'CHOCOLATE': [], 'STRAWBERRIES': [], 'ROSES': []}
        # result = {'ORCHIDS': []}

        traderData = ""
        conversions = 0

        for key, val in state.position.items():
            self.position[key] = val

        order_depth_gb = state.order_depths[Symbol("GIFT_BASKET")]
        buy_orders_gb = list(order_depth_gb.buy_orders.items())
        sell_orders_gb = list(order_depth_gb.sell_orders.items())

        # result["GIFT_BASKET"] += self.orders_mm_orchids(order_depth, ducks_price_selling, ducks_price_buying)
        result["GIFT_BASKET"] += self.orders_mm_gb(order_depth_gb)

        logger.flush(state, result, conversions, traderData)
        return result, conversions, traderData
    