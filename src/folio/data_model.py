from dataclasses import dataclass
from typing import Literal, TypedDict


class PositionDict(TypedDict):
    """Type definition for position dictionary representation"""

    ticker: str
    position_type: Literal["stock", "option"]
    quantity: float
    beta: float
    beta_adjusted_exposure: float
    market_exposure: float  # Quantity * Current Price (fetched at runtime)


class StockPositionDict(PositionDict):
    """Type definition for stock position dictionary"""

    pass


class OptionPositionDict(PositionDict):
    """Type definition for option position dictionary

    TODO: Extend with additional option Greeks (gamma, theta, vega, implied_volatility)
    to match the planned OptionPosition class enhancements.
    """

    strike: float
    expiry: str
    option_type: Literal["CALL", "PUT"]
    delta: float
    delta_exposure: float  # Delta * Notional Value * sign(Quantity)
    notional_value: float  # 100 * Underlying Price * |Quantity|
    underlying_beta: float


class ExposureBreakdownDict(TypedDict):
    """Type definition for exposure breakdown dictionary"""

    stock_exposure: float  # Represents the market exposure from stock positions
    stock_beta_adjusted: float  # Risk-adjusted stock exposure
    option_delta_exposure: float  # Represents the market exposure from option positions
    option_beta_adjusted: float  # Risk-adjusted option exposure
    total_exposure: float  # Combined market exposure from stocks and options
    total_beta_adjusted: float  # Combined risk-adjusted exposure
    description: str  # Human-readable explanation
    formula: str  # Calculation formula used
    components: dict[str, float]  # Detailed breakdown of components


class PortfolioGroupDict(TypedDict):
    """Type definition for portfolio group dictionary"""

    ticker: str
    stock_position: StockPositionDict | None
    option_positions: list[OptionPositionDict]
    net_exposure: float  # Stock Exposure + Sum(Option Delta Exposures)
    beta: float  # Underlying beta
    beta_adjusted_exposure: float  # Sum of all beta-adjusted exposures
    total_delta_exposure: float  # Sum of all option delta exposures
    options_delta_exposure: float  # Same as total_delta_exposure
    call_count: int  # Number of call option positions
    put_count: int  # Number of put option positions


class PortfolioSummaryDict(TypedDict):
    """Type definition for portfolio summary dictionary"""

    net_market_exposure: float  # Long - Short (excluding cash)
    portfolio_beta: float  # Weighted average beta of all positions
    long_exposure: ExposureBreakdownDict  # Detailed breakdown of long exposures
    short_exposure: ExposureBreakdownDict  # Detailed breakdown of short exposures
    options_exposure: ExposureBreakdownDict  # Detailed breakdown of option exposures
    short_percentage: float  # Short / (Long + Short)
    cash_like_positions: list[StockPositionDict]  # List of cash positions
    cash_like_value: float  # Total value of cash positions
    cash_like_count: int  # Number of cash positions
    cash_percentage: float  # Cash / Portfolio Estimated Value
    portfolio_estimate_value: float  # Net Market Exposure + Cash
    help_text: dict[str, str]  # Explanations of each metric


@dataclass
class Position:
    """Base class for all positions"""

    ticker: str
    position_type: Literal["stock", "option"]
    quantity: float
    beta: float
    beta_adjusted_exposure: float
    market_exposure: float  # Quantity * Current Price (fetched at runtime)

    def to_dict(self) -> PositionDict:
        """Convert to a typed dictionary"""
        return {
            "ticker": self.ticker,
            "position_type": self.position_type,
            "quantity": self.quantity,
            "beta": self.beta,
            "beta_adjusted_exposure": self.beta_adjusted_exposure,
            "market_exposure": self.market_exposure,
        }

    @classmethod
    def from_dict(cls, data: PositionDict) -> "Position":
        """Create a Position from a dictionary

        Args:
            data: Dictionary representation of a Position

        Returns:
            A new Position instance
        """
        return cls(
            ticker=data["ticker"],
            position_type=data["position_type"],
            quantity=data["quantity"],
            beta=data["beta"],
            beta_adjusted_exposure=data["beta_adjusted_exposure"],
            market_exposure=data["market_exposure"],
        )


