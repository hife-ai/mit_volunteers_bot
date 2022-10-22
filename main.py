import telebot
from telebot import types
import json
from db import add_user_to_db, add_role_to_db, read_schedule
from state import deserialize
from buttons import ButtonsMaker

secrets = json.load(open("secrets.json"))
config = json.load(open("config.json"))
bot = telebot.TeleBot(secrets['token'])

bm = ButtonsMaker(config)


def send_buttons(state: dict, chat_id: int, call_id: int = None, message_id: int = None):
    markup = types.InlineKeyboardMarkup()

    if state['cmd'] == 'f':
        role, subrole = state['role'], state['subrole']
        name = config['roles'][role]['subroles'][subrole]['name']
        text = f'''Вы записаны на {state['date']} в качестве роли "{name}"'''
        add_role_to_db(state)
        bot.send_message(chat_id, text)
        return
    elif 'role' not in state:
        grid = bm.make_buttons_for_roles(state)
        text = 'Выберите роль'
    elif 'subrole' not in state:
        grid = bm.make_buttons_for_subroles(state)
        text = 'Выберите роль'
    elif 'date' not in state:
        grid = bm.make_buttons_for_dates(state)
        text = 'Выберите дату'
    elif ' ' not in state['date']:
        grid = bm.make_buttons_for_times(state)
        text = 'Выберите время (GMT+3, MSK)'
        if grid is None:
            grid = bm.make_back_button()
            text = 'Нет доступных опций времени для этой даты'
    else:
        grid = bm.make_confirm_button(state)
        role = state['role']
        subrole = state['subrole']
        name = config['roles'][role]['subroles'][subrole]['name']
        text = f'Подтвердите роль:\n {name}, время: {state["date"]}'

    for row in grid:
        markup.row(*row)

    if call_id is not None:
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=markup)
        bot.answer_callback_query(call_id)
    else:
        bot.send_message(chat_id=chat_id, text='Выберите роль', reply_markup=markup)


@bot.message_handler(commands=['start', 'role', 'schedule'])
def start_message(message):
    command = message.text
    add_user_to_db(message.from_user.username, message.from_user.first_name, message.from_user.last_name)

    if command in ['/start', '/role']:
        send_buttons({'cmd': 'c', 'username': message.from_user.username}, chat_id=message.chat.id)
    if command == '/schedule':
        csv = read_schedule()
        csv.to_csv("schedule.csv")
        bot.send_document(message.chat.id, document=open('schedule.csv', 'rb'))


@bot.callback_query_handler(lambda call: True)
def handle(call):
    state = deserialize(call.data)
    send_buttons(state, chat_id=call.message.chat.id, call_id=call.id, message_id=call.message.id)


def polling():
    bot.polling()


polling()
