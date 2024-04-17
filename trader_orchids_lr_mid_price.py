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
    
    position = {"AMETHYSTS": 0, "STARFRUIT": 0, "ORCHIDS": 0}
    starfruit_cache = []
    starfruit_dim = 4

    orchids_cache = []
    sunlights_cache = []
    humidity_cache = []
    orchids_dim = 3

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

        undercut_buy = best_bid + 1
        undercut_sell = best_ask - 1

        bid_price = min(undercut_buy, acc_bid)
        ask_price = max(undercut_sell, acc_ask)

        curr_pos = self.position["STARFRUIT"]

        for ask, vol in sell_orders:
            if ((ask <= acc_bid) or ((self.position["STARFRUIT"] < 0) and (ask == acc_bid + 1))) and curr_pos < STARFRUIT_POS_LIMIT: ## Try adding (self.position[product]<0) and (ask == acc_bid+1) to the condition
                order_for = min(-vol, STARFRUIT_POS_LIMIT - curr_pos)
                curr_pos += order_for
                assert(order_for >= 0)
                orders.append(Order("STARFRUIT", ask, order_for))

        if curr_pos < STARFRUIT_POS_LIMIT:
            num = STARFRUIT_POS_LIMIT - curr_pos
            orders.append(Order("STARFRUIT", bid_price, num))
            curr_pos += num


        curr_pos = self.position["STARFRUIT"]

        for bid, vol in buy_orders:
            if ((bid >= acc_ask) or ((self.position["STARFRUIT"] > 0) and (bid == acc_ask - 1))) and curr_pos > -STARFRUIT_POS_LIMIT: ## Try adding (self.position[product]>0) and (bid == acc_ask-1) to the condition
                order_for = max(-vol, -STARFRUIT_POS_LIMIT-curr_pos)
                curr_pos += order_for
                assert(order_for <= 0)
                orders.append(Order("STARFRUIT", bid, order_for))

        if curr_pos > -STARFRUIT_POS_LIMIT:
            num = -STARFRUIT_POS_LIMIT-curr_pos
            orders.append(Order("STARFRUIT", ask_price, num))
            curr_pos += num

        return orders

    def calc_next_price_orchids(self):
        coeff = [-3.01573128e+00,  6.05763426e+00, -3.04186888e+00, -1.47180306e+03, 2.93898496e+03, -1.46717968e+03,  1.20520562e-03,  1.38457398e-02, 9.82786093e-01]
        intercept = 2.3046044945308495
        nxt_price = intercept
        for i, val in enumerate(self.sunlights_cache):
            nxt_price += val * coeff[i]
        for i, val in enumerate(self.humidity_cache):
            nxt_price += val * coeff[i+3]
        for i, val in enumerate(self.orchids_cache):
            nxt_price += val * coeff[i+6]
        return int(round(nxt_price))

    def compute_orders_orchids(self, order_depth, acc_bid, acc_ask):
        ORCHIDS_POS_LIMIT = 100
        orders: list[Order] = []

        sell_orders = list(order_depth.sell_orders.items())
        buy_orders = list(order_depth.buy_orders.items())
        best_ask, best_ask_amount = sell_orders[0]
        best_bid, best_bid_amount = buy_orders[0]
    
        curr_pos = self.position["ORCHIDS"]
        num_sell_bins = int(best_ask) - int(acc_ask)
        if(num_sell_bins > 0):
            weights_bin = [0] * num_sell_bins
            weights_bin[0] = 1

            for i in range(1, num_sell_bins):
                weights_bin[i] = 0.4*weights_bin[i-1]

            ## normalise the weights:
            sum_weights = sum(weights_bin)
            volume_bins = [int((x/sum_weights)*(-ORCHIDS_POS_LIMIT - curr_pos)) for x in weights_bin]

            i = 0
            for price in range(int(acc_ask), int(best_ask)):
                orders.append(Order("ORCHIDS", price, volume_bins[i]))
                i += 1

        num_buy_bins = int(acc_bid) - int(best_bid)
        if(num_buy_bins > 0):
            weights_bin = [0] * num_buy_bins
            weights_bin[0] = 1

            for i in range(1, num_buy_bins):
                weights_bin[i] = 0.4*weights_bin[i-1]

            ## normalise the weights:
            sum_weights = sum(weights_bin)
            volume_bins = [int((x/sum_weights)*(ORCHIDS_POS_LIMIT - curr_pos)) for x in weights_bin]

            i = 0
            for price in range(int(acc_bid), int(best_bid), -1):
                orders.append(Order("ORCHIDS", price, volume_bins[i]))
                i += 1


        return orders
    
    def run(self, state: TradingState):
        result = {'AMETHYSTS': [], 'STARFRUIT': [], 'ORCHIDS': []}
        traderData = ""

        for key, val in state.position.items():
            self.position[key] = val

        if len(self.starfruit_cache) == self.starfruit_dim:
            self.starfruit_cache.pop(0)
        
        ## buy_orders.items() = list of tuples of bids in decreasing order
        ## sell_orders.items() = list of tuples of asks in increasing order

        # best_bid_sf, best_bid_amount_sf = list(state.order_depths["STARFRUIT"].buy_orders.items())[0]
        # best_ask_sf, best_ask_amount_sf = list(state.order_depths["STARFRUIT"].sell_orders.items())[0]

        # self.starfruit_cache.append((best_bid_sf + best_ask_sf)/2)

        # INF = 1e9
        # starfruit_lb = 1
        # starfruit_ub = 10000

        # if len(self.starfruit_cache) == self.starfruit_dim:
        #     starfruit_lb = self.calc_next_price_starfruit()-1
        #     starfruit_ub = self.calc_next_price_starfruit()+1

        # result["STARFRUIT"] += self.compute_orders_sf(state.order_depths["STARFRUIT"], starfruit_lb, starfruit_ub)

        best_bid_orchids, best_bid_amount_orchids = list(state.order_depths["ORCHIDS"].buy_orders.items())[0]
        best_ask_orchids, best_ask_amount_orchids = list(state.order_depths["ORCHIDS"].sell_orders.items())[0]

        observations = state.observations.conversionObservations["ORCHIDS"]
        self.sunlights_cache.append(observations.sunlight)
        self.humidity_cache.append(observations.humidity)
        self.orchids_cache.append((best_bid_orchids + best_ask_orchids)/2)
        orchids_lb = 1
        orchids_ub = 10000

        if len(self.orchids_cache) >= self.orchids_dim:
            self.orchids_cache.pop(0)
            self.sunlights_cache.pop(0)
            self.humidity_cache.pop(0)
            nxt_price = self.calc_next_price_orchids()
            orchids_lb = nxt_price-1
            orchids_ub = nxt_price+1
            result["ORCHIDS"] += self.compute_orders_orchids(state.order_depths["ORCHIDS"], orchids_lb, orchids_ub)

        conversions = 0
        logger.flush(state, result, conversions, traderData)
        return result, conversions, traderData