@dataclass
class OptionPosition(Position):
    """Class for option positions

    TODO: Extend with additional option Greeks:
    - gamma: Measures sensitivity of delta to changes in the underlying price
    - theta: Time decay, measures change in option value as time passes
    - vega: Measures sensitivity to implied volatility changes
    - implied_volatility: The market's expectation of future volatility
    """

    strike: float
    expiry: str
    option_type: Literal["CALL", "PUT"]
    delta: float
    delta_exposure: float  # Delta * Notional Value * sign(Quantity)
    notional_value: float  # 100 * Underlying Price * |Quantity|
    underlying_beta: float

    def __post_init__(self):
        self.position_type = "option"

    def to_dict(self) -> OptionPositionDict:
        base_dict = super().to_dict()
        return {
            **base_dict,
            "strike": self.strike,
            "expiry": self.expiry,
            "option_type": self.option_type,
            "delta": self.delta,
            "delta_exposure": self.delta_exposure,
            "notional_value": self.notional_value,
            "underlying_beta": self.underlying_beta,
        }

    @classmethod
    def from_dict(cls, data: OptionPositionDict) -> "OptionPosition":
        """Create an OptionPosition from a dictionary

        Args:
            data: Dictionary representation of an OptionPosition

        Returns:
            A new OptionPosition instance
        """
        return cls(
            ticker=data["ticker"],
            position_type=data["position_type"],
            quantity=data["quantity"],
            beta=data["beta"],
            beta_adjusted_exposure=data["beta_adjusted_exposure"],
            market_exposure=data["market_exposure"],
            strike=data["strike"],
            expiry=data["expiry"],
            option_type=data["option_type"],
            delta=data["delta"],
            delta_exposure=data["delta_exposure"],
            notional_value=data["notional_value"],
            underlying_beta=data["underlying_beta"],
        )


@dataclass
class StockPosition:
    """Details of a stock position"""

    ticker: str
    quantity: int
    beta: float
    market_exposure: float  # Quantity * Current Price (fetched at runtime)
    beta_adjusted_exposure: float  # Market Exposure * Beta

    def to_dict(self) -> StockPositionDict:
        """Convert to a Dash-compatible dictionary"""
        return {
            "ticker": self.ticker,
            "quantity": self.quantity,
            "beta": self.beta,
            "market_exposure": self.market_exposure,
            "beta_adjusted_exposure": self.beta_adjusted_exposure,
            "position_type": "stock",
        }

    @classmethod
    def from_dict(cls, data: StockPositionDict) -> "StockPosition":
        """Create a StockPosition from a dictionary

        Args:
            data: Dictionary representation of a StockPosition

        Returns:
            A new StockPosition instance
        """
        return cls(
            ticker=data["ticker"],
            quantity=data["quantity"],
            beta=data["beta"],
            market_exposure=data["market_exposure"],
            beta_adjusted_exposure=data["beta_adjusted_exposure"],
        )


@dataclass
class PortfolioGroup:
    """Group of related positions (stock + options)"""

    ticker: str
    stock_position: StockPosition | None
    option_positions: list[OptionPosition]

    # Group metrics
    net_exposure: float  # Stock Exposure + Sum(Option Delta Exposures)
    beta: float  # Underlying beta
    beta_adjusted_exposure: float  # Sum of all beta-adjusted exposures
    total_delta_exposure: float  # Sum of all option delta exposures
    options_delta_exposure: float  # Same as total_delta_exposure

    # Option counts
    call_count: int = 0
    put_count: int = 0

    def __post_init__(self) -> None:
        """Calculate option-specific metrics"""
        self.call_count = sum(
            1 for opt in self.option_positions if opt.option_type == "CALL"
        )
        self.put_count = sum(
            1 for opt in self.option_positions if opt.option_type == "PUT"
        )

    def to_dict(self) -> PortfolioGroupDict:
        """Convert to a Dash-compatible dictionary"""
        return {
            "ticker": self.ticker,
            "stock_position": self.stock_position.to_dict()
            if self.stock_position
            else None,
            "option_positions": [opt.to_dict() for opt in self.option_positions],
            "net_exposure": self.net_exposure,
            "beta": self.beta,
            "beta_adjusted_exposure": self.beta_adjusted_exposure,
            "total_delta_exposure": self.total_delta_exposure,
            "options_delta_exposure": self.options_delta_exposure,
            "call_count": self.call_count,
            "put_count": self.put_count,
        }

    @classmethod
    def from_dict(cls, data: PortfolioGroupDict) -> "PortfolioGroup":
        """Create a PortfolioGroup from a dictionary

        Args:
            data: Dictionary representation of a PortfolioGroup

        Returns:
            A new PortfolioGroup instance
        """
        # Create stock position if present
        stock_position = None
        if data.get("stock_position"):
            stock_position = StockPosition.from_dict(data["stock_position"])

        # Create option positions
        option_positions = []
        for opt_data in data.get("option_positions", []):
            option_positions.append(OptionPosition.from_dict(opt_data))

        # Create the group
        return cls(
            ticker=data["ticker"],
            stock_position=stock_position,
            option_positions=option_positions,
            net_exposure=data["net_exposure"],
            beta=data["beta"],
            beta_adjusted_exposure=data["beta_adjusted_exposure"],
            total_delta_exposure=data["total_delta_exposure"],
            options_delta_exposure=data["options_delta_exposure"],
            call_count=data.get("call_count", 0),
            put_count=data.get("put_count", 0),
        )

    def get_details(
        self,
    ) -> dict[str, dict[str, float] | list[dict[str, str | float]]]:
        """Get detailed breakdown of the group's exposures"""
        return {
            "Stock Position": {
                "Market Exposure": self.stock_position.market_exposure
                if self.stock_position
                else 0,
                "Beta-Adjusted": self.stock_position.beta_adjusted_exposure
                if self.stock_position
                else 0,
            },
            "Options": [
                {
                    "Type": opt.option_type,
                    "Strike": opt.strike,
                    "Expiry": opt.expiry,
                    "Delta": opt.delta,
                    "Delta Exposure": opt.delta_exposure,
                    "Beta-Adjusted": opt.beta_adjusted_exposure,
                }
                for opt in self.option_positions
            ],
            "Total": {
                "Net Exposure": self.net_exposure,
                "Beta-Adjusted": self.beta_adjusted_exposure,
            },
        }


@dataclass
class ExposureBreakdown:
    """Detailed breakdown of exposure by type

    This class provides a comprehensive view of market exposure, separating
    stock exposure from options exposure to help users understand the
    different risk components in their portfolio.
    """

    stock_exposure: float  # Represents the market exposure from stock positions
    stock_beta_adjusted: float  # Risk-adjusted stock exposure
    option_delta_exposure: float  # Represents the market exposure from option positions
    option_beta_adjusted: float  # Risk-adjusted option exposure
    total_exposure: float  # Combined market exposure from stocks and options
    total_beta_adjusted: float  # Combined risk-adjusted exposure
    description: str  # Human-readable explanation
    formula: str  # Calculation formula used
    components: dict[str, float]  # Detailed breakdown of components

    def to_dict(self) -> ExposureBreakdownDict:
        """Convert to a Dash-compatible dictionary"""
        return {
            "stock_exposure": self.stock_exposure,
            "stock_beta_adjusted": self.stock_beta_adjusted,
            "option_delta_exposure": self.option_delta_exposure,
            "option_beta_adjusted": self.option_beta_adjusted,
            "total_exposure": self.total_exposure,
            "total_beta_adjusted": self.total_beta_adjusted,
            "description": self.description,
            "formula": self.formula,
            "components": self.components,
        }

    @classmethod
    def from_dict(cls, data: ExposureBreakdownDict) -> "ExposureBreakdown":
        """Create an ExposureBreakdown from a dictionary

        Args:
            data: Dictionary representation of an ExposureBreakdown

        Returns:
            A new ExposureBreakdown instance
        """
        return cls(
            stock_exposure=data["stock_exposure"],
            stock_beta_adjusted=data["stock_beta_adjusted"],
            option_delta_exposure=data["option_delta_exposure"],
            option_beta_adjusted=data["option_beta_adjusted"],
            total_exposure=data["total_exposure"],
            total_beta_adjusted=data["total_beta_adjusted"],
            description=data["description"],
            formula=data["formula"],
            components=data["components"],
        )


@dataclass
class PortfolioSummary:
    """Summary of portfolio metrics with detailed breakdowns

    This class provides a comprehensive view of your portfolio's market exposure,
    risk characteristics, and defensive positioning. It helps you understand your
    portfolio's directional bias, sensitivity to market movements, and overall
    risk profile.
    """

    # Market exposure metrics (excluding cash)
    net_market_exposure: float  # Long - Short (excluding cash)
    portfolio_beta: float  # Weighted average beta of all positions

    # Exposure breakdowns
    long_exposure: ExposureBreakdown  # Detailed breakdown of long exposures
    short_exposure: ExposureBreakdown  # Detailed breakdown of short exposures
    options_exposure: ExposureBreakdown  # Detailed breakdown of option exposures

    # Derived metrics
    short_percentage: float  # Short / (Long + Short)

    # Cash metrics (separate from market exposure)
    cash_like_positions: list[StockPosition] = None  # List of cash positions
    cash_like_value: float = 0.0  # Total value of cash positions
    cash_like_count: int = 0  # Number of cash positions
    cash_percentage: float = 0.0  # Cash / Portfolio Estimated Value

    # Portfolio estimated value (for reference only)
    portfolio_estimate_value: float = 0.0  # Net Market Exposure + Cash

    # Help text for each metric
    help_text: dict[str, str] | None = None

    def __post_init__(self):
        """Initialize help text for metrics"""
        self.help_text = {
            "net_market_exposure": """
                Net Market Exposure: Your portfolio's overall directional bias

                This metric shows whether your portfolio is net long or short the market.
                A positive value means you have more long exposure than short exposure,
                indicating a bullish stance. A negative value indicates a bearish stance.

                Use this to understand how your portfolio might perform in different market
                environments and to ensure your market exposure aligns with your outlook.
            """,
            "portfolio_beta": """
                Portfolio Beta: Your portfolio's sensitivity to market movements

                This metric shows how much your portfolio is expected to move relative to
                the overall market. A beta of 1.5 means your portfolio would be expected
                to move 1.5% for every 1% move in the market.

                Use this to gauge your portfolio's risk level and to ensure it matches
                your risk tolerance and market outlook.
            """,
            "long_exposure": """
                Long Exposure: Your portfolio's bullish positioning

                This metric shows your total positive market exposure from both stocks
                and options. It includes long stock positions, long call options, and
                short put options.

                Use this to understand your potential upside in rising markets and to
                ensure your bullish positioning aligns with your market outlook.
            """,
            "short_exposure": """
                Short Exposure: Your portfolio's bearish positioning

                This metric shows your total negative market exposure from both stocks
                and options. It includes short stock positions, short call options, and
                long put options.

                Use this to understand your downside protection in falling markets and
                to ensure your hedging strategy is adequate for your risk tolerance.
            """,
            "options_exposure": """
                Options Exposure: Your market exposure from options

                This breakdown shows how options contribute to your overall market exposure.
                Options can provide leverage, income, or hedging depending on the strategy.

                Use this to understand how much of your market risk comes from options
                versus stocks, and to ensure your options strategies align with your
                investment goals.
            """,
            "short_percentage": """
                Short Percentage: Your portfolio's hedge ratio

                This metric shows what percentage of your market exposure is short.
                A higher percentage indicates more downside protection.

                Use this to gauge your defensive positioning and to ensure your
                hedging strategy aligns with your market outlook and risk tolerance.
            """,
            "cash_like_positions": """
                Cash-like Positions: Your portfolio's defensive assets

                These are positions with very low market correlation, such as money
                market funds, short-term treasuries, and other highly liquid assets.

                Use this to understand your defensive positioning and available capital
                for new opportunities.
            """,
            "cash_like_value": """
                Cash-like Value: Your portfolio's defensive capital

                This is the total value of your cash and cash-equivalent positions.
                It represents your most liquid and lowest-risk assets.

                Use this to understand your defensive positioning and available
                dry powder for new investment opportunities.
            """,
            "cash_like_count": """
                Cash-like Count: Diversification of your defensive assets

                This shows how many different cash or cash-equivalent positions
                you hold in your portfolio.

                Use this to ensure you're not overly concentrated in a single
                cash-like instrument.
            """,
            "cash_percentage": """
                Cash Percentage: Your portfolio's defensive allocation

                This shows what percentage of your portfolio is in cash or cash equivalents.
                A higher percentage indicates more safety in market downturns but potentially
                lower returns in bull markets.

                Use this to gauge your defensive positioning and to ensure it aligns with
                your market outlook and risk tolerance.
            """,
            "portfolio_estimate_value": """
                Portfolio Estimated Value: Your portfolio's total size

                This is an estimate of your portfolio's total value, including both
                market exposure and cash. It provides a baseline for calculating
                percentage allocations.

                Use this to track your portfolio's overall size and to calculate
                meaningful percentage allocations for different exposures.
            """,
        }

    def to_dict(self) -> PortfolioSummaryDict:
        """Convert to a Dash-compatible dictionary"""
        if self.help_text is None:
            self.__post_init__()

        # Initialize empty list if None
        if self.cash_like_positions is None:
            self.cash_like_positions = []

        return {
            "net_market_exposure": self.net_market_exposure,
            "portfolio_beta": self.portfolio_beta,
            "long_exposure": self.long_exposure.to_dict(),
            "short_exposure": self.short_exposure.to_dict(),
            "options_exposure": self.options_exposure.to_dict(),
            "short_percentage": self.short_percentage,
            "cash_like_positions": [pos.to_dict() for pos in self.cash_like_positions],
            "cash_like_value": self.cash_like_value,
            "cash_like_count": self.cash_like_count,
            "cash_percentage": self.cash_percentage,
            "portfolio_estimate_value": self.portfolio_estimate_value,
            "help_text": self.help_text if self.help_text is not None else {},
        }

    @classmethod
    def from_dict(cls, data: PortfolioSummaryDict) -> "PortfolioSummary":
        """Create a PortfolioSummary from a dictionary

        Args:
            data: Dictionary representation of a PortfolioSummary

        Returns:
            A new PortfolioSummary instance
        """
        # Create exposure breakdowns
        long_exposure = ExposureBreakdown.from_dict(data["long_exposure"])
        short_exposure = ExposureBreakdown.from_dict(data["short_exposure"])
        options_exposure = ExposureBreakdown.from_dict(data["options_exposure"])

        # Create cash-like positions
        cash_like_positions = []
        for pos_data in data.get("cash_like_positions", []):
            cash_like_positions.append(StockPosition.from_dict(pos_data))

        # Support both old and new field names for backward compatibility
        net_market_exposure = data.get(
            "net_market_exposure", data.get("total_value_net", 0.0)
        )
        cash_percentage = data.get("cash_percentage", 0.0)
        portfolio_estimate_value = data.get("portfolio_estimate_value", 0.0)

        return cls(
            net_market_exposure=net_market_exposure,
            portfolio_beta=data["portfolio_beta"],
            long_exposure=long_exposure,
            short_exposure=short_exposure,
            options_exposure=options_exposure,
            short_percentage=data["short_percentage"],
            cash_like_positions=cash_like_positions,
            cash_like_value=data["cash_like_value"],
            cash_like_count=data["cash_like_count"],
            cash_percentage=cash_percentage,
            portfolio_estimate_value=portfolio_estimate_value,
            help_text=data.get("help_text"),
        )


