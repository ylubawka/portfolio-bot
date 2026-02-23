import telebot
from telebot import types
import sqlite3
from datetime import datetime
import os
import time
from dotenv import load_dotenv

# --- НАСТРОЙКИ ---
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 5593462428

DB_PATH = '/data/database.db' if os.path.exists('/data') else 'database.db'


# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, username TEXT, bots_count INTEGER DEFAULT 0, last_payment TEXT)'''
                   )
    cursor.execute('''CREATE TABLE IF NOT EXISTS reviews 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT, text TEXT, photo_id TEXT, rating INTEGER, date TEXT)'''
                   )

    cursor.execute("PRAGMA table_info(reviews)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'rating' not in columns:
        cursor.execute('ALTER TABLE reviews ADD COLUMN rating INTEGER')

    conn.commit()
    conn.close()


# --- ФУНКЦИЯ ДЛЯ ГЕНЕРАЦИИ КНОПОК (ОБНОВЛЯЕТ МЕНЮ) ---
def get_main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # Если ты добавишь новую кнопку здесь, она обновится у юзера после любого сообщения
    markup.add('📂 Попробовать примеры ботов за 1р', '💰 Купить бота',
               '✨Посмотреть отзывы')
    markup.add('📊 Моя статистика', '🆘 Поддержка')

    if user_id == ADMIN_ID:
        markup.add('⚙️ Админка', '📢 Рассылка')
    return markup


def register_user(message):
    user_id = message.chat.id
    username = message.from_user.username if message.from_user.username else "NoName"
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR IGNORE INTO users (user_id, username, last_payment) VALUES (?, ?, ?)',
        (user_id, username, datetime.now().strftime("%Y-%m-%d")))
    cursor.execute(
        'UPDATE users SET username = ?, last_payment = ? WHERE user_id = ?',
        (username, datetime.now().strftime("%Y-%m-%d"), user_id))
    conn.commit()
    conn.close()


def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT user_id, username, bots_count, last_payment FROM users')
    rows = cursor.fetchall()
    conn.close()
    return rows


# --- КОМАНДА START ---
@bot.message_handler(commands=['start'])
def start(message):
    register_user(message)
    bot.send_message(
        message.chat.id,
        f"Привет! Я <b>ylubawka</b>. Коплю на PS4! 🎮 вместе с сестрой❤️\n\n"
        f"Выбери кнопку в меню, чтобы начать.",
        reply_markup=get_main_keyboard(message.chat.id),
        parse_mode='HTML')


# --- ГЛАВНЫЕ ТЕКСТОВЫЕ КНОПКИ ---
@bot.message_handler(func=lambda message: True)
def main_menu(message):
    register_user(message)
    kb = get_main_keyboard(message.chat.id)

    if message.text == '💰 Купить бота':
        try:
            bot.send_message(
                ADMIN_ID,
                f"🔔 <b>Новая заявка!</b>\nОт: @{message.from_user.username}\nID: <code>{message.chat.id}</code>",
                parse_mode='HTML')
        except:
            pass
        bot.send_message(message.chat.id,
                         "Для заказа бота пиши мне в ЛС: @ylubawka \n\n"
                         "Цена — от 500 руб.\n"
                         "Сервер — 100 руб/неделя.",
                         reply_markup=kb)

    elif message.text == '📂 Попробовать примеры ботов за 1р':
        inline_kb = types.InlineKeyboardMarkup(row_width=1)
        inline_kb.add(
            types.InlineKeyboardButton("🛒 Демо-Магазин",
                                       callback_data="demo_shop"),
            types.InlineKeyboardButton("📈 Демо-Кликер",
                                       callback_data="demo_clicker"),
            types.InlineKeyboardButton("📝 Демо-Анкета",
                                       callback_data="demo_form"))
        bot.send_message(message.chat.id,
                         "Выбери, что хочешь протестировать:",
                         reply_markup=inline_kb)

    elif message.text == '✨Посмотреть отзывы':
        inline_kb = types.InlineKeyboardMarkup(row_width=2)
        inline_kb.add(
            types.InlineKeyboardButton("📖 Читать отзывы",
                                       callback_data="read_0"),
            types.InlineKeyboardButton("✍️ Оставить отзыв",
                                       callback_data="write_review"))
        bot.send_message(message.chat.id,
                         "Наши отзывы:",
                         reply_markup=inline_kb)

    elif message.text == '📊 Моя статистика':
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT bots_count, last_payment FROM users WHERE user_id = ?',
            (message.chat.id, ))
        row = cursor.fetchone()
        conn.close()
        if row:
            bot.send_message(
                message.chat.id,
                f"📊 <b>Статистика:</b>\n🤖 Ботов: {row[0]}\n📅 Активность: {row[1]}",
                parse_mode='HTML',
                reply_markup=kb)

    elif message.text == '🆘 Поддержка':
        bot.send_message(message.chat.id,
                         "Пишите админу: @ylubawka",
                         reply_markup=kb)

    elif message.text == '⚙️ Админка' and message.chat.id == ADMIN_ID:
        inline_kb = types.InlineKeyboardMarkup()
        inline_kb.add(
            types.InlineKeyboardButton("📊 Показать всю базу",
                                       callback_data="view_db"))
        inline_kb.add(
            types.InlineKeyboardButton("➕ Добавить бота юзеру",
                                       callback_data="add_bot_start"))
        bot.send_message(ADMIN_ID,
                         "<b>Панель управления:</b>",
                         reply_markup=inline_kb,
                         parse_mode='HTML')

    elif message.text == '📢 Рассылка' and message.chat.id == ADMIN_ID:
        msg = bot.send_message(ADMIN_ID, "Введите текст сообщения:")
        bot.register_next_step_handler(msg, admin_broadcast)

    else:
        # Если юзер просто что-то написал, обновляем ему меню
        bot.send_message(message.chat.id, "Меню обновлено ✅", reply_markup=kb)


