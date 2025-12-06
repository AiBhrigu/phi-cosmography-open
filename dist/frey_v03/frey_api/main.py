from fastapi import FastAPI
from pydantic import BaseModel

from frey_core import (
    build_phi_passport,
    match_profiles,
    log_event,
    PhiPassport
)

app = FastAPI(title="FREY API", version="0.3.0")

class PassportRequest(BaseModel):
    user_id: str
    birth_date: int

class MatchAssetRequest(BaseModel):
    user_birth: int
    asset_code: str

class EventRequest(BaseModel):
    user_id: str
    event: str

@app.get('/ping')
def ping():
    return {'status': 'ok', 'phi': 1.618}

@app.post('/phi-passport')
def api_phi_passport(req: PassportRequest) -> PhiPassport:
    return build_phi_passport(req.user_id, req.birth_date)

@app.post('/match-user-asset')
def api_match_user_asset(req: MatchAssetRequest):
    user = build_phi_passport('user', req.user_birth)
    asset = build_phi_passport(req.asset_code, 20000101)
    return match_profiles(user, asset)

@app.post('/event-log')
def api_event_log(req: EventRequest):
    return log_event(req.user_id, req.event)
