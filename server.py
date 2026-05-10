from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

store = {
    "offer": None,
    "answer": None,
}


class SDP(BaseModel):
    sdp: str


@app.get("/")
def home():
    return {"status": "ok"}


@app.post("/offer")
def post_offer(data: SDP):
    store["offer"] = data.sdp
    store["answer"] = None
    return {"ok": True}


@app.get("/offer")
def get_offer():
    return {"sdp": store["offer"]}


@app.post("/answer")
def post_answer(data: SDP):
    store["answer"] = data.sdp
    return {"ok": True}


@app.get("/answer")
def get_answer():
    return {"sdp": store["answer"]}