from fastapi import APIRouter
from sqlalchemy import desc
from app.db.session import SessionLocal
from app.db.models import MarketTick

router = APIRouter()


@router.get("/ticks/latest")
def latest_ticks(limit: int = 20):
    db = SessionLocal()
    try:
        rows = (
            db.query(MarketTick)
            .order_by(desc(MarketTick.timestamp))
            .limit(limit)
            .all()
        )

        return [
            {
                "company_id": r.company_id,
                "main_type": r.main_type,
                "sub_type": r.sub_type,
                "short_name": r.short_name,
                "trading_date": r.trading_date,
                "price_high": r.price_high,
                "price_low": r.price_low,
                "close_price": r.close_price,
                "open_price": r.open_price,
                "trade_volume": r.trade_volume,
                "share_volume": r.share_volume,
                "turnover": r.turnover,
                "timestamp": r.timestamp
            }
            for r in rows
        ]
    finally:
        db.close()