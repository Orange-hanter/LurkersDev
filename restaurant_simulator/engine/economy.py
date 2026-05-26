from ..models import GameState
from ..config import REP_MIN, REP_MAX


def end_of_day(state: GameState) -> str:
    total_salary = sum(s.daily_salary for s in state.staff_list)
    state.pending_expense += total_salary

    state.budget += state.pending_income
    state.budget -= state.pending_expense
    state.reputation += state.pending_rep

    state.reputation = max(REP_MIN, min(REP_MAX, state.reputation))

    if state.budget <= 0 or state.reputation <= REP_MIN:
        return "bankruptcy"
    return "next_day"
