from pydantic import BaseModel


class ReferralCreate(BaseModel):

    telegramId: int


class ReferralVisitCreate(BaseModel):

    referralCode: str
    visitorTelegramId: int
