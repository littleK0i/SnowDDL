class StockSaleSum:
    def __init__(self):
        self._cost_total = 0
        self._symbol = ""

    def process(self, symbol, quantity, price):
        self._symbol = symbol
        cost = quantity * price
        self._cost_total += cost
        yield (symbol, cost)

    def end_partition(self):
        yield (self._symbol, self._cost_total)
