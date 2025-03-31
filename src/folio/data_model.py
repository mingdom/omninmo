from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Position:
    """Base class for all positions"""

    ticker: str
    position_type: str  # "stock" or "option"
    quantity: float
    market_value: float
    beta: float
    beta_adjusted_exposure: float
    clean_value: float
    weight: float
    position_beta: float


@dataclass
class OptionPosition(Position):
    """Class for option positions"""

    strike: float
    expiry: str
    option_type: str  # "CALL" or "PUT"
    delta: float
    delta_exposure: float
    notional_value: float
    underlying_beta: float

    def __post_init__(self):
        self.position_type = "option"


@dataclass
class PortfolioGroup:
    """Class for grouping stock and option positions by underlying"""

    stock_position: Optional[Position] = None
    option_positions: List[OptionPosition] = field(default_factory=list)
    net_exposure: float = 0.0
    beta_adjusted_exposure: float = 0.0
    total_delta_exposure: float = 0.0
    call_count: int = 0
    put_count: int = 0
    net_option_value: float = 0.0

    def __post_init__(self):
        # Calculate net exposure
        self.net_exposure = (
            self.stock_position.market_value if self.stock_position else 0.0
        ) + sum(opt.market_value for opt in self.option_positions)

        # Calculate beta-adjusted exposure
        self.beta_adjusted_exposure = (
            self.stock_position.beta_adjusted_exposure if self.stock_position else 0.0
        ) + sum(opt.beta_adjusted_exposure for opt in self.option_positions)

        # Calculate total delta exposure
        self.total_delta_exposure = sum(
            opt.delta_exposure for opt in self.option_positions
        )

        # Count calls and puts
        self.call_count = sum(
            1 for opt in self.option_positions if opt.option_type == "CALL"
        )
        self.put_count = sum(
            1 for opt in self.option_positions if opt.option_type == "PUT"
        )

        # Calculate net option value
        self.net_option_value = sum(opt.market_value for opt in self.option_positions)


@dataclass
class PortfolioSummary:
    """Class for portfolio-wide summary metrics"""

    total_value_net: float
    total_value_abs: float
    portfolio_beta: float
    long_value: float
    long_beta_exposure: float
    long_portfolio_beta: float
    short_value: float
    short_beta_exposure: float
    short_portfolio_beta: float
    short_percentage: float
    options_delta_exposure: float
    options_beta_adjusted: float
    total_exposure_before_shorts: float
    total_exposure_after_shorts: float
    exposure_reduction_amount: float
    exposure_reduction_percentage: float


def create_portfolio_group(
    stock_data: Optional[Dict], option_data: List[Dict]
) -> Optional[PortfolioGroup]:
    """Create a PortfolioGroup from stock and option data"""

    # Create stock position if data exists
    stock_position = None
    if stock_data:
        stock_position = Position(
            ticker=stock_data["ticker"],
            position_type="stock",
            quantity=stock_data["quantity"],
            market_value=stock_data["market_value"],
            beta=stock_data["beta"],
            beta_adjusted_exposure=stock_data["beta_adjusted_exposure"],
            clean_value=stock_data["clean_value"],
            weight=stock_data["weight"],
            position_beta=stock_data["position_beta"],
        )

    # Create option positions
    option_positions = []
    for opt_data in option_data:
        option_position = OptionPosition(
            ticker=opt_data["ticker"],
            position_type="option",
            quantity=opt_data["quantity"],
            market_value=opt_data["market_value"],
            beta=opt_data["beta"],
            beta_adjusted_exposure=opt_data["beta_adjusted_exposure"],
            clean_value=opt_data["clean_value"],
            weight=opt_data["weight"],
            position_beta=opt_data["position_beta"],
            strike=opt_data["strike"],
            expiry=opt_data["expiry"],
            option_type=opt_data["option_type"],
            delta=opt_data["delta"],
            delta_exposure=opt_data["delta_exposure"],
            notional_value=opt_data["notional_value"],
            underlying_beta=opt_data["underlying_beta"],
        )
        option_positions.append(option_position)

    # Create and return portfolio group if we have any positions
    if stock_position or option_positions:
        return PortfolioGroup(
            stock_position=stock_position, option_positions=option_positions
        )

    return None
