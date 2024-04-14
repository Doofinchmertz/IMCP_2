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
    # starfruit_cache = []
    # starfruit_dim = 4

    # def calc_next_price_starfruit(self):
    #     coeff = [0.18895127, 0.20771801, 0.26114406, 0.34171985]
    #     intercept = 2.3552758852292754
    #     nxt_price = intercept
    #     for i, val in enumerate(self.starfruit_cache):
    #         nxt_price += val * coeff[i]
    #     return int(round(nxt_price))

    # def compute_orders_sf(self, order_depth, acc_bid, acc_ask):
    #     STARFRUIT_POS_LIMIT = 20
    #     orders: list[Order] = []

    #     sell_orders = list(order_depth.sell_orders.items())
    #     buy_orders = list(order_depth.buy_orders.items())
    #     best_ask, best_ask_amount = sell_orders[0]
    #     best_bid, best_bid_amount = buy_orders[0]

    #     curr_pos = self.position["STARFRUIT"]

    #     for ask, vol in sell_orders:
    #         if ((ask <= acc_bid) or ((self.position["STARFRUIT"] < 0) and (ask == acc_bid + 1))) and curr_pos < STARFRUIT_POS_LIMIT: ## Try adding (self.position[product]<0) and (ask == acc_bid+1) to the condition
    #             order_for = min(-vol, STARFRUIT_POS_LIMIT - curr_pos)
    #             curr_pos += order_for
    #             assert(order_for >= 0)
    #             orders.append(Order("STARFRUIT", ask, order_for))

    #     if best_bid + 1 <= acc_bid:
    #         if curr_pos < STARFRUIT_POS_LIMIT:
    #             num = STARFRUIT_POS_LIMIT - curr_pos
    #             orders.append(Order("STARFRUIT", best_bid + 1, num))
    #             curr_pos += num


    #     curr_pos = self.position["STARFRUIT"]

    #     for bid, vol in buy_orders:
    #         if ((bid >= acc_ask) or ((self.position["STARFRUIT"] > 0) and (bid == acc_ask - 1))) and curr_pos > -STARFRUIT_POS_LIMIT: ## Try adding (self.position[product]>0) and (bid == acc_ask-1) to the condition
    #             order_for = max(-vol, -STARFRUIT_POS_LIMIT-curr_pos)
    #             curr_pos += order_for
    #             assert(order_for <= 0)
    #             orders.append(Order("STARFRUIT", bid, order_for))

    #     if best_ask - 1 >= acc_ask:
    #         if curr_pos > -STARFRUIT_POS_LIMIT:
    #             num = -STARFRUIT_POS_LIMIT-curr_pos
    #             orders.append(Order("STARFRUIT", best_ask - 1, num))
    #             curr_pos += num

    #     return orders

    def orders_mm_orchids(self, order_depth):
        ORCHIDS_POS_LIMIT = 100
        orders: list[Order] = []

        sell_orders = list(order_depth.sell_orders.items())
        buy_orders = list(order_depth.buy_orders.items())
        best_ask, best_ask_amount = sell_orders[0]
        best_bid, best_bid_amount = buy_orders[0]

        undercut_buy = best_bid + 1
        undercut_sell = best_ask - 1

        # bid_price = min(undercut_buy, acc_bid - 1)
        # ask_price = max(undercut_sell, acc_ask + 1)

        curr_pos = self.position["ORCHIDS"]

        for ask, vol in sell_orders:
            if ((ask <= undercut_buy)  and curr_pos < ORCHIDS_POS_LIMIT):
                order_for = min(-vol, ORCHIDS_POS_LIMIT - curr_pos)
                curr_pos += order_for
                assert(order_for >= 0)
                orders.append(Order("ORCHIDS", ask, order_for))
        
        if curr_pos < ORCHIDS_POS_LIMIT:
            num = ORCHIDS_POS_LIMIT - curr_pos
            orders.append(Order("ORCHIDS", undercut_buy, num))
            curr_pos += num
        
        curr_pos = self.position["ORCHIDS"]

        #
        for bid, vol in buy_orders:
            if ((bid > undercut_sell) and curr_pos > -ORCHIDS_POS_LIMIT):
                order_for = max(-vol, -ORCHIDS_POS_LIMIT-curr_pos)
                curr_pos += order_for
                assert(order_for <= 0)
                orders.append(Order("ORCHIDS", bid, order_for))

        #zabardasti last layer clear kardo
        amt = min(10, best_bid_amount)
        if curr_pos == 0:
            orders.append(Order("ORCHIDS", best_bid, -amt))
            curr_pos += -amt

        if curr_pos > -ORCHIDS_POS_LIMIT:
            num = -ORCHIDS_POS_LIMIT-curr_pos
            orders.append(Order("ORCHIDS", undercut_sell, num))
            curr_pos += num

        # amt = max(-10, best_bid_amount)
        # if curr_pos == 90:
        #     orders.append(Order("ORCHIDS", best_bid, amt))

        return orders


        ## Checking if we can put an order for mm by buying from other markets
        

    # def compute_orders_orchids(self, order_depth):
    #     orders: list[Order] = []

    #     buy_orders = list(order_depth.buy_orders.items())
    #     sell_orders = list(order_depth.sell_orders.items())
    #     best_ask, best_ask_amount = sell_orders[0]
    #     best_bid, best_bid_amount = buy_orders[0]

    #     orders.append(Order("ORCHIDS", best_bid, -best_bid_amount))

    #     return orders


    def run(self, state: TradingState):
        # result = {'AMETHYSTS': [], 'STARFRUIT': [], 'ORCHIDS': []}
        result = {'ORCHIDS': []}

        traderData = ""
        conversions = 0

        for key, val in state.position.items():
            self.position[key] = val

        order_depth = state.order_depths[Symbol("ORCHIDS")]
        buy_orders = list(order_depth.buy_orders.items())
        sell_orders = list(order_depth.sell_orders.items())

        # Best values of orchids
        best_ask, best_ask_amount = sell_orders[0]
        best_bid, best_bid_amount = buy_orders[0]

        undercut_buy = best_bid + 1
        undercut_sell = best_ask - 1


        # if state.timestamp < 500:
        #     # Buying shit out right now
        #     result['ORCHIDS'].append(Order("ORCHIDS", best_ask, -best_ask_amount))

        # Selling stuff and keeping
        # if state.timestamp < 500:
        #     result['ORCHIDS'].append(Order("ORCHIDS", best_bid, -best_bid_amount))
        
        # if state.timestamp > 0: 
        #     ## Thinning the market
        #     curr_pos = self.position[]

        # else:
        #     #Checking for arbitrage oppourtunities
        #     if best_ask < state.observations.conversionObservations["ORCHIDS"].bidPrice - state.observations.conversionObservations["ORCHIDS"].exportTariff - state.observations.conversionObservations["ORCHIDS"].transportFees:
        #         result['ORCHIDS'].append(Order("ORCHIDS", best_ask, -best_ask_amount))
        #         conversions = best_ask_amount

        result["ORCHIDS"] += self.orders_mm_orchids(order_depth)

        curr_pos = self.position["ORCHIDS"]

        if undercut_buy > state.observations.conversionObservations["ORCHIDS"].askPrice + state.observations.conversionObservations["ORCHIDS"].importTariff - state.observations.conversionObservations["ORCHIDS"].transportFees:
            # orders.append(Order("ORCHIDS", best_ask, -best_ask_amount))
            conversions = min(5, -curr_pos)
        
        curr_pos = self.position["ORCHIDS"]
        if undercut_sell < state.observations.conversionObservations["ORCHIDS"].bidPrice - state.observations.conversionObservations["ORCHIDS"].exportTariff - state.observations.conversionObservations["ORCHIDS"].transportFees -0.5:
            # orders.append(Order("ORCHIDS", best_bid, -best_bid_amount))
            conversions = max(-5, -curr_pos)
            
        logger.flush(state, result, conversions, traderData)
        return result, conversions, traderData