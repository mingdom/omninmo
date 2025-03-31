from dataclasses import dataclass
from typing import Dict, List, Literal, NotRequired, Optional, TypedDict, Union


class PositionDict(TypedDict):
    """Type definition for position dictionary representation"""

    ticker: str
    position_type: Literal["stock", "option"]
    quantity: float
    market_value: float
    beta: float
    beta_adjusted_exposure: float
    clean_value: float
    weight: float
    position_beta: float


class StockPositionDict(PositionDict):
    """Type definition for stock position dictionary"""

    pass


class OptionPositionDict(PositionDict):
    """Type definition for option position dictionary"""

    strike: float
    expiry: str
    option_type: Literal["CALL", "PUT"]
    delta: float
    delta_exposure: float
    notional_value: float
    underlying_beta: float


class ExposureBreakdownDict(TypedDict):
    """Type definition for exposure breakdown dictionary"""

    stock_value: float
    stock_beta_adjusted: float
    option_delta_value: float
    option_beta_adjusted: float
    total_value: float
    total_beta_adjusted: float
    description: str
    formula: str
    components: Dict[str, float]


class PortfolioGroupDict(TypedDict):
    """Type definition for portfolio group dictionary"""

    ticker: str
    stock_position: NotRequired[Union[StockPositionDict, None]]
    option_positions: List[OptionPositionDict]
    total_value: float
    net_exposure: float
    beta: float
    beta_adjusted_exposure: float
    total_delta_exposure: float
    options_delta_exposure: float
    call_count: int
    put_count: int
    net_option_value: float


class PortfolioSummaryDict(TypedDict):
    """Type definition for portfolio summary dictionary"""

    total_value_net: float
    total_value_abs: float
    portfolio_beta: float
    long_exposure: ExposureBreakdownDict
    short_exposure: ExposureBreakdownDict
    options_exposure: ExposureBreakdownDict
    short_percentage: float
    exposure_reduction_percentage: float
    help_text: Dict[str, str]


@dataclass
class Position:
    """Base class for all positions"""

    ticker: str
    position_type: Literal["stock", "option"]
    quantity: float
    market_value: float
    beta: float
    beta_adjusted_exposure: float
    clean_value: float
    weight: float
    position_beta: float

    def to_dict(self) -> PositionDict:
        """Convert to a typed dictionary"""
        return {
            "ticker": self.ticker,
            "position_type": self.position_type,
            "quantity": self.quantity,
            "market_value": self.market_value,
            "beta": self.beta,
            "beta_adjusted_exposure": self.beta_adjusted_exposure,
            "clean_value": self.clean_value,
            "weight": self.weight,
            "position_beta": self.position_beta,
        }


@dataclass
class OptionPosition(Position):
    """Class for option positions"""

    strike: float
    expiry: str
    option_type: Literal["CALL", "PUT"]
    delta: float
    delta_exposure: float
    notional_value: float
    underlying_beta: float

    def __post_init__(self):
        self.position_type = "option"
        self.clean_value = self.market_value
        self.weight = 1.0
        self.position_beta = self.beta

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


@dataclass
class StockPosition:
    """Details of a stock position"""

    ticker: str
    quantity: int
    market_value: float
    beta: float
    beta_adjusted_exposure: float

    def to_dict(self) -> StockPositionDict:
        """Convert to a Dash-compatible dictionary"""
        return {
            "ticker": self.ticker,
            "quantity": self.quantity,
            "market_value": self.market_value,
            "beta": self.beta,
            "beta_adjusted_exposure": self.beta_adjusted_exposure,
            "position_type": "stock",
            "clean_value": self.market_value,
            "weight": 1.0,
            "position_beta": self.beta,
        }


