from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import os
import httpx

from database import SessionLocal
from models import User, ReferralVisit
from schemas import ReferralCreate, ReferralVisitCreate
from utils import generate_code

from database import engine
from models import Base
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

# Telegram Bot настройки
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8438331740:AAGxuhrNsqAfVbDrALrv0nxSL94Q6cE5L7M")
TELEGRAM_ADMIN_ID = 535860690

from fastapi import Request
from pydantic import BaseModel


class Feedback(BaseModel):
    message: str
    userAgent: str = None
    timestamp: int = None


@app.post("/api/feedback")
async def feedback(data: Feedback):
    """
    Получает обратную связь и отправляет в Telegram администратору
    """
    try:
        async with httpx.AsyncClient() as client:
            # Формируем сообщение для Telegram
            text = f"📩 <b>Обратная связь от пользователя</b>\n\n"
            text += f"{data.message}\n\n"
            if data.userAgent:
                text += f"<i>User Agent: {data.userAgent[:100]}...</i>"
            
            # Отправляем сообщение в Telegram
            response = await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": TELEGRAM_ADMIN_ID,
                    "text": text,
                    "parse_mode": "HTML"
                },
                timeout=10.0
            )
            
            if response.status_code != 200:
                print(f"Telegram API error: {response.status_code} - {response.text}")
                return {"success": False, "error": "Failed to send message"}
                
        return {"success": True}
    except Exception as e:
        print(f"Feedback error: {e}")
        return {"success": False, "error": str(e)}


app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)


@app.on_event("startup")
async def startup():

    print("CREATING TABLES...")

    async with engine.begin() as conn:

        await conn.run_sync(Base.metadata.create_all)

    print("TABLES CREATED")

async def get_db():

    async with SessionLocal() as session:

        yield session


# POST /api/referral


@app.post("/api/referral")
async def create_referral(
    data: ReferralCreate,
    db: AsyncSession = Depends(get_db)
):

    result = await db.execute(

        select(User)
        .where(
            User.telegram_id == data.telegramId
        )

    )

    user = result.scalar_one_or_none()

    if user:

        return {

            "referralCode": user.referral_code

        }

    code = generate_code()

    user = User(

        telegram_id=data.telegramId,
        referral_code=code

    )

    db.add(user)

    await db.commit()

    return {

        "referralCode": code

    }


# GET /api/user/{telegramId}


@app.get("/api/user/{telegramId}")
async def get_user(
    telegramId: int,
    db: AsyncSession = Depends(get_db)
):

    result = await db.execute(

        select(User)
        .where(
            User.telegram_id == telegramId
        )

    )

    user = result.scalar_one_or_none()

    if not user:

        return None

    return {

        "id": user.id,
        "telegramId": user.telegram_id,
        "referralCode": user.referral_code,
        "referralCount": user.referral_count

    }


# POST /api/referral/visit


@app.post("/api/referral/visit")
async def referral_visit(
    data: ReferralVisitCreate,
    db: AsyncSession = Depends(get_db)
):

    result = await db.execute(

        select(User)
        .where(
            User.referral_code == data.referralCode
        )

    )

    user = result.scalar_one_or_none()

    if not user:

        return {

            "success": False

        }

    visit = ReferralVisit(

        referrer_id=user.id,
        visitor_telegram_id=data.visitorTelegramId

    )

    user.referral_count += 1

    db.add(visit)

    await db.commit()

    return {

        "success": True

    }


# GET /api/referral/stats


@app.get("/api/referral/stats")
async def stats(
    telegramId: int,
    db: AsyncSession = Depends(get_db)
):

    result = await db.execute(

        select(User)
        .where(
            User.telegram_id == telegramId
        )

    )

    user = result.scalar_one_or_none()

    if not user:

        return None

    visits = await db.execute(

        select(func.count())
        .select_from(ReferralVisit)
        .where(
            ReferralVisit.referrer_id == user.id
        )

    )

    return {

        "referralCount": user.referral_count,
        "visits": visits.scalar()

    }