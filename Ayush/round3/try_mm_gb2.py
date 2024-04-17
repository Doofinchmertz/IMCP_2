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
    
    position = {"AMETHYSTS": 0, "STARFRUIT": 0, "ORCHIDS": 0, "GIFT_BASKET": 0, "CHOCOLATE": 0, "STRAWBERRIES":0, "ROSES": 0}
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

    # def compute_orders_amethysts(self, order_depth, acc_bid, acc_ask):
    #     AMETHYSTS_POS_LIMIT = 20
    #     orders: list[Order] = []

    #     sell_orders = list(order_depth.sell_orders.items())
    #     buy_orders = list(order_depth.buy_orders.items())
    #     best_ask, best_ask_amount = sell_orders[0]
    #     best_bid, best_bid_amount = buy_orders[0]

    #     undercut_buy = best_bid + 1
    #     undercut_sell = best_ask - 1

    #     bid_price = min(undercut_buy, acc_bid - 1)
    #     ask_price = max(undercut_sell, acc_ask + 1)

    #     curr_pos = self.position["AMETHYSTS"]

    #     for ask, vol in sell_orders:
    #         if ((ask < acc_bid) or ((self.position["AMETHYSTS"] < 0) and (ask == acc_bid))) and curr_pos < AMETHYSTS_POS_LIMIT:
    #             order_for = min(-vol, AMETHYSTS_POS_LIMIT - curr_pos)
    #             curr_pos += order_for
    #             assert(order_for >= 0)
    #             orders.append(Order("AMETHYSTS", ask, order_for))
        
    #     if curr_pos < AMETHYSTS_POS_LIMIT:
    #         num = AMETHYSTS_POS_LIMIT - curr_pos
    #         orders.append(Order("AMETHYSTS", bid_price, num))
    #         curr_pos += num
        
    #     curr_pos = self.position["AMETHYSTS"]

    #     for bid, vol in buy_orders:
    #         if ((bid > acc_ask) or ((self.position["AMETHYSTS"] > 0) and (bid == acc_ask))) and curr_pos > -AMETHYSTS_POS_LIMIT:
    #             order_for = max(-vol, -AMETHYSTS_POS_LIMIT-curr_pos)
    #             curr_pos += order_for
    #             assert(order_for <= 0)
    #             orders.append(Order("AMETHYSTS", bid, order_for))

    #     if curr_pos > -AMETHYSTS_POS_LIMIT:
    #         num = -AMETHYSTS_POS_LIMIT-curr_pos
    #         orders.append(Order("AMETHYSTS", ask_price, num))
    #         curr_pos += num

    #     return orders

    # def orders_mm_orchids(self, order_depth, ducks_price_sell, ducks_price_buy):
    #     ORCHIDS_POS_LIMIT = 100
    #     orders: list[Order] = []

    #     sell_orders = list(order_depth.sell_orders.items())
    #     buy_orders = list(order_depth.buy_orders.items())
    #     best_ask, best_ask_amount = sell_orders[0]
    #     best_bid, best_bid_amount = buy_orders[0]

    #     undercut_buy = best_bid + 1
    #     undercut_sell = best_ask - 1

    #     # bid_price = min(undercut_buy, acc_bid - 1)
    #     # ask_price = max(undercut_sell, acc_ask + 1)

    #     curr_pos = self.position["ORCHIDS"]

    #     ## for orders with value, duck + 2, to undercut_sell
    #     num_sell_bins = int(undercut_sell) - int(ducks_price_sell) - 1
    #     if num_sell_bins > 0:
    #         weights_bin = [0] * num_sell_bins
    #         weights_bin[0] = 1

    #         for i in range(1, num_sell_bins):
    #             weights_bin[i] = 0.3*weights_bin[i-1]

    #         ## normalise the weights:
    #         sum_weights = sum(weights_bin)
    #         volume_bins = [int((x/sum_weights)*(-ORCHIDS_POS_LIMIT - curr_pos)) for x in weights_bin]

    #         # num_of_orders = undercut_sell - ducks_price_sell - 1
    #         # vol_of_orders = int((100 - curr_pos)/num_of_orders)
    #         i = 0
    #         for price in range(int(ducks_price_sell) + 2, int(undercut_sell) + 1):
    #             orders.append(Order("ORCHIDS", price, volume_bins[i]))
    #             i+=1
    #         #appending 10 values for a lower timestamp
    #         # orders.append(Order("ORCHIDS", int(ducks_price_sell) + 1, -10))
            
    #     curr_pos = self.position["ORCHIDS"]

    #     if undercut_buy < ducks_price_sell:
    #         vol_bin = int(100 / (ducks_price_sell - undercut_buy))
    #         for price in range(int(undercut_buy), int(ducks_price_sell)+1):
    #             orders.append(Order("ORCHIDS", price, vol_bin))


    #     ## for orders with value, duck - 1, to undercut_buy
    #     num_buy_bins = int(ducks_price_buy) - int(undercut_buy)
    #     if num_buy_bins > 0:
    #         weights_bin = [0] * num_buy_bins
    #         weights_bin[0] = 1

    #         for i in range(1, num_buy_bins):
    #             weights_bin[i] = 0.4*weights_bin[i-1]

    #         ## normalise the weights:
    #         sum_weights = sum(weights_bin)
    #         volume_bins = [int((x/sum_weights)*(ORCHIDS_POS_LIMIT - curr_pos)) for x in weights_bin]

    #         # num_of_orders = undercut_buy - ducks_price_buy
    #         # vol_of_orders = int((100 + curr_pos)/num_of_orders)
    #         i = 0
    #         for price in range(int(ducks_price_buy) - 1, int(undercut_buy) ,-1):
    #             orders.append(Order("ORCHIDS", price, volume_bins[i]))
    #             i+=1


    #     return orders


    #     ## Checking if we can put an order for mm by buying from other markets
        
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
    
    def compute_orders_basket(self, order_depth, state: TradingState):

        orders = {'CHOCOLATE' : [], 'STRAWBERRIES': [], 'ROSES' : [], 'GIFT_BASKET' : []}
        prods = ['CHOCOLATE', 'STRAWBERRIES', 'ROSES', 'GIFT_BASKET']

        osell, obuy, best_sell, best_buy, worst_sell, worst_buy, mid_price, vol_buy, vol_sell = {}, {}, {}, {}, {}, {}, {}, {}, {}

        for p in prods:

            order_depth[p] = state.order_depths[Symbol(p)]
            osell[p] = order_depth[p].sell_orders.items()
            obuy[p] = order_depth[p].buy_orders.items()

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

        res_buy = mid_price['PICNIC_BASKET'] - mid_price['DIP']*4 - mid_price['BAGUETTE']*2 - mid_price['UKULELE'] - 375
        res_sell = mid_price['PICNIC_BASKET'] - mid_price['DIP']*4 - mid_price['BAGUETTE']*2 - mid_price['UKULELE'] - 375

        trade_at = self.basket_std*0.5
        close_at = self.basket_std*(-1000)

        pb_pos = self.position['PICNIC_BASKET']
        pb_neg = self.position['PICNIC_BASKET']

        uku_pos = self.position['UKULELE']
        uku_neg = self.position['UKULELE']


        basket_buy_sig = 0
        basket_sell_sig = 0

        if self.position['PICNIC_BASKET'] == self.POSITION_LIMIT['PICNIC_BASKET']:
            self.cont_buy_basket_unfill = 0
        if self.position['PICNIC_BASKET'] == -self.POSITION_LIMIT['PICNIC_BASKET']:
            self.cont_sell_basket_unfill = 0

        do_bask = 0

        if res_sell > trade_at:
            vol = self.position['PICNIC_BASKET'] + self.POSITION_LIMIT['PICNIC_BASKET']
            self.cont_buy_basket_unfill = 0 # no need to buy rn
            assert(vol >= 0)
            if vol > 0:
                do_bask = 1
                basket_sell_sig = 1
                orders['PICNIC_BASKET'].append(Order('PICNIC_BASKET', worst_buy['PICNIC_BASKET'], -vol)) 
                self.cont_sell_basket_unfill += 2
                pb_neg -= vol
                #uku_pos += vol
        elif res_buy < -trade_at:
            vol = self.POSITION_LIMIT['PICNIC_BASKET'] - self.position['PICNIC_BASKET']
            self.cont_sell_basket_unfill = 0 # no need to sell rn
            assert(vol >= 0)
            if vol > 0:
                do_bask = 1
                basket_buy_sig = 1
                orders['PICNIC_BASKET'].append(Order('PICNIC_BASKET', worst_sell['PICNIC_BASKET'], vol))
                self.cont_buy_basket_unfill += 2
                pb_pos += vol

        if int(round(self.person_position['Olivia']['UKULELE'])) > 0:

            val_ord = self.POSITION_LIMIT['UKULELE'] - uku_pos
            if val_ord > 0:
                orders['UKULELE'].append(Order('UKULELE', worst_sell['UKULELE'], val_ord))
        if int(round(self.person_position['Olivia']['UKULELE'])) < 0:

            val_ord = -(self.POSITION_LIMIT['UKULELE'] + uku_neg)
            if val_ord < 0:
                orders['UKULELE'].append(Order('UKULELE', worst_buy['UKULELE'], val_ord))

        return orders

    # def compute_orders_orchids(self, order_depth):
    #     orders: list[Order] = []

    #     buy_orders = list(order_depth.buy_orders.items())
    #     sell_orders = list(order_depth.sell_orders.items())
    #     best_ask, best_ask_amount = sell_orders[0]
    #     best_bid, best_bid_amount = buy_orders[0]

    #     orders.append(Order("ORCHIDS", best_bid, -best_bid_amount))

    #     return orders


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