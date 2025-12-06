from pydantic import BaseModel
from .phi_passport import PhiPassport

class MatchResult(BaseModel):
    compatibility: float
    delta: float

def match_profiles(a: PhiPassport, b: PhiPassport) -> MatchResult:
    delta = abs(a.phi_code - b.phi_code)
    comp = max(0.0, 1.0 - delta)
    return MatchResult(compatibility=comp, delta=delta)