# --- CALLBACK ОБРАБОТЧИК ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    if call.data.startswith("read_"):
        offset = int(call.data.split("_")[1])
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT username, text, photo_id, date, rating FROM reviews ORDER BY id DESC LIMIT 5 OFFSET ?',
            (offset, ))
        rows = cursor.fetchall()
        conn.close()
        if not rows and offset == 0:
            bot.answer_callback_query(call.id, "Отзывов пока нет.")
            return
        for r_name, r_text, r_photo, r_date, r_rating in rows:
            stars = "⭐" * (r_rating if r_rating else 5)
            caption = f"👤 @{r_name} ({r_date})\nОценка: {stars}\n\n«{r_text}»"
            if r_photo:
                bot.send_photo(call.message.chat.id, r_photo, caption=caption)
            else:
                bot.send_message(call.message.chat.id, caption)

        markup = types.InlineKeyboardMarkup()
        if len(rows) == 5:
            markup.add(
                types.InlineKeyboardButton("⬇️ Показать еще",
                                           callback_data=f"read_{offset + 5}"))
        bot.send_message(call.message.chat.id,
                         "--- Конец списка ---",
                         reply_markup=markup)

    elif call.data == "write_review":
        markup = types.InlineKeyboardMarkup(row_width=5)
        btns = [
            types.InlineKeyboardButton(str(i), callback_data=f"rate_{i}")
            for i in range(1, 6)
        ]
        markup.add(*btns)
        bot.send_message(call.message.chat.id,
                         "Оцени работу (1-5 ⭐):",
                         reply_markup=markup)

    elif call.data.startswith("rate_"):
        rating = int(call.data.split("_")[1])
        msg = bot.send_message(
            call.message.chat.id,
            f"Вы выбрали {rating} ⭐. Напишите отзыв или пришлите фото:")
        bot.register_next_step_handler(msg, process_review_step, rating)

    elif call.data == "demo_shop":
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Купить iPhone (0 руб)",
                                       callback_data="shop_confirm"))
        bot.edit_message_text("Пример магазина:",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=markup)

    elif call.data == "shop_confirm":
        bot.answer_callback_query(call.id, "Товар в корзине!", show_alert=True)

    elif call.data == "demo_clicker":
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Клик! ⚡️", callback_data="click_1"))
        bot.edit_message_text("Твой счет: 0",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=markup)

    elif call.data.startswith("click_"):
        count = int(call.data.split("_")[1])
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Клик! ⚡️",
                                       callback_data=f"click_{count+1}"))
        bot.edit_message_text(f"Твой счет: {count}",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=markup)

    elif call.data == "demo_form":
        msg = bot.send_message(call.message.chat.id, "Как тебя зовут?")
        bot.register_next_step_handler(
            msg, lambda m: bot.send_message(m.chat.id, f"Приятно, {m.text}!"))

    elif call.data == "view_db" and call.from_user.id == ADMIN_ID:
        users = get_all_users()
        report = "📋 <b>База:</b>\n"
        for u_id, u_name, b_count, l_pay in users:
            report += f"👤 @{u_name} | ID: <code>{u_id}</code>\n"
        bot.send_message(ADMIN_ID, report, parse_mode='HTML')

    elif call.data == "add_bot_start" and call.from_user.id == ADMIN_ID:
        msg = bot.send_message(ADMIN_ID, "Введите ID пользователя:")
        bot.register_next_step_handler(msg, admin_add_bot_final)


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def process_review_step(message, rating):
    photo_id = None
    text = ""
    if message.content_type == 'photo':
        photo_id = message.photo[-1].file_id
        text = message.caption if message.caption else "Без текста"
    elif message.content_type == 'text':
        text = message.text

    username = message.from_user.username or "Anon"
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO reviews (user_id, username, text, photo_id, rating, date) VALUES (?, ?, ?, ?, ?, ?)',
        (message.chat.id, username, text, photo_id, rating,
         datetime.now().strftime("%d.%m.%Y")))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id,
                     "✅ Отзыв опубликован!",
                     reply_markup=get_main_keyboard(message.chat.id))


def admin_broadcast(message):
    users = get_all_users()
    for user in users:
        try:
            bot.send_message(user[0], message.text)
        except:
            pass
    bot.send_message(ADMIN_ID, "✅ Готово!")


def admin_add_bot_final(message):
    try:
        target_id = int(message.text)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET bots_count = bots_count + 1 WHERE user_id = ?',
            (target_id, ))
        conn.commit()
        conn.close()
        bot.send_message(ADMIN_ID, "✅ Добавлено!")
    except:
        bot.send_message(ADMIN_ID, "Ошибка!")


def run_bot():
    while True:
        try:
            init_db()
            print("Бот в сети!")
            bot.infinity_polling(timeout=20)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)


if __name__ == '__main__':
    run_bot()
