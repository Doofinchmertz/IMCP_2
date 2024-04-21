from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import Any
import string
import json

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
    
    position = {"AMETHYSTS": 0, "STARFRUIT": 0, "ORCHIDS": 0, "GIFT_BASKET": 0, "CHOCOLATE": 0, "ROSES": 0, "STRAWBERRIES": 0}
    pos_limits = {'AMETHYSTS': 20, 'STARFRUIT': 20, 'ORCHIDS': 100, 'GIFT_BASKET': 60, 'CHOCOLATE': 250, 'ROSES': 60, 'STRAWBERRIES': 350}
    EMA_THRESHOLD = 0.0005
    FAST_PERIOD = 9
    SLOW_PERIOD = 26


    def calc_next_price_starfruit(self):
        coeff = [0.18895127, 0.20771801, 0.26114406, 0.34171985]
        intercept = 2.3552758852292754
        nxt_price = intercept
        for i, val in enumerate(self.starfruit_cache):
            nxt_price += val * coeff[i]
        return int(round(nxt_price))

    def find_emas(self, state, traderData):
        for product in traderData.keys():
            buy_orders = list(state.order_depths[product].buy_orders.items())
            sell_orders = list(state.order_depths[product].sell_orders.items())
            best_bid, best_bid_volume = buy_orders[0]
            best_ask, best_ask_volume = sell_orders[0]
            mid_price = (best_bid + best_ask) / 2
            prev_fast_ema = traderData[product]['fast_ema']
            alpha_fast = 2/(1 + self.FAST_PERIOD)
            new_fast_ema = alpha_fast*mid_price + (1 - alpha_fast)*prev_fast_ema
            traderData[product]['fast_ema'] = new_fast_ema
            prev_slow_ema = traderData[product]['slow_ema']
            alpha_slow = 2/(1 + self.SLOW_PERIOD)
            new_slow_ema = alpha_slow*mid_price + (1 - alpha_slow)*prev_slow_ema
            traderData[product]['slow_ema'] = new_slow_ema
        return traderData

    def get_momentum_orders(self, state, product, traderData):
        orders = []
        buy_orders = list(state.order_depths[product].buy_orders.items())
        sell_orders = list(state.order_depths[product].sell_orders.items())
        best_bid, best_bid_volume = buy_orders[0]
        best_ask, best_ask_volume = sell_orders[0]
        mid_price = (best_bid + best_ask) / 2
        if traderData[product]['fast_ema'] - traderData[product]['slow_ema'] > self.EMA_THRESHOLD * mid_price:
            if self.position[product] < self.pos_limits[product]:
                orders.append(Order(product, best_ask, min(-best_ask_volume, self.pos_limits[product] - self.position[product])))
        elif traderData[product]['fast_ema'] - traderData[product]['slow_ema'] < -self.EMA_THRESHOLD * mid_price:
            if self.position[product] > -self.pos_limits[product]:
                orders.append(Order(product, best_bid, max(-best_bid_volume, -self.pos_limits[product] - self.position[product])))
        return orders

    def run(self, state: TradingState):
        result = {'GIFT_BASKET': [], 'CHOCOLATE': [], 'ROSES': [], 'STRAWBERRIES': []}
        if state.traderData == "":
            traderData = {'GIFT_BASKET': {'fast_ema': 0, 'slow_ema': 0}, 'CHOCOLATE': {'fast_ema': 0, 'slow_ema': 0}, 'ROSES': {'fast_ema': 0, 'slow_ema': 0}, 'STRAWBERRIES': {'fast_ema': 0, 'slow_ema': 0}}
        else:
            traderData = json.loads(state.traderData)
        conversions = 0

        for key, val in state.position.items():
            self.position[key] = val

        traderData = self.find_emas(state, traderData)

        for product in result.keys():
            result[product] = self.get_momentum_orders(state, product, traderData)

        traderData = json.dumps(traderData)
        logger.flush(state, result, conversions, traderData)
        return result, conversions, traderData