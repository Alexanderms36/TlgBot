import telebot
import sqlite3
import re
from telebot import types
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from settings import SETTINGS, updateSettings


json_dict = updateSettings()
token = json_dict.get('token')
admin_chatid = json_dict.get('admin_chatid')
bot = telebot.TeleBot(token)
DB = sqlite3.connect('db/database', check_same_thread=False)
cursor = DB.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS users
                  (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, surname TEXT, patronymic TEXT, birthdate TEXT, phone TEXT,
                is_admin INTEGER, is_confirmed INTEGER)''')
DB.commit()
user_counter = 0
admin = 0

# Обработчик команды /start (регистрация пользователя)
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет! Я бот ОСО. Давай сперва зарегистрируемся")
    bot.send_message(message.chat.id, "Как тебя зовут? Напиши фамилию имя и отчество через пробел")
    # Обработчик текстовых сообщений
    @bot.message_handler(content_types=['text'])
    def get_text_messages(message):
        date_pattern = r"\b\d{2}\.\d{2}\.\d{4}\b"
        name_pattern = r"^[А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]*$"
        #ХИХИХ НЕТ У МКЕЯ ДАТЫ
        # привет я Дима 06.02.2004
        resultName = re.search(name_pattern, message.text)
        resultDate = re.search(date_pattern, message.text)

        if resultName:
            name, surname, patronymic = message.text.split(" ")
            cursor.execute("INSERT INTO users (user_id, name, surname, patronymic) VALUES (?, ?, ?, ?)",
                       (message.chat.id, name, surname, patronymic))
        
            DB.commit()
            bot.send_message(message.chat.id, 'Введи дату рождения в формате ДД.ММ.ГГГГ')

        elif resultDate:
            cursor.execute("UPDATE users SET birthdate = ? WHERE user_id = ?",
                           (message.text, message.chat.id))
            DB.commit()
            request_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            phone_button = KeyboardButton(text="Отправить номер телефона", request_contact=True)
            request_keyboard.add(phone_button)
            bot.send_message(message.chat.id, 'Нажми на кнопку, чтобы отправить свой номер телефона', reply_markup=request_keyboard)

            @bot.message_handler(content_types=['contact'])
            def handle_contact(message):
                phone_number = message.contact.phone_number
                cursor.execute("UPDATE users SET phone = ?, is_confirmed = ? WHERE user_id = ?",
                            (phone_number, 0, message.chat.id))
                
                if(message.chat.id == admin_chatid):
                    admin = 1
                    cursor.execute("UPDATE users SET is_admin = ? WHERE user_id = ?",
                                   (admin, message.chat.id))
                    
                DB.commit()
                bot.send_message(message.chat.id, 'Спасибо, ожидайте ответа в ближайшее время!', reply_markup=ReplyKeyboardRemove())
                return
        else:
            bot.send_message(message.chat.id, 'Некорректный ввод!')
        return
    return

def get_is_confirmed(user_id):
    with DB:
        cursor = DB.cursor()
        cursor.execute("SELECT is_confirmed FROM users WHERE user_id = ?", (user_id,))
        is_confirmed = cursor.fetchone()[0]
    return is_confirmed

def getter(table_name):
    with DB:
        cursor = DB.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
    return rows

def printPretend(n):
    rows = getter("users")
    text = rows[n][2] + " " + rows[n][3] + " " + rows[n][4] + " " + rows[n][5] 
    return text

def defineID(i):
    rows = getter("users")
    tgid = rows[i][1]
    return tgid
# Админ
def addUser(i):
    user_id = defineID(i)
    with DB:
        cursor = DB.cursor()
        cursor.execute("UPDATE users SET is_confirmed = ? WHERE user_id = ?", (1, user_id))
        bot.send_message(user_id, "Вы успешно добавлены в пользователи!")
    DB.commit()

@bot.message_handler(commands=['admin'])
def button_message(message):
    if message.chat.id == admin_chatid:
        markup = telebot.types.InlineKeyboardMarkup()
        item1 = telebot.types.InlineKeyboardButton("Активисты", callback_data = 'activists')
        item2 = telebot.types.InlineKeyboardButton("Рейтинг", callback_data = 'rating')
        markup.add(item1, item2)
        bot.send_message(message.chat.id, "Выберите действие", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Вы не администратор!")

markup = telebot.types.InlineKeyboardMarkup()
itemadd = telebot.types.InlineKeyboardButton('Принять', callback_data='accept')
itemdeny = telebot.types.InlineKeyboardButton('Отменить', callback_data='deny')


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    global user_counter
    global markup, itemadd, itemdeny
    if call.data == "activists":
        markup.add(itemadd, itemdeny)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=printPretend(i), reply_markup=markup)
    elif call.data == "rating":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="RARRR")
    elif call.data == "accept":
        addUser(user_counter)
        user_counter += 1
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=printPretend(i), reply_markup=markup)
    elif call.data == "deny":
        user_counter += 1
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=printPretend(i), reply_markup=markup)
    bot.answer_callback_query(callback_query_id=call.id)

#USER 
@bot.message_handler(commands=['menu'])
def menu(message):
    if get_is_confirmed(message.chat.id) == 1:
        markup = telebot.types.InlineKeyboardMarkup()
        item1 = telebot.types.InlineKeyboardButton("Мои активности", callback_data = 'my_activities')
        item2 = telebot.types.InlineKeyboardButton("Общий Рейтинг", callback_data = 'rating')
        markup.add(item1, item2)
        bot.send_message(message.chat.id, "Выберите действие", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Вы не находитесь в списке пользователей")

@bot.message_handler(commands=['button'])
def button_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Начать")
    markup.add(item1)
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)





bot.infinity_polling()