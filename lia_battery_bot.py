import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

# Токен бота
API_TOKEN = '7920642202:AAEADufPJOoagFF2_6aWojFEseGmKK_haD4'
bot = telebot.TeleBot(API_TOKEN)

# ID группы администраторов
ADMIN_GROUP_ID = '-1002307809231'
user_data = {}
current_question = {}

# Вопросы для анкеты
questions = [
    ("Тип электротехники",
     ["Погрузчик", "Штабелер", "Ричтрак", "УПШ", "Подъёмник ножничный", "Тележка", "Паллето-перевозчик", "Другое"]),
    ("Давайте заполним основные характеристики вашей АКБ. Часть информации можно найти на шильдике - табличке которая обычно находится с торца корпуса АКБ. Укажите пожалуйста ëмкость (A/h)", []),
    ("Напряжение", ["24V", "48V", "72V", "80V"]),
    ("Габариты: введите значения ДхШхВ в мм", []),
    ("Напряжение зарядного устройства?", ["220V", "380V"]),
    ("Когда была приобретена техника?", ["Меньше года", "1-3 года", "Больше 3 лет"]),
    ("Режим работы склада?", ["1 смена", "2 смены", "3 смены"]),
    ("Перерывы, пересменки", ["1 час", "2 часа", "Без перерывов"]),
    ("Часы работы АКБ за смену?", ["Менее 4 часов", "4-8 часов", "Более 8 часов"]),
    ("Температура на складе?", ["Холодно", "Тепло", "Работает на улице"]),
    ("Когда планируется замена АКБ?", ["В ближайшие 3 месяца", "Через 6 месяцев", "Не планирую"]),
    ("Критерии выбора поставщика", ["Цена", "Гарантия", "Сроки поставки", "Удалённость"]),
    ("Сколько батарей с такими характеристиками нужно?", []),
    ("Укажите ИНН и название вашей компании", []),
    ("Батарею приобретаете для себя?", ["Для себя", "Дилер"]),
    ("Укажите ваш контактный телефон", []),
    ("Email", []),
    ("Приоритетный способ отправки КП", ["WhatsApp", "Email", "Telegram"]),
    ("Когда с вами можно связаться и уточнить информацию по рассмотрению КП.", ["Через 2-3 дня", "Через неделю", "Через месяц"]),
    ("Время по МСК?", ["Утро 10:00-12:00", "День 13:00-15:00", "Вечер 15:00-17:00"])
]


# Функция создания клавиатуры с вариантами ответов
def create_keyboard(options):
    if not options:
        return None
    markup = InlineKeyboardMarkup(row_width=3)
    buttons = [InlineKeyboardButton(opt, callback_data=opt) for opt in options]
    markup.add(*buttons)
    return markup


# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    begin_survey(message.chat.id)


# Начало опроса
def begin_survey(chat_id):
    user_data[chat_id] = {}
    current_question[chat_id] = 0
    bot.send_message(chat_id, questions[0][0], reply_markup=create_keyboard(questions[0][1]))


# Обработчик ответов с кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    q_index = current_question.get(chat_id, 0)
    user_data[chat_id][questions[q_index][0]] = call.data

    # Отображение ответа пользователя в чате
    bot.send_message(chat_id, f"Ваш ответ: {call.data}")

    q_index += 1
    if q_index < len(questions):
        current_question[chat_id] = q_index
        bot.send_message(chat_id, questions[q_index][0], reply_markup=create_keyboard(questions[q_index][1]))
    else:
        send_application(chat_id, call.from_user)


# Обработчик текстовых ответов
@bot.message_handler(content_types=['text'])
def handle_text(message: Message):
    chat_id = message.chat.id
    text = message.text.strip()

    if text.lower() == "нужна акб":
        begin_survey(chat_id)
        return

    q_index = current_question.get(chat_id, 0)
    if q_index >= len(questions):
        return

    user_data[chat_id][questions[q_index][0]] = text
    bot.send_message(chat_id, f"Вы ответили: {text}")  # Отображаем ответ

    q_index += 1
    current_question[chat_id] = q_index
    if q_index < len(questions):
        bot.send_message(chat_id, questions[q_index][0], reply_markup=create_keyboard(questions[q_index][1]))
    else:
        send_application(chat_id, message.from_user)


# Отправка заявки администратору
def send_application(chat_id, user):
    report = f"Заявка от @{user.username} ({user.id}):\n"
    report += "\n".join([f"{q}: {user_data[chat_id][q]}" for q in user_data[chat_id]])
    bot.send_message(ADMIN_GROUP_ID, report)
    bot.send_message(chat_id,
                     "Спасибо! В течение 10 минут пришлём КП. Вы можете прикрепить фото шильдика с мотора и текущей АКБ, так же можете прислать чертёж батареи (при наличии). Чтобы заполнить новую заявку, отправьте сообщение 'Нужна АКБ'.")
    user_data.pop(chat_id, None)
    current_question.pop(chat_id, None)


# Обработка загруженных фото
@bot.message_handler(content_types=['photo'])
def handle_photo(message: Message):
    chat_id = message.chat.id
    photo_id = message.photo[-1].file_id
    bot.send_photo(ADMIN_GROUP_ID, photo_id, caption=f"Фото шильдика от @{message.from_user.username}")
    bot.send_message(chat_id, "Фото получено!")


# Запуск бота
if __name__ == '__main__':
    bot.polling(none_stop=True)
