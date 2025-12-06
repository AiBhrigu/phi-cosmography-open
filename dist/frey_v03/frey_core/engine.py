class FreyCoreEngine:
    """Minimal stable engine core."""
    def __init__(self):
        pass

    def phi_basic(self, birth_date: int) -> float:
        year = birth_date // 10000
        return ((year % 100) / 100)
