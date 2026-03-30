import telebot
import psycopg2
import os
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# ---------------- CONFIG ----------------

TOKEN = "8647557552:AAEYbCBHPD6gdt4Zy2wlJzQSiTw9oYGdelY"
ADMIN_ID = 8648483733  # put your telegram id here
DATABASE_URL = os.getenv("DATABASE_URL")

bot = telebot.TeleBot(TOKEN)

# ---------------- DATABASE ----------------

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id BIGINT PRIMARY KEY
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS media(
    id SERIAL PRIMARY KEY,
    media_type TEXT,
    file_id TEXT
);
""")

conn.commit()

# ---------------- ADMIN PANEL ----------------

def admin_keyboard():

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(
        KeyboardButton("📊 Statistics"),
        KeyboardButton("📢 Broadcast")
    )

    kb.add(
        KeyboardButton("📤 Forward Media"),
        KeyboardButton("👥 Users")
    )

    return kb


# ---------------- START ----------------

@bot.message_handler(commands=['start'])
def start(message):

    user_id = message.from_user.id

    cursor.execute(
        "INSERT INTO users(user_id) VALUES(%s) ON CONFLICT DO NOTHING",
        (user_id,)
    )

    conn.commit()

    # ADMIN START
    if user_id == ADMIN_ID:

        bot.send_message(
            message.chat.id,
            "✅ Admin access granted"
        )

        bot.send_message(
            message.chat.id,
            "🔐 Admin Panel",
            reply_markup=admin_keyboard()
        )

        return

    # USER START
    bot.send_message(
        message.chat.id,
        "👋 Welcome!\n\nSend any media and I will resend it anonymously."
    )


# ---------------- STATISTICS ----------------

@bot.message_handler(func=lambda m: m.text == "📊 Statistics")
def stats(message):

    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM media")
    media = cursor.fetchone()[0]

    bot.send_message(
        message.chat.id,
        f"📊 Bot Statistics\n\n👥 Users: {users}\n📤 Media Saved: {media}"
    )


# ---------------- USER COUNT ----------------

@bot.message_handler(func=lambda m: m.text == "👥 Users")
def users_count(message):

    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    bot.send_message(message.chat.id, f"👥 Total Users: {users}")


# ---------------- BROADCAST ----------------

broadcast_mode = False

@bot.message_handler(func=lambda m: m.text == "📢 Broadcast")
def broadcast_start(message):

    global broadcast_mode

    if message.from_user.id != ADMIN_ID:
        return

    broadcast_mode = True

    bot.send_message(message.chat.id, "Send the message to broadcast.")


@bot.message_handler(func=lambda m: broadcast_mode and m.from_user.id == ADMIN_ID)
def send_broadcast(message):

    global broadcast_mode

    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    sent = 0

    for user in users:

        try:
            bot.send_message(user[0], message.text)
            sent += 1
        except:
            pass

    broadcast_mode = False

    bot.send_message(message.chat.id, f"✅ Broadcast sent to {sent} users.")


# ---------------- MEDIA HANDLER ----------------

@bot.message_handler(content_types=[
    'photo','video','document','audio',
    'voice','sticker','animation','video_note'
])
def relay_media(message):

    chat_id = message.chat.id

    try:

        if message.photo:
            file_id = message.photo[-1].file_id
            bot.send_photo(chat_id, file_id)
            media_type = "photo"

        elif message.video:
            file_id = message.video.file_id
            bot.send_video(chat_id, file_id)
            media_type = "video"

        elif message.document:
            file_id = message.document.file_id
            bot.send_document(chat_id, file_id)
            media_type = "document"

        elif message.audio:
            file_id = message.audio.file_id
            bot.send_audio(chat_id, file_id)
            media_type = "audio"

        elif message.voice:
            file_id = message.voice.file_id
            bot.send_voice(chat_id, file_id)
            media_type = "voice"

        elif message.animation:
            file_id = message.animation.file_id
            bot.send_animation(chat_id, file_id)
            media_type = "animation"

        elif message.sticker:
            file_id = message.sticker.file_id
            bot.send_sticker(chat_id, file_id)
            media_type = "sticker"

        elif message.video_note:
            file_id = message.video_note.file_id
            bot.send_video_note(chat_id, file_id)
            media_type = "video_note"

        else:
            return

        # save media
        cursor.execute(
            "INSERT INTO media(media_type,file_id) VALUES(%s,%s)",
            (media_type, file_id)
        )

        conn.commit()

        bot.delete_message(chat_id, message.message_id)

    except Exception as e:
        print(e)


# ---------------- RUN BOT ----------------

print("Bot running...")
bot.infinity_polling()
