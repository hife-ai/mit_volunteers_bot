from telebot import types
from datetime import datetime, timedelta

from state import serialize


class ButtonsMaker:
    def __init__(self, config):
        self.config = config

    @staticmethod
    def make_button(name: str, state: dict):
        callback_data = serialize(state)
        return types.InlineKeyboardButton(name, callback_data=callback_data)

    @staticmethod
    def make_grid(buttons: list, columns: int = 1):
        grid = []
        for i in range(0, len(buttons), columns):
            row = buttons[i:i + columns]
            grid.append(row)
        return grid

    def make_buttons_for_roles(self, state: dict):
        buttons = []
        for label, role in self.config['roles'].items():
            state = state | {"role": label}
            if len(role['subroles']) == 1:
                state['subrole'] = list(role['subroles'].keys())[0]

            buttons.append(self.make_button(role['name'], state))

        return self.make_grid(buttons, columns=2)

    def make_buttons_for_subroles(self, state: dict):
        role = state['role']
        buttons = []
        for label, subrole in self.config['roles'][role]['subroles'].items():
            buttons.append(self.make_button(subrole['name'], state | {'subrole': label}))

        return self.make_grid(buttons, columns=1) + self.make_back_button(state)

    def make_buttons_for_dates(self, state: dict):
        buttons = []
        dates = [datetime.now().date() + timedelta(days=days) for days in range(7)]
        for date in dates:
            buttons.append(self.make_button(date.isoformat(), state | {'date': date}))

        return self.make_grid(buttons, columns=1) + self.make_back_button(state)

    def make_buttons_for_times(self, state: dict):
        role = state['role']
        date = datetime.fromisoformat(state['date'])
        buttons = []
        hours = self.config['times'].get(role, list(range(8, 23)))

        for hour in hours:
            time = date + timedelta(hours=hour)
            if datetime.now() + timedelta(minutes=15) < time:
                buttons.append(self.make_button(f'{hour}:00', state | {'date': time}))

        if not buttons:
            return None

        return self.make_grid(buttons, columns=3) + self.make_back_button(state)

    def make_back_button(self, state: dict):
        return [[self.make_button("Вернуться в начало", {'cmd': 'c', 'username': state['username']})]]

    def make_confirm_button(self, state: dict):
        return [[self.make_button("Подтвердить", state | {'cmd': 'f'})]] + self.make_back_button(state)
