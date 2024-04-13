from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import Any
import string
import json
# import jsonpickle


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
    
    position = {"STARFRUIT": 0}
    starfruit_cache = []
    starfruit_dim = 3

    def compute_starfruit_macd(self, mid_price, f_period=1, s_period=119, signal_period=6):
        # print("hi")
        
        # Using history
        if len(self.starfruit_cache) < 3:
            self.starfruit_cache.extend([0] * (3 - len(self.starfruit_cache)))

        ema_fast = self.starfruit_cache[0]
        ema_slow = self.starfruit_cache[1]
        signal_line = self.starfruit_cache[2]

        ema_fast = ((f_period-1) / (f_period + 1)) * ema_fast + (2 / (f_period + 1)) * mid_price
        # Calculate the long-term exponential moving average (EMA)
        ema_slow = ((s_period-1) / (s_period + 1)) * ema_slow + (2 / (s_period + 1)) * mid_price
        # Calculate the MACD line
        macd_line = ema_fast - ema_slow
        # Calculate the signal line
        signal_line = ((signal_period-1) / (signal_period + 1)) * signal_line + (2 / (signal_period + 1)) * macd_line
        # Calculate the MACD histogram
        macd_hist = macd_line - signal_line

        # print("ema_fast: ", ema_fast)
        # print("ema_slow: ", ema_slow)
        # print("macd_line: ", macd_line)
        # print("signal_line: ", signal_line)
        # print("macd_hist: ", macd_hist)

        # Updating values to be stored
        self.starfruit_cache = [ema_fast, ema_slow, signal_line]

        return ema_fast, ema_slow, macd_line, signal_line, macd_hist

    def compute_orders_sf(self, order_depth, macd_hist):
        STARFRUIT_POS_LIMIT = 20
        # print("macd_hist: ", macd_hist)

        orders = []

        sell_orders = list(order_depth.sell_orders.items())
        buy_orders = list(order_depth.buy_orders.items())
        best_ask, best_ask_amount = sell_orders[0]
        best_bid, best_bid_amount = buy_orders[0]

        undercut_buy = best_bid + 1
        undercut_sell = best_ask - 1

        bid_price = undercut_buy
        ask_price = undercut_sell

        curr_pos = self.position["STARFRUIT"]

        ## if macd_hist < 0, buying
        # if -0.2 < macd_hist < 0.2:
            # print("macd_hist: ", macd_hist)
        
        if macd_hist < -0.01:
            # for ask, vol in buy_orders:
            #     if ((self.position["STARFRUIT"] < 0)) and curr_pos < STARFRUIT_POS_LIMIT:
            #         order_for = min(vol, STARFRUIT_POS_LIMIT - curr_pos)
            #         # curr_pos += order_for
            #         assert(order_for >= 0)
            #         orders.append(Order("STARFRUIT", ask, order_for))
            
            curr_pos = self.position["STARFRUIT"]
            if curr_pos < STARFRUIT_POS_LIMIT:
                # ask, vol = sell_orders[0]
                # print(curr_pos, STARFRUIT_POS_LIMIT, vol)
                num = min(STARFRUIT_POS_LIMIT - curr_pos, 51)
                print(num, "num")
                orders.append(Order("STARFRUIT", undercut_buy, num))
                curr_pos += num
                print("lele_bhenchod")

        curr_pos = self.position["STARFRUIT"]
        
        ## if macd_hist > 0, selling
        if macd_hist > 0.01:

            # for ask, vol in sell_orders:
                # if ((self.position["STARFRUIT"] > 0)) and curr_pos > -STARFRUIT_POS_LIMIT:
                #     order_for = min(vol, -STARFRUIT_POS_LIMIT - curr_pos)
                #     # curr_pos += order_for
                #     assert(order_for <= 0)
                #     orders.append(Order("STARFRUIT", ask, order_for))
            if curr_pos > -STARFRUIT_POS_LIMIT:
                bid, vol = buy_orders[0]
                num = max(-STARFRUIT_POS_LIMIT - curr_pos, -51)
                orders.append(Order("STARFRUIT", undercut_sell, num))
                curr_pos += num
                print("bech bhenchod")

        return orders


    def run(self, state):
        # print("hi from run_2")
        result = {'STARFRUIT': []}
        
        for key, val in state.position.items():
            self.position[key] = val

        # print("hi from run")

        best_bid_sf, best_bid_amount_sf = list(state.order_depths["STARFRUIT"].buy_orders.items())[0]
        best_ask_sf, best_ask_amount_sf = list(state.order_depths["STARFRUIT"].sell_orders.items())[0]

        if len(self.starfruit_cache) == 0:
            self.starfruit_cache.extend([best_ask_sf, best_ask_sf, 0])



        ema_fast, ema_slow, macd_line, signal_line, macd_hist = self.compute_starfruit_macd((best_bid_sf + best_ask_sf)/2)
        result["STARFRUIT"] += self.compute_orders_sf(state.order_depths["STARFRUIT"], macd_hist)
        traderData = "jsonpickle.encode(state)"  # assuming state is the data to remember

        conversions = 1
        logger.flush(state, result, conversions, traderData)
        return result, conversions, traderData