class MarketContext:

    def __init__(
        self,
        row=None,
        orderbook=None,
        market_clock=None,
        session=None,
        engine_outputs=None,
    ):

        self.row = row

        self.orderbook = orderbook

        self.market_clock = market_clock

        self.session = session

        self.engine_outputs = (
            engine_outputs
            if engine_outputs is not None
            else {}
        )

        self.system_state = {}

    def set_row(
        self,
        row
    ):

        self.row = row

    def set_orderbook(
        self,
        orderbook
    ):

        self.orderbook = orderbook

    def set_market_clock(
        self,
        market_clock
    ):

        self.market_clock = market_clock

    def set_session(
        self,
        session
    ):

        self.session = session

    def set_engine_outputs(
        self,
        engine_outputs
    ):

        self.engine_outputs = engine_outputs

    def set_system_state(
        self,
        key,
        value
    ):

        self.system_state[
            key
        ] = value

    def get_system_state(
        self,
        key,
        default=None
    ):

        return self.system_state.get(
            key,
            default
        )

    def to_dict(self):

        return {

            "row": self.row,

            "orderbook": self.orderbook,

            "market_clock": self.market_clock,

            "session": self.session,

            "engine_outputs": self.engine_outputs,

            "system_state": self.system_state,
        }