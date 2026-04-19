from aiogram.fsm.state import State, StatesGroup


class GetKeyStates(StatesGroup):
    choosing_plan = State()
    entering_custom_days = State()
    entering_comment = State()
    waiting_payment_proof = State()
    confirming_request = State()


class RenewSubscriptionStates(StatesGroup):
    choosing_plan = State()
    entering_custom_days = State()
    entering_comment = State()
    waiting_payment_proof = State()
    confirming_request = State()