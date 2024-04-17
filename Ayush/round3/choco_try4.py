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
    
    position = {"AMETHYSTS": 0, "STARFRUIT": 0, "ORCHIDS": 0, "CHOCOLATE": 0, "STRAWBERRIES": 0, "ROSES": 0, "GIFT_BASKET": 0}
    spread_cache = []
    spread_cache_size = 200

    choco_cache = []
    choco_cache_size = 200

    strawberries_cache = []
    strawberries_cache_dim = 4

    def get_prices(self, state: TradingState, symbol: Symbol):
        buy_orders = list(state.order_depths[symbol].buy_orders.items())
        sell_orders = list(state.order_depths[symbol].sell_orders.items())
        best_bid, best_bid_volume = buy_orders[0]
        best_ask, best_ask_volume = sell_orders[0]
        return best_bid, best_ask, (best_bid + best_ask) / 2, best_bid_volume, best_ask_volume

    def get_next_strawberries_price(self):
        coeff = [-0.01891429,  0.03899502, 0.12832107,  0.85131869]
        intercept = 1.126909434863137
        nxt_price = intercept
        for i, val in enumerate(self.strawberries_cache):
            nxt_price += val * coeff[i]
        return int(round(nxt_price))
    
    def get_orders_strawberries(self, best_bid_strawberries, best_ask_strawberries, mid_price_strawberries, best_bid_volume_strawberries, best_ask_volume_strawberries):
        strawberries = []
        STRAWBERRIES_POS_LIMIT = 350
        if(len(self.strawberries_cache) == self.strawberries_cache_dim):
            self.strawberries_cache.pop(0)
        self.strawberries_cache.append(mid_price_strawberries)
        nxt_price = self.get_next_strawberries_price()
        
        curr_pos = self.position["STRAWBERRIES"]
        if (best_ask_strawberries < nxt_price):
            order_for = min(-best_ask_volume_strawberries, STRAWBERRIES_POS_LIMIT - curr_pos)
            curr_pos += order_for
            assert(order_for >= 0)
            strawberries.append(Order("STRAWBERRIES", best_ask_strawberries, order_for))

        if (best_bid_strawberries > nxt_price):
            order_for = max(-best_bid_volume_strawberries, -STRAWBERRIES_POS_LIMIT - curr_pos)
            curr_pos += order_for
            assert(order_for <= 0)
            strawberries.append(Order("STRAWBERRIES", best_bid_strawberries, order_for))

        return strawberries

    def orders_chocolate(self, state: TradingState):
        CHOCO_LIMIT = 250
        orders: list[Order] = []    
        best_bid_chocolate, best_ask_chocolate, mid_price_chocolate, best_bid_volume_chocolate, best_ask_volume_chocolate = self.get_prices(state, "CHOCOLATE")

        if len(self.choco_cache) == self.choco_cache_size:
            self.choco_cache.pop(0)
        self.choco_cache.append(mid_price_chocolate)

        avg_choco = np.mean(np.array(self.choco_cache))
        std_choco = np.std(np.array(self.choco_cache))

        curr_pos = self.position["CHOCOLATE"]

        if (len(self.choco_cache) > 3):
            choco_recent = np.mean(np.array(self.choco_cache[-3:]))
            if (choco_recent < avg_choco - 1.5*std_choco):
                print("hi_minus")
                vol = CHOCO_LIMIT - curr_pos
                orders.append(Order("CHOCOLATE", best_ask_chocolate, vol))
            elif (choco_recent > avg_choco + 1.5*std_choco):
                vol = -CHOCO_LIMIT - curr_pos
                print("hi_plus")
                orders.append(Order("CHOCOLATE", best_bid_chocolate, vol))
        
        return orders

    
    def run(self, state: TradingState):
        result = {'AMETHYSTS': [], 'STARFRUIT': [], 'ORCHIDS': [], 'CHOCOLATE': [], 'STRAWBERRIES': [], 'ROSES': [], 'GIFT_BASKET': []}
        traderData = ""
        conversions = 0

        for key, val in state.position.items():
            self.position[key] = val

        
        ## buy_orders.items() = list of tuples of bids in decreasing order
        ## sell_orders.items() = list of tuples of asks in increasing order

        result['CHOCOLATE'] += self.orders_chocolate(state)

        logger.flush(state, result, conversions, traderData)
        return result, conversions, traderData