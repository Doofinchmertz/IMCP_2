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
    
    def run(self, state: TradingState):
        # Only method required. It takes all buy and sell orders for all symbols as an input, and outputs a list of orders to be sent
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))
        result = {}
        traderData = ""
        POSITION_LIMIT = 20
        traderDataDict = {"prev_ema":0}
        prevDataDict = {"prev_ema":0}

        traderDataDict["ask_vwap_-1"] = 0
        traderDataDict["ask_vwap_-2"] = 0
        traderDataDict["ask_vwap_-3"] = 0
        prevDataDict["ask_vwap_-1"] = 0
        prevDataDict["ask_vwap_-2"] = 0
        prevDataDict["ask_vwap_-3"] = 0

        traderDataDict["bid_vwap_-1"] = 0
        traderDataDict["bid_vwap_-2"] = 0
        traderDataDict["bid_vwap_-1"] = 0
        prevDataDict["bid_vwap_-1"] = 0
        prevDataDict["bid_vwap_-2"] = 0
        prevDataDict["bid_vwap_-3"] = 0

        for product in state.order_depths:
            if product == "STARFRUIT":
                # coeff = [0.71039057, 0.1848555, 0.10453474, 1.1281731918970763]
                # coeff = [0.33784719, 0.26181147, 0.22293829, 0.17502343, 12.01585829020405]
                # coeff = [0.33922834, 0.26003937, 0.21324316, 0.18708019, 2.0601760119307073]
                # coeff = [0.29828608, 0.21728841, 0.16708144, 0.1040832, 0.11671686, 0.09471415, 9.239640558342217] 
                # coeff = [ 0.442155 , 0.12808201, -0.01124977, 0.29783109, 0.0825154, 0.06035712, 1.9887987381416679]
                coeff =  [ 0.44125852,  0.12375015,  -0.02300774,  0.0808372,   0.29703273,  0.08032768, 0.04989463, -0.05028714, 1.8456174269604162]
                curr_position = 0
                if(product in state.position):
                    curr_position = state.position[product]
                order_depth: OrderDepth = state.order_depths[product]
                orders: List[Order] = []
                best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]

                if (state.traderData != ""):
                    prevDataDict = json.loads(state.traderData)

                buy_orders = order_depth.buy_orders.items()
                sell_orders = order_depth.sell_orders.items()

                bid_vwap_0 = sum([float(price) * float(amount) for price, amount in buy_orders]) / sum([float(amount) for price, amount in buy_orders])
                bid_vwap_1 = prevDataDict["bid_vwap_-1"]
                bid_vwap_2 = prevDataDict["bid_vwap_-2"]
                bid_vwap_3 = prevDataDict["bid_vwap_-3"]

                ask_vwap_0 = sum([float(price) * float(amount) for price, amount in sell_orders]) / sum([float(amount) for price, amount in sell_orders])
                ask_vwap_1 = prevDataDict["ask_vwap_-1"]
                ask_vwap_2 = prevDataDict["ask_vwap_-2"]
                ask_vwap_3 = prevDataDict["ask_vwap_-3"]

                traderDataDict["bid_vwap_-1"] = bid_vwap_0
                traderDataDict["bid_vwap_-2"] = bid_vwap_1
                traderDataDict["bid_vwap_-3"] = bid_vwap_2
                traderDataDict["ask_vwap_-1"] = ask_vwap_0
                traderDataDict["ask_vwap_-2"] = ask_vwap_1
                traderDataDict["ask_vwap_-3"] = ask_vwap_2

                prev_ema = prevDataDict["prev_ema"]
                middle_price = (best_ask + best_bid) / 2
                alpha = 2 / (1 + 10)
                ema = alpha * middle_price + (1 - alpha) * prev_ema
                traderDataDict["prev_ema"] = ema

                traderData = json.dumps(traderDataDict)
                if state.timestamp < 400:
                    continue

                predicted_mid_price = coeff[0] * bid_vwap_0 + coeff[1] * bid_vwap_1 + coeff[2] * bid_vwap_2 + coeff[3] * bid_vwap_3 + coeff[4] * ask_vwap_0 + coeff[5] * ask_vwap_1 + coeff[6] * ask_vwap_2 + coeff[7] * ask_vwap_3 + coeff[8]
                
                lamda = 1
                acceptable_price = predicted_mid_price*lamda + ema*(1-lamda)

                if len(order_depth.sell_orders) != 0:
                    best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                    if int(best_ask) < acceptable_price:
                        buy_amount = POSITION_LIMIT - curr_position
                        # buy_amount = -best_ask_amount
                        orders.append(Order(product, best_ask, buy_amount))
                if len(order_depth.buy_orders) != 0:
                    best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                    if int(best_bid) > acceptable_price:
                        sell_amount = -POSITION_LIMIT - curr_position
                        # sell_amount = -best_bid_amount
                        orders.append(Order(product, best_bid, sell_amount))

                result[product] = orders
    
        # traderData = str((best_bid + best_ask)//2) # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.
        
        conversions = 1
        logger.flush(state, result, conversions, traderData)
        return result, conversions, traderData