from pydantic import BaseModel
from datetime import datetime


class MarketTick(BaseModel):
    symbol: str
    price: float
    volume: float
    timestamp: datetime