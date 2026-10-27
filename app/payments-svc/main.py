import logging

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("payments")

app = FastAPI(title="payments-svc (mock)")


class Charge(BaseModel):
    order_id: int
    amount: float
    card_number: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/charge")
def charge(c: Charge):
    # Mock payment: always approves. Use test card 4111111111111111.
    log.info("charging order=%s amount=%s card=%s", c.order_id, c.amount, c.card_number)
    return {"order_id": c.order_id, "status": "approved", "amount": c.amount}