def create_portfolio_group(
    stock_data: dict[str, str | int | float] | None = None,
    option_data: list[dict[str, str | int | float]] | None = None,
) -> PortfolioGroup | None:
    """Create a PortfolioGroup from stock and option data"""
    if not stock_data and not option_data:
        return None

    # Create stock position if data exists
    stock_position = None
    if stock_data:
        stock_position = StockPosition(
            ticker=stock_data["ticker"],
            quantity=stock_data["quantity"],
            beta=stock_data["beta"],
            market_exposure=stock_data["market_exposure"],
            beta_adjusted_exposure=stock_data["beta_adjusted_exposure"],
        )

    # Create option positions if data exists
    option_positions = []
    if option_data:
        for opt in option_data:
            option_positions.append(
                OptionPosition(
                    # Base Position fields
                    ticker=opt["ticker"],
                    position_type="option",
                    quantity=opt["quantity"],
                    beta=opt["beta"],
                    beta_adjusted_exposure=opt["beta_adjusted_exposure"],
                    market_exposure=opt["market_exposure"],
                    # OptionPosition specific fields
                    strike=opt["strike"],
                    expiry=opt["expiry"],
                    option_type=opt["option_type"],
                    delta=opt["delta"],
                    delta_exposure=opt["delta_exposure"],
                    notional_value=opt["notional_value"],
                    underlying_beta=opt["beta"],  # Use same beta for underlying
                )
            )

    # Calculate group metrics
    net_exposure = (stock_position.market_exposure if stock_position else 0) + sum(
        opt.delta_exposure for opt in option_positions
    )

    beta = stock_position.beta if stock_position else 0  # Use stock beta as base

    beta_adjusted_exposure = (
        stock_position.beta_adjusted_exposure if stock_position else 0
    ) + sum(opt.beta_adjusted_exposure for opt in option_positions)

    total_delta_exposure = sum(opt.delta_exposure for opt in option_positions)

    options_delta_exposure = sum(opt.delta_exposure for opt in option_positions)

    return PortfolioGroup(
        ticker=stock_data["ticker"] if stock_data else option_data[0]["ticker"],
        stock_position=stock_position,
        option_positions=option_positions,
        net_exposure=net_exposure,
        beta=beta,
        beta_adjusted_exposure=beta_adjusted_exposure,
        total_delta_exposure=total_delta_exposure,
        options_delta_exposure=options_delta_exposure,
    )
