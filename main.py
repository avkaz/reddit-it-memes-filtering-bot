from config import *
from PIL import Image
from telebot import types

# Initialize the Telegram bot
bot = telebot.TeleBot('your_telegram_bot_here', parse_mode='HTML')
print("connected to the bot")

# Setup logging
import logging
logging.basicConfig(filename='bot.log', level=logging.INFO)

# Command handler for /start
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=3)
    btn1 = types.InlineKeyboardButton(text='Мемы', callback_data='memes')
    btn2 = types.InlineKeyboardButton(text='Статистика', callback_data='stat')
    btn3 = types.InlineKeyboardButton(text='Новый пост', callback_data='new_post')
    btn4 = types.InlineKeyboardButton(text='Мемы в очереди', callback_data='queue')
    btn5 = types.InlineKeyboardButton(text='Удаленные мемы', callback_data='deleted_memes')
    markup.add(btn1, btn2, btn3, btn4, btn5)
    bot.send_message(message.from_user.id, "☰ *Menu*", parse_mode="Markdown", reply_markup=markup)

# Callback handler for inline keyboard buttons
@bot.callback_query_handler(func=lambda callback: True)
def callback_worker(callback):
    if callback.data == "memes":
        for i in range(10):
            delete_message(chat_id=callback.message.chat.id, message_id=callback.message.id - i)
        send_meme(callback.message)
    elif callback.data == "in_prod":
        for i in range(10):
            delete_message(chat_id=callback.message.chat.id, message_id=callback.message.id - i)
        in_prod(callback.message)
    elif callback.data == "in_prod_manual":
        for i in range(10):
            delete_message(chat_id=callback.message.chat.id, message_id=callback.message.id - i)
        in_prod_manual(callback.message)
    elif callback.data == "continue":
        for i in range(10):
            delete_message(chat_id=callback.message.chat.id, message_id=callback.message.id - i)
        send_meme(callback.message)
    elif callback.data == "continue_manual":
        for i in range(10):
            delete_message(chat_id=callback.message.chat.id, message_id=callback.message.id - i)
        send_new_post_instructions(callback.message)
    elif callback.data == "skip":
        for i in range(10):
            delete_message(chat_id=callback.message.chat.id, message_id=callback.message.id - i)
        skip_meme(callback.message)
    elif callback.data == "shit":
        for i in range(10):
            delete_message(chat_id=callback.message.chat.id, message_id=callback.message.id - i)
        delete_meme(callback.message)
    elif callback.data == "shit_manual":
        for i in range(10):
            delete_message(chat_id=callback.message.chat.id, message_id=callback.message.id - i)
        show_menu(callback.message)
    elif callback.data == "stop":
        for i in range(50):
            delete_message(chat_id=callback.message.chat.id, message_id=callback.message.id - i)
        show_menu(callback.message)
    elif callback.data == "delete_caption":
        for i in range(10):
            delete_message(chat_id=callback.message.chat.id, message_id=callback.message.id - i)
        delete_caption(callback.message)
    elif callback.data == "stat":
        for i in range(10):
            delete_message(chat_id=callback.message.chat.id, message_id=callback.message.id - i)
        send_statistics(callback.message)
    elif callback.data == "new_post":
        for i in range(10):
            delete_message(chat_id=callback.message.chat.id, message_id=callback.message.id - i)
        send_new_post_instructions(callback.message)
    elif callback.data == "queue":
        for i in range(10):
            delete_message(chat_id=callback.message.chat.id, message_id=callback.message.id - i)
        send_all_memes_in_queue(callback.message)
    elif callback.data == "continue_queue":
        for i in range(10):
            delete_message(chat_id=callback.message.chat.id, message_id=callback.message.id - i)
        continue_with_memes_from_queue(callback.message)
    elif callback.data == "deleted_memes":
        for i in range(10):
            delete_message(chat_id=callback.message.chat.id, message_id=callback.message.id - i)
        send_first_10_deleted_memes(callback.message)
    elif callback.data.startswith("deleteMeme"):
        meme_id = int(callback.data.split("_")[-1])
        handle_meme_to_delete(callback.message, meme_id)
    elif callback.data.startswith("deleteManualMeme"):
        meme_id = int(callback.data.split("_")[-1])
        handle_manual_meme_to_delete(callback.message, meme_id)
    elif callback.data.startswith("deleteCommentFor"):
        meme_id = int(callback.data.split("_")[-1])
        delete_comment_for_meme_in_queue(callback.message, meme_id)
    elif callback.data.startswith("returnBackFromQueue"):
        meme_id = int(callback.data.split("_")[-1])
        move_meme_back_to_menu_from_queue(callback.message, meme_id)
    elif callback.data.startswith("returnBackFromDeleted"):
        meme_id = int(callback.data.split("_")[-1])
        move_meme_back_to_menu_from_deleted(callback.message, meme_id)


