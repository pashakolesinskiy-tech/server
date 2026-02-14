from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    telegram_id = Column(
        BigInteger,
        unique=True,
        index=True
    )

    referral_code = Column(
        String,
        unique=True,
        index=True
    )

    referral_count = Column(
        Integer,
        default=0
    )

    created_at = Column(
        DateTime,
        default=func.now()
    )


class ReferralVisit(Base):

    __tablename__ = "referral_visits"

    id = Column(Integer, primary_key=True)

    referrer_id = Column(
        Integer,
        ForeignKey("users.id")
    )

    visitor_telegram_id = Column(BigInteger)

    created_at = Column(
        DateTime,
        default=func.now()
    )