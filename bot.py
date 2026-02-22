import telebot
from telebot import types
import sqlite3
from datetime import datetime
import os

# Твой токен и ID
load_dotenv()

# Получаем токен
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5593462428 

# --- НАСТРОЙКА ПУТИ БАЗЫ ДАННЫХ ---
# Если папка /data существует (на сервере), пишем туда. Если нет (локально) — в текущую папку.
DB_PATH = '/data/database.db' if os.path.exists('/data') else 'database.db'

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, 
                       username TEXT, 
                       bots_count INTEGER DEFAULT 0, 
                       last_payment TEXT)''')
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, bots_count, last_payment FROM users')
    rows = cursor.fetchall()
    conn.close()
    return rows

# --- СТАРТ ---
@bot.message_handler(commands=['start'])
def start(message):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    username = message.from_user.username if message.from_user.username else "NoName"
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username, last_payment) VALUES (?, ?, ?)', 
                   (message.chat.id, username, datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('📂 Попробовать примеры ботов за 1р', '💰 Купить бота')
    if message.chat.id == ADMIN_ID:
        markup.add('⚙️ Админка')

    bot.send_message(message.chat.id, 
                     f"Привет! Я <b>ylubawka</b>. Коплю на PS4! 🎮 вместе с сестрой❤️\n\n"
                     f"Выбери кнопку в меню, чтобы начать.\n\n"
                     f"Если хочешь заказать бота, жми '💰 Купить бота'.\n\n"
                     f"Если хочешь увидеть примеры, жми '📂 Попробовать примеры ботов за 1р'.",
                     reply_markup=markup, parse_mode='HTML')

# --- КУПИТЬ БОТА ---
@bot.message_handler(func=lambda message: message.text == '💰 Купить бота')
def buy_handler(message):
    try:
        bot.send_message(ADMIN_ID, f"🔔 <b>Новая заявка!</b>\nОт: @{message.from_user.username}\nID: <code>{message.chat.id}</code>", parse_mode='HTML')
    except:
        print("Ошибка: Админ (ты) еще не запустил бота!")

    bot.send_message(message.chat.id, "Для заказа бота пиши мне в ЛС: @ylubawka \n\n"
                                      "Цена — от 500 руб.\n"
                                      "Сервер — 100 руб/неделя."
                                      "\n\n Цена изменяется в зависимости от бота, если тебе нужен бот с простыми функциями, то цена может быть ниже.")

# --- ПРИМЕРЫ ---
@bot.message_handler(func=lambda message: message.text == '📂 Попробовать примеры ботов за 1р')
def examples_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🛒 Демо-Магазин", callback_data="demo_shop"),
        types.InlineKeyboardButton("📈 Демо-Кликер", callback_data="demo_clicker"),
        types.InlineKeyboardButton("📝 Демо-Анкета", callback_data="demo_form")
    )
    bot.send_message(message.chat.id, "Выбери, что хочешь протестировать:", reply_markup=markup)

# --- АДМИНКА ---
@bot.message_handler(func=lambda message: message.text == '⚙️ Админка' and message.chat.id == ADMIN_ID)
def admin_panel(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📊 Показать всю базу", callback_data="view_db"))
    markup.add(types.InlineKeyboardButton("➕ Добавить бота юзеру", callback_data="add_bot_start"))
    bot.send_message(ADMIN_ID, "<b>Панель управления для ylubawka:</b>", reply_markup=markup, parse_mode='HTML')

# --- CALLBACKS ---
@bot.callback_query_handler(func=lambda call: True)
def callback_all(call):
    if call.data == "demo_shop":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Купить iPhone (0 руб)", callback_data="shop_confirm"))
        bot.edit_message_text("Пример магазина. Нажми кнопку для покупки:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "shop_confirm":
        bot.answer_callback_query(call.id, "Товар в корзине!", show_alert=True)
    
    elif call.data == "demo_clicker":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Клик! ⚡️", callback_data="click_1"))
        bot.edit_message_text("Твой счет: 0", call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data.startswith("click_"):
        count = int(call.data.split("_")[1])
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Клик! ⚡️", callback_data=f"click_{count+1}"))
        bot.edit_message_text(f"Твой счет: {count}", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "demo_form":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "Как тебя зовут? (Демо сбора данных)")
        bot.register_next_step_handler(msg, lambda m: bot.send_message(m.chat.id, f"Приятно, {m.text}! Так бот собирает данные."))

    elif call.data == "view_db" and call.from_user.id == ADMIN_ID:
        users = get_all_users()
        report = "📋 <b>База:</b>\n"
        for u_id, u_name, b_count, l_pay in users:
            report += f"👤 @{u_name} | ID: <code>{u_id}</code> | Ботов: {b_count}\n"
        bot.send_message(ADMIN_ID, report, parse_mode='HTML')

    elif call.data == "add_bot_start" and call.from_user.id == ADMIN_ID:
        msg = bot.send_message(ADMIN_ID, "Введите ID пользователя:")
        bot.register_next_step_handler(msg, admin_add_bot_final)

def admin_add_bot_final(message):
    try:
        target_id = int(message.text)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET bots_count = bots_count + 1, last_payment = ? WHERE user_id = ?', 
                       (datetime.now().strftime("%Y-%m-%d"), target_id))
        conn.commit()
        conn.close()
        bot.send_message(ADMIN_ID, "✅ Успешно добавлено!")
        bot.send_message(target_id, "🎁 ylubawka добавил вам бота!")
    except:
        bot.send_message(ADMIN_ID, "Ошибка! Вводи цифры ID.")

# --- ЗАПУСК ---
if __name__ == '__main__':
    init_db()
    print(f"Бот ylubawka готов! База данных: {DB_PATH}")
    bot.infinity_polling()