# Handle capturing comments
@bot.message_handler(func=lambda message: message.chat.id in states and states[message.chat.id] == 'capture_comment', content_types=['text'])
def handle_comment(message):
    try:
        # Get the comment text from the user
        comment_text = message.text

        # Save the comment to the database
        meme = db_handler.get_meme()
        if meme:
            meme_id = meme.id
            db_handler.set_comment(meme_id, comment_text)

        final_meme = db_handler.get_meme()
        if final_meme:
            url = final_meme.url
            media = download_media(url)

            if media:
                my_comment = final_meme.my_comment

                # Send the final meme with the user's comment
                if isinstance(media, Image.Image):
                    bot.send_photo(message.chat.id, media, caption=my_comment)
                elif isinstance(media, str):  # Assuming video file path
                    bot.send_video(message.chat.id, open(media, 'rb'), caption=my_comment)

                # Send a confirmation message with inline keyboard
                markup = types.InlineKeyboardMarkup(row_width=2)
                btn_1 = types.InlineKeyboardButton(text='Опубликовать', callback_data='in_prod')
                btn_2 = types.InlineKeyboardButton(text='Удалить подпись', callback_data='delete_caption')
                btn_3 = types.InlineKeyboardButton(text='Гавно', callback_data='shit')
                btn_4 = types.InlineKeyboardButton(text='Пропустить', callback_data='skip')
                btn_5 = types.InlineKeyboardButton(text='Стоп', callback_data='stop')
                markup.add(btn_1, btn_2, btn_3, btn_4, btn_5)

                # Delete previous messages
                for i in range(4):
                    try:
                        bot.delete_message(message.chat.id, message.id - i)
                    except Exception as e:
                        logging.error(f"Error deleting message: {e}")

                bot.send_message(message.chat.id, 'Опубликовать?', reply_markup=markup)

        # Clear the state after capturing the comment
        del states[message.chat.id]

    except Exception as e:
        logging.error(f"An error occurred in handle_comment: {e}")

# Handle new post messages
@bot.message_handler(func=lambda message: message.chat.id in states and states[message.chat.id] == 'capture_new_post',content_types=['document', 'photo', 'audio', 'video', 'voice'])
def handle_new_post(message):
    try:
        # Initialize variables for media and text
        my_comment = None
        file_id = None  # Define file_id here

        # Check the content type of the message
        if message.text:
            my_comment = message.text
        elif message.document:
            # Handle document
            file_info = bot.get_file(message.document.file_id)
            file_id = message.document.file_id
            file_path = save_media_file(file_info)
            my_comment = message.caption
        elif message.photo:
            # Handle photo
            file_id = message.photo[-1].file_id  # Use the last photo size
            file_info = bot.get_file(file_id)
            file_path = save_media_file(file_info)
            my_comment = message.caption
        elif message.audio:
            # Handle audio
            file_id = message.audio.file_id
            file_info = bot.get_file(file_id)
            file_path = save_media_file(file_info)
            my_comment = message.caption
        elif message.video:
            # Handle video
            file_id = message.video.file_id
            file_info = bot.get_file(file_id)
            file_path = save_media_file(file_info)
            my_comment = message.caption
        elif message.voice:
            # Handle voice
            file_id = message.voice.file_id
            file_info = bot.get_file(file_id)
            file_path = save_media_file(file_info)
            my_comment = message.caption

        # Save new_post to the database
        db_handler.set_new_post(file_path, my_comment)

        # Create confirmation keyboard
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_1 = types.InlineKeyboardButton(text='Да', callback_data='in_prod_manual')
        btn_2 = types.InlineKeyboardButton(text='Нет', callback_data='shit_manual')
        markup.add(btn_1, btn_2)

        # Send confirmation message with inline keyboard
        bot.send_message(message.chat.id, 'Опубликовать?', reply_markup=markup)

        # Clear the state after capturing the new post
        del states[message.chat.id]

    except Exception as e:
        logging.error(f"An error occurred in handle_new_post: {e}")



# Start the bot
bot.polling(none_stop=True, interval=0)
