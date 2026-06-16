from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

from app.db.base import Base


class MarketTick(Base):
    __tablename__ = "market_ticks"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(String, index=True, nullable=False)
    main_type = Column(String)
    sub_type = Column(String)
    short_name = Column(String)
    trading_date = Column(String)
    price_high = Column(Float)
    price_low = Column(Float)
    close_price = Column(Float)
    open_price = Column(Float)
    trade_volume = Column(Integer)
    share_volume = Column(Integer)
    turnover = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)