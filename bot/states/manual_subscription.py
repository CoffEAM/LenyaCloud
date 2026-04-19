from aiogram.fsm.state import State, StatesGroup


class ManualSubscriptionStates(StatesGroup):
    entering_user_id = State()
    choosing_type = State()
    entering_days = State()
    entering_access_text = State()
    entering_confirm = State()