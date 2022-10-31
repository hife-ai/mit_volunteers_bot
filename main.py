import telebot
from telebot import types
import json
import db
from state import deserialize
from buttons import ButtonsMaker
from threading import Thread
from time import sleep

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
        db.add_role_to_db(state)
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
    db.add_user_to_db(message.from_user.username, message.from_user.first_name, message.from_user.last_name, message.chat.id)

    if command in ['/start', '/role']:
        send_buttons({'cmd': 'c', 'username': message.from_user.username}, chat_id=message.chat.id)
    if command == '/schedule':
        csv = db.read_schedule()
        csv.to_csv("schedule.csv")
        bot.send_document(message.chat.id, document=open('schedule.csv', 'rb'))


@bot.callback_query_handler(lambda call: not call.data.startswith("notification"))
def handle(call):
    state = deserialize(call.data)
    send_buttons(state, chat_id=call.message.chat.id, call_id=call.id, message_id=call.message.id)


def notify_admin_person_unavailable(id: int):
    admins = db.get_admins()
    print (admins)
    for admin in admins:
        admin_chat_id = db.get_chat_id(admin)
        print (admin_chat_id)
        entry = db.get_role_info(id)
        bot.send_message(chat_id=admin_chat_id, text=f"Волонтер @{entry.username} не успевает или отклонил запись на роль '{entry.subrole}' "
                                                     f"на время {entry['datetime']}")


def send_notifications():
    entries = db.get_nearest_unconfirmed_entries('1 hour')
    print (entries)
    for _, entry in entries.iterrows():
        markup = types.InlineKeyboardMarkup()
        grid = bm.make_notification_buttons(entry.id)

        for row in grid:
            markup.row(*row)

        db.set_entry_status(entry.id, "notification sent")
        bot.send_message(entry.chat_id, f"@{entry.username}, Вы записаны на роль {entry.subrole} на время {entry['datetime']}.", reply_markup=markup)

def check_confirmations():
    entries = db.get_nearest_unconfirmed_entries('15 minutes')
    for _, entry in entries.iterrows():
        db.set_entry_status(entry.id, "missed; admins notified")
        notify_admin_person_unavailable(entry.id)


@bot.callback_query_handler(lambda call: call.data.startswith("notification"))
def handle_notification_answer(call):
    _, status, id = call.data.split(';')

    db.set_entry_status(int(id), status)
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.id,
                          text=call.message.text + "\n" +
                               ("Вы подтвердили роль" if status == 'confirmed' else "Вы отказались от роли"))

    if status == 'refused':
        notify_admin_person_unavailable(id)


def notifications_thread():
    while True:
        send_notifications()
        check_confirmations()
        sleep(30)


Thread(target=notifications_thread).start()


def polling():
    bot.polling()


polling()
