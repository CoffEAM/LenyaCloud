from aiogram.fsm.state import State, StatesGroup


class AdminIssueRequestStates(StatesGroup):
    entering_access_text = State()


class AdminRejectRequestStates(StatesGroup):
    entering_reject_reason = State()