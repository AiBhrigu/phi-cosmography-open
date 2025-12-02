from pydantic import BaseModel

class PhiPassport(BaseModel):
    user_id: str
    birth_date: int
    phi_code: float

def build_phi_passport(user_id: str, birth_date: int) -> PhiPassport:
    year = birth_date // 10000
    phi = (year % 100) / 100
    return PhiPassport(user_id=user_id, birth_date=birth_date, phi_code=phi)
