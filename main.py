import telebot
import sqlite3
import threading

bot = telebot.TeleBot('6923949475:AAFc-lic9vzAirSUZ7AZAL7EX0VrRoEnvDI')
conn = sqlite3.connect('playlists.db', check_same_thread=False)
cursor = conn.cursor()
lock = threading.Lock()

# Удаляем текущую таблицу, если она существует, и создаем новую
cursor.execute('''
    DROP TABLE IF EXISTS playlists
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS playlists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        playlist_name TEXT,
        playlist_link TEXT
    )
''')

conn.commit()

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "Хой! я метал бот и я могу хранить ссылки на плейлисты. Используй /add_playlist для добавления плейлиста и /show_playlists для просмотра всех плейлистов.")

@bot.message_handler(commands=['add_playlist'])
def handle_add_playlist(message):
    bot.send_message(message.chat.id, "Введите название плейлиста:")
    bot.register_next_step_handler(message, process_add_playlist_name)

def process_add_playlist_name(message):
    user_id = message.from_user.id
    playlist_name = message.text

    bot.send_message(message.chat.id, f"Отлично! Теперь введите ссылку для плейлиста '{playlist_name}':")
    bot.register_next_step_handler(message, process_add_playlist_link, user_id, playlist_name)

def process_add_playlist_link(message, user_id, playlist_name):
    playlist_link = message.text

    with lock:
        cursor.execute('INSERT INTO playlists (user_id, playlist_name, playlist_link) VALUES (?, ?, ?)', (user_id, playlist_name, playlist_link))
        conn.commit()

    bot.send_message(message.chat.id, "Плейлист добавлен успешно!")

@bot.message_handler(commands=['show_playlists'])
def handle_show_playlists(message):
    user_id = message.from_user.id

    with lock:
        cursor.execute('SELECT playlist_name FROM playlists WHERE user_id = ?', (user_id,))
        playlists = cursor.fetchall()

    if not playlists:
        bot.send_message(message.chat.id, "У вас нет сохраненных плейлистов.")
    else:
        keyboard = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        for playlist in playlists:
            keyboard.add(telebot.types.KeyboardButton(playlist[0]))

        bot.send_message(message.chat.id, "Выберите плейлист:", reply_markup=keyboard)
        bot.register_next_step_handler(message, process_send_playlist)

def process_send_playlist(message):
    user_id = message.from_user.id
    selected_playlist_name = message.text

    with lock:
        cursor.execute('SELECT playlist_link FROM playlists WHERE user_id = ? AND playlist_name = ?', (user_id, selected_playlist_name))
        result = cursor.fetchone()

    if result:
        bot.send_message(message.chat.id, f"Вот ваш плейлист '{selected_playlist_name}': {result[0]}")
    else:
        bot.send_message(message.chat.id, "Такого плейлиста нет в вашем списке.")
# Копирование стикеров
@bot.message_handler(content_types=['sticker'])
def handle_sticker(message):
    sticker_id = message.sticker.file_id
    bot.send_sticker(message.chat.id, sticker_id)

if __name__ == "__main__":
    bot.polling()
