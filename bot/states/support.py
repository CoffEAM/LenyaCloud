from aiogram.fsm.state import State, StatesGroup


class UserSupportStates(StatesGroup):
    choosing_topic = State()
    entering_message = State()


class AdminSupportStates(StatesGroup):
    entering_reply = State()