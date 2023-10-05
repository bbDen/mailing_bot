import threading

import psycopg2
import telebot
import time
from utility.connection_db import db_params
from utility.bot_token import BOT_TOKEN

conn = psycopg2.connect(**db_params)

cursor = conn.cursor()

bot = telebot.TeleBot(BOT_TOKEN)
subscribers = {}
active_users = {}


@bot.message_handler(commands=['start'])
def start(message):
    select_query = f"""SELECT * FROM users WHERE telegram_id = '{message.from_user.id}'"""
    cursor.execute(select_query, message.from_user.username)
    result1 = cursor.fetchall()
    if not len(result1) > 0:
        insert_query = f""" INSERT INTO users (telegram_id, is_active, first_name, last_name, telegram_name)
         VALUES ({message.from_user.id}, {True}, '{message.from_user.first_name}', '{message.from_user.last_name}',
        '{message.from_user.username}')"""
        cursor.execute(insert_query)
        conn.commit()

    user_id = message.chat.id
    bot.send_message(user_id,
                     "Добро пожаловать! Приятного времяпровождения!")


@bot.message_handler(commands=['deactivate'])
def deactivate(message):
    update_query = f"""UPDATE users SET is_active={False} WHERE telegram_id = {message.from_user.id} """
    cursor.execute(update_query)
    conn.commit()
    bot.send_message(message.from_user.id, 'Вы деактивировали свой аккаунт')


def send_periodic_messages(user_id):
    bot.send_message(user_id, "Здравствуйте, регулярная рассылка для неактивных абонентов")


@bot.message_handler(commands=['stop'])
def stop(message):
    user_id = message.chat.id
    if user_id in subscribers and subscribers[user_id]:
        subscribers[user_id] = False
        bot.send_message(user_id, "Рассылка остановлена.")


@bot.message_handler(commands=['activate'])
def activate(message):
    update_query = f"""UPDATE users SET is_active={True} WHERE telegram_id = {message.from_user.id} """
    cursor.execute(update_query)
    conn.commit()
    bot.send_message(message.from_user.id, 'Вы активировали свой аккаунт')


def job():
    while True:
        check_unactive_users_query = f"""SELECT * FROM users WHERE is_active = {False}"""
        cursor.execute(check_unactive_users_query)
        result = cursor.fetchall()
        for man in result:
            send_periodic_messages(man[1])
        time.sleep(10)


thread = threading.Thread(target=job)
thread.daemon = True
thread.start()

bot.polling()