@dataclass
class PortfolioGroup:
    """Group of related positions (stock + options)"""

    ticker: str
    stock_position: Optional[StockPosition]
    option_positions: List[OptionPosition]

    # Group metrics
    total_value: float
    net_exposure: float
    beta: float
    beta_adjusted_exposure: float
    total_delta_exposure: float
    options_delta_exposure: float

    # Option counts
    call_count: int = 0
    put_count: int = 0
    net_option_value: float = 0.0

    def __post_init__(self) -> None:
        """Calculate option-specific metrics"""
        self.call_count = sum(
            1 for opt in self.option_positions if opt.option_type == "CALL"
        )
        self.put_count = sum(
            1 for opt in self.option_positions if opt.option_type == "PUT"
        )
        self.net_option_value = sum(opt.market_value for opt in self.option_positions)

    def to_dict(self) -> PortfolioGroupDict:
        """Convert to a Dash-compatible dictionary"""
        return {
            "ticker": self.ticker,
            "stock_position": self.stock_position.to_dict()
            if self.stock_position
            else None,
            "option_positions": [opt.to_dict() for opt in self.option_positions],
            "total_value": self.total_value,
            "net_exposure": self.net_exposure,
            "beta": self.beta,
            "beta_adjusted_exposure": self.beta_adjusted_exposure,
            "total_delta_exposure": self.total_delta_exposure,
            "options_delta_exposure": self.options_delta_exposure,
            "call_count": self.call_count,
            "put_count": self.put_count,
            "net_option_value": self.net_option_value,
        }

    def get_details(
        self,
    ) -> Dict[str, Union[Dict[str, float], List[Dict[str, Union[str, float]]]]]:
        """Get detailed breakdown of the group's exposures"""
        return {
            "Stock Position": {
                "Value": self.stock_position.market_value if self.stock_position else 0,
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
    """Detailed breakdown of exposure by type"""

    stock_value: float
    stock_beta_adjusted: float
    option_delta_value: float
    option_beta_adjusted: float
    total_value: float
    total_beta_adjusted: float
    description: str
    formula: str
    components: Dict[str, float]

    def to_dict(self) -> ExposureBreakdownDict:
        """Convert to a Dash-compatible dictionary"""
        return {
            "stock_value": self.stock_value,
            "stock_beta_adjusted": self.stock_beta_adjusted,
            "option_delta_value": self.option_delta_value,
            "option_beta_adjusted": self.option_beta_adjusted,
            "total_value": self.total_value,
            "total_beta_adjusted": self.total_beta_adjusted,
            "description": self.description,
            "formula": self.formula,
            "components": self.components,
        }


@dataclass
class PortfolioSummary:
    """Summary of portfolio metrics with detailed breakdowns"""

    # Total portfolio values
    total_value_net: float
    total_value_abs: float
    portfolio_beta: float

    # Long exposure details
    long_exposure: ExposureBreakdown

    # Short exposure details
    short_exposure: ExposureBreakdown

    # Options exposure (for reference)
    options_exposure: ExposureBreakdown

    # Derived metrics
    short_percentage: float
    exposure_reduction_percentage: float

    # Help text for each metric
    help_text: Optional[Dict[str, str]] = None

    def __post_init__(self):
        """Initialize help text for metrics"""
        self.help_text = {
            "total_value_net": """
                Net portfolio value (Long - Short)
                Formula: Sum of all position values
                Includes: Stock positions and option market values
            """,
            "total_value_abs": """
                Gross portfolio value (|Long| + |Short|)
                Formula: Sum of absolute values of all positions
                Includes: Stock positions and option market values
            """,
            "portfolio_beta": """
                Portfolio's overall market sensitivity
                Formula: Weighted average of position betas
                Note: Options contribute through delta-adjusted exposure
            """,
            "long_exposure": """
                Long market exposure
                Includes:
                - Long stock positions
                - Long call options (delta-adjusted)
                - Short put options (delta-adjusted)
                Formula: Stock value + Option delta exposure
            """,
            "short_exposure": """
                Short market exposure
                Includes:
                - Short stock positions
                - Short call options (delta-adjusted)
                - Long put options (delta-adjusted)
                Formula: |Stock value + Option delta exposure|
            """,
            "options_exposure": """
                Option positions' market exposure
                Calculation:
                - Calls: +delta * notional for long, -delta * notional for short
                - Puts: -delta * notional for long, +delta * notional for short
                Note: This is shown for reference, already included in long/short
            """,
            "short_percentage": """
                Percentage of portfolio in short positions
                Formula: |Short exposure| / Gross exposure
                Includes both stock and option positions
            """,
            "exposure_reduction_percentage": """
                How much shorts reduce long exposure
                Formula: |Short exposure| / Long exposure
                Shows effectiveness of hedging
            """,
        }

    def to_dict(self) -> PortfolioSummaryDict:
        """Convert to a Dash-compatible dictionary"""
        if self.help_text is None:
            self.__post_init__()
        return {
            "total_value_net": self.total_value_net,
            "total_value_abs": self.total_value_abs,
            "portfolio_beta": self.portfolio_beta,
            "long_exposure": self.long_exposure.to_dict(),
            "short_exposure": self.short_exposure.to_dict(),
            "options_exposure": self.options_exposure.to_dict(),
            "short_percentage": self.short_percentage,
            "exposure_reduction_percentage": self.exposure_reduction_percentage,
            "help_text": self.help_text if self.help_text is not None else {},
        }


def create_portfolio_group(
    stock_data: Optional[Dict[str, Union[str, int, float]]] = None,
    option_data: Optional[List[Dict[str, Union[str, int, float]]]] = None,
) -> Optional[PortfolioGroup]:
    """Create a PortfolioGroup from stock and option data"""
    if not stock_data and not option_data:
        return None

    # Create stock position if data exists
    stock_position = None
    if stock_data:
        stock_position = StockPosition(
            ticker=stock_data["ticker"],
            quantity=stock_data["quantity"],
            market_value=stock_data["market_value"],
            beta=stock_data["beta"],
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
                    market_value=opt["market_value"],
                    beta=opt["beta"],
                    beta_adjusted_exposure=opt["beta_adjusted_exposure"],
                    clean_value=opt["market_value"],  # Use market value as clean value
                    weight=1.0,  # Default weight
                    position_beta=opt["beta"],  # Use position beta
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
    total_value = (stock_position.market_value if stock_position else 0) + sum(
        opt.market_value for opt in option_positions
    )

    net_exposure = (stock_position.market_value if stock_position else 0) + sum(
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
        total_value=total_value,
        net_exposure=net_exposure,
        beta=beta,
        beta_adjusted_exposure=beta_adjusted_exposure,
        total_delta_exposure=total_delta_exposure,
        options_delta_exposure=options_delta_exposure,
    )
