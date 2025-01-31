import telebot
from telebot import types
from db_handler import DBHandler
import requests
from PIL import Image
from io import BytesIO
import os
from mimetypes import guess_extension
import logging
import tempfile
import threading
import time
import firebase_admin
from firebase_admin import credentials, storage
from werkzeug.utils import secure_filename

cred = credentials.Certificate("key.json")
firebase_admin.initialize_app(cred, {'storageBucket': 'codereview-22c86.appspot.com'})

bucket = storage.bucket()


bot = telebot.TeleBot('your_telegram_bot_token_here', parse_mode='HTML')


# Get the current working directory
current_directory = os.getcwd()

# Specify the subdirectory for media storage (one directory back)
media_subdir = os.path.join(current_directory, '..')

# Construct the full path to the media directory
media_dir = os.path.join(media_subdir, 'media')

DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_HOST = os.environ.get('DB_HOST')  
DB_PORT = os.environ.get('DB_PORT')       
DB_NAME = os.environ.get('DB_NAME')

# Construct the PostgreSQL database URL
db_url = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# Correct the DBHandler initialization
db_handler = DBHandler(db_url)

# Ensure the directory exists
if not os.path.exists(media_dir):
    os.makedirs(media_dir)

# Function to send a meme
# Define states
states = {}
def send_meme(message):
    stat_values = db_handler.get_short_stat()
    if stat_values is not None:
        memes_toGo, memes_in_queue = stat_values

    try:
        meme = db_handler.get_meme()
        if meme:
            url = meme.url
            if url:
                media = download_media(url)

                if media:
                    rank = meme.rank
                    comments = meme.comments
                    signature = meme.signature
                    my_comment = meme.my_comment
                    posted_when = meme.posted_when

                    # Send meme details and media
                    bot.send_message(message.chat.id,
                                     f'Mемов осталось: {memes_toGo}\nМемы в очереди: {memes_in_queue}\n')
                    bot.send_message(message.chat.id,
                                     f'Posted days ago: {posted_when}\nRank: {rank}\nComments: {comments}\nSignature: {signature}')
                    if my_comment is not None:
                        if isinstance(media, Image.Image):
                            send_media_threaded(bot, message, media, bot.send_photo, caption=my_comment)
                        elif isinstance(media, str):  # Assuming video file path
                            send_media_threaded(bot, message, media, bot.send_video, caption=my_comment)

                        # Send confirmation message with inline keyboard
                        markup = types.InlineKeyboardMarkup(row_width=2)
                        btn_1 = types.InlineKeyboardButton(text='Опубликовать', callback_data='in_prod')
                        btn_2 = types.InlineKeyboardButton(text='Удалить подпись', callback_data='delete_caption')
                        btn_3 = types.InlineKeyboardButton(text='Гавно', callback_data='shit')
                        btn_4 = types.InlineKeyboardButton(text='Пропустить', callback_data='skip')
                        btn_5 = types.InlineKeyboardButton(text='Стоп', callback_data='stop')
                        markup.add(btn_1, btn_2, btn_3, btn_4, btn_5)

                        # Set the state to capture comment
                        states[message.chat.id] = 'capture_comment'

                        bot.send_message(message.chat.id, 'Опубликовать?', reply_markup=markup)

                        # Delete temporary video file after sending
                        if isinstance(media, str) and os.path.exists(media):
                            os.remove(media)
                    else:
                        if isinstance(media, Image.Image):
                            send_media_threaded(bot, message, media, bot.send_photo)
                        elif isinstance(media, str):  # Assuming video file path
                            send_media_threaded(bot, message, media, bot.send_video)

                        # Send confirmation message with inline keyboard
                        markup = types.InlineKeyboardMarkup(row_width=2)
                        btn_1 = types.InlineKeyboardButton(text='Опубликовать', callback_data='in_prod')
                        btn_2 = types.InlineKeyboardButton(text='Гавно', callback_data='shit')
                        btn_3 = types.InlineKeyboardButton(text='Пропустить', callback_data='skip')
                        btn_4 = types.InlineKeyboardButton(text='Стоп', callback_data='stop')
                        markup.add(btn_1, btn_2, btn_3, btn_4)

                        # Set the state to capture comment
                        states[message.chat.id] = 'capture_comment'

                        bot.send_message(message.chat.id, 'Опубликовать?', reply_markup=markup)

                        # Delete temporary video file after sending
                        if isinstance(media, str) and os.path.exists(media):
                            os.remove(media)
                else:
                    delete_meme(message)
            else:
                delete_meme(message)
        else:
            markup = types.InlineKeyboardMarkup(row_width=1)
            btn1 = types.InlineKeyboardButton(text='В Меню', callback_data='stop')
            markup.add(btn1)
            bot.send_message(message.chat.id, 'Извините, но у нас закончились мемы на данный момент.', markup=markup)
    except Exception as e:
        print(f"An error occurred: {e}")


def send_media_threaded(bot, message, media, send_function, **kwargs):
    chat_id = message.chat.id
    thread = threading.Thread(target=send_function, args=(chat_id, media), kwargs=kwargs)
    thread.start()

    # Wait for the thread to finish or timeout after 30 seconds
    thread.join(timeout=30)

    # If the thread is still alive after the timeout, it means it took too long
    if thread.is_alive():
        thread._stop()  # Stop the thread
        print("Timeout occurred while sending media.")
        delete_meme(message)



# Function to download an image from a URL
def download_media(url):
    response = requests.get(url)

    if response.status_code == 200:
        content_type = response.headers.get('content-type')

        if 'image' in content_type:
            # If the content is an image
            image = Image.open(BytesIO(response.content))

            # Convert the image to RGBA if it has transparency in the palette
            if 'transparency' in image.info:
                image = image.convert('RGBA')

            return image

        elif 'video' in content_type:
            # If the content is a video
            file_extension = guess_extension(content_type.split('/')[1])
            file_path = f'temporary_video{file_extension}'

            with open(file_path, 'wb') as video_file:
                video_file.write(response.content)

            return file_path

    return None

# Function to save media file to a specified directory
def save_media_file(file_info):
    logging.info("Media file started saving")
    try:
        # Download file
        downloaded_file = bot.download_file(file_info.file_path)

        # Ensure downloaded_file is bytes-like
        if isinstance(downloaded_file, bytes):
            filename = secure_filename(file_info.file_path.split('/')[-1])  # Get filename from path
            blob = bucket.blob(filename)

            # Upload file to bucket
            try:
                blob.upload_from_string(downloaded_file)
                file_path = blob.name  # Get the path to the object in the blob
                logging.info(f"Media file saved successfully: {file_path}")
                return file_path
            except Exception as upload_error:
                logging.error(f"Error uploading media file to blob: {upload_error}")
                return None

        else:
            logging.error("Error downloading file: Unexpected file format")
            return None

    except Exception as e:
        logging.error(f"Error saving media file: {e}")
        return None

# Function to mark a meme as checked and approved
def in_prod(message):
    meme = db_handler.get_meme()
    if meme:
        meme_id = meme.id
        db_handler.mark_as_checked(meme_id, True)
        db_handler.mark_as_approved(meme_id, True)
        if meme.posted_when == 0  and meme.rank <=50:
            db_handler.modify_stat('+',all_published_count=1, published_suggested_count=1)
        else:
            db_handler.modify_stat('+',all_published_count=1, published_suggested_count=1, rank=meme.rank)

        # Ask the user if they want to continue with more memes
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_1 = types.InlineKeyboardButton(text='Да', callback_data='continue')
        btn_2 = types.InlineKeyboardButton(text='Нет', callback_data='stop')
        markup.add(btn_1, btn_2)

        bot.send_message(message.chat.id, 'Мем добавлен в очередь. Продолжить с мемами?', reply_markup=markup)

#function to mark to prod post, created manualy. Not from suggested reddit db.
def in_prod_manual(message):
    meme = db_handler.get_manual_meme()
    if meme:
        meme_id = meme.id
        db_handler.mark_as_checked(meme_id, True)
        db_handler.mark_as_approved(meme_id, True)
        db_handler.mark_as_published(meme_id, False)
        db_handler.modify_stat('+', all_published_count=1, published_manual_count=1)

        # Ask the user if they want to continue with more memes
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_1 = types.InlineKeyboardButton(text='Да', callback_data='continue_manual')
        btn_2 = types.InlineKeyboardButton(text='Нет', callback_data='stop')
        markup.add(btn_1, btn_2)

        bot.send_message(message.chat.id, 'Пост добавлен в очередь. Он будет опубликован раньше остальных. Добавить еще один пост?', reply_markup=markup)

# function that adds 101 to the load_order. And this meme will appear in 10 memes.
def skip_meme(message):
    meme = db_handler.get_meme()
    if meme:
        meme_id = meme.id
        db_handler.skip_meme(meme_id)

        send_meme(message)

# marks meme to delete
def delete_meme(message):
    meme = db_handler.get_meme()
    if meme:
        meme_id = meme.id
        db_handler.mark_as_checked(meme_id, True)
        db_handler.mark_as_approved(meme_id, False)
        db_handler.modify_stat('+', all_deleted_count=1)

        send_meme(message)

def delete_message(chat_id, message_id):
    try:
        bot.delete_message(chat_id=chat_id, message_id=message_id)
    except telebot.apihelper.ApiException as e:
        if "Message to delete not found" not in str(e):
            pass

def show_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=3)
    btn1 = types.InlineKeyboardButton(text='Мемы', callback_data='memes')
    btn2 = types.InlineKeyboardButton(text='Статистика', callback_data='stat')
    btn3 = types.InlineKeyboardButton(text='Новый пост', callback_data='new_post')
    btn4 = types.InlineKeyboardButton(text='Мемы в очереди', callback_data='queue')
    btn5 = types.InlineKeyboardButton(text='Удаленные мемы', callback_data='deleted_memes')
    markup.add(btn1, btn2, btn3, btn4, btn5)
    bot.send_message(message.chat.id, "☰ Menu", reply_markup=markup)

def delete_caption(message):
    meme = db_handler.get_meme()
    if meme:
        meme_id = meme.id
        db_handler.delete_comment(meme_id)

        send_meme(message)
def send_statistics(message):
    stat_values = db_handler.get_stat()

    if stat_values is not None:
        memes_toGo, memes_in_queue, all_published_count, all_deleted_count, published_suggested_count, published_manual_count, max_rank_of_suggested, min_rank_of_suggested, mean_rank_of_suggested = stat_values

        all_seen_count = all_published_count + all_deleted_count

        if all_seen_count != 0:
            filter_percentage = round(published_suggested_count/(all_seen_count)*100)
        else: filter_percentage = 0
        if all_published_count != 0:
            suggested_memes_percentage = round(published_suggested_count/all_published_count*100)
        else: suggested_memes_percentage = 0

        all_seen_count = all_published_count + all_deleted_count

        markup = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton(text='В Меню', callback_data='stop')
        markup.add(btn1)
        message_text = (
    f'Mемов осталось:                       *{memes_toGo}*\n'
    f'Мемы в очереди:                       *{memes_in_queue}*\n'
    '----------------------------------------------------------------\n'
    f'Всего просмотренно:                *{all_seen_count}*\n'
    f'Всего опубликовано:                *{all_published_count}*\n'
    f'Всего удалено:                            *{all_deleted_count}*\n'
    f'Процент опубликованных:     *{filter_percentage}%*\n'
    f'Опубликовано с реддита:       *{published_suggested_count}*\n'
    f'Опубликовано вручную:          *{published_manual_count}*\n'
    f'Процент с реддита:                   *{suggested_memes_percentage}%*\n'
    f'Максимальный ранг:                *{max_rank_of_suggested}*\n'
    f'Минимальный ранг:                  *{min_rank_of_suggested}*\n'
    f'Средний ранг:                             *{mean_rank_of_suggested}*'
        )

        bot.send_message(message.chat.id, message_text, parse_mode="Markdown", reply_markup=markup)

    else:
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton(text='В Меню', callback_data='stop')
        markup.add(btn1)
        bot.send_message(message.chat.id, "Что-то сломалось", reply_markup=markup)



def send_new_post_instructions(message):
    new_post_instruction_text = "Как будет выглядеть новый пост?"
    # Set the state to capture new_post
    states[message.chat.id] = 'capture_new_post'

    bot.send_message(message.chat.id, new_post_instruction_text)




def send_all_memes_in_queue(message):
    memes = db_handler.get_memes_from_queue()

    if not memes:
        menu_markup = types.InlineKeyboardMarkup(row_width=1)
        menu_btn = types.InlineKeyboardButton(text='В меню', callback_data='stop')
        menu_markup.add(menu_btn)
        bot.send_message(message.chat.id, "Нет мемов в очереди.",
                         reply_markup=menu_markup)
        return

    for meme in memes:
        try:
            if not (meme.file_id or meme.url):
                logging.warning("Meme has no file_id or URL. Cannot post.")
                mark_to_delete(meme.id)
                continue

            if meme.file_id:
                logging.info(f"Found meme with file_id: {meme.file_id}")
                media = meme.file_id
            elif meme.url:
                logging.info(f"Found meme with URL: {meme.url}")
                media = download_media_from_queue(meme.url)

            if not media:
                logging.warning("Error displaying meme: Media not found.")
                bot.send_message(message.chat.id, f"Error displaying meme: Media not found. ID:{meme.id}")
                mark_to_delete(meme.id)
                continue

            caption = meme.my_comment
            markup_with_delete_comment = types.InlineKeyboardMarkup(row_width=2)
            markup_with_back_to_menu = types.InlineKeyboardMarkup(row_width=2)
            markup_only_delete = types.InlineKeyboardMarkup(row_width=1)
            btn1 = types.InlineKeyboardButton(text='Удалить', callback_data=f'deleteMeme_{meme.id}')
            btn2 = types.InlineKeyboardButton(text='Удалить комментарий', callback_data=f'deleteCommentFor_{meme.id}')
            btn3 = types.InlineKeyboardButton(text='Вернуть на доработку', callback_data=f'returnBackFromQueue_{meme.id}')
            btn4 = types.InlineKeyboardButton(text='Удалить', callback_data=f'deleteManualMeme_{meme.id}')
            markup_with_delete_comment.add(btn1, btn2)
            markup_with_back_to_menu.add(btn1, btn3)
            markup_only_delete.add(btn4)

            if media.lower().endswith(('mp4', 'mov', 'avi')):
                send_method = bot.send_video
            else:
                send_method = bot.send_photo

            if meme.rank == 99999:
                blob = bucket.blob(media)  # Assuming `media` is the path or filename in Firebase Storage
                file_data = blob.download_as_bytes()

                # Determine media type

                if caption:
                    send_method(message.chat.id, BytesIO(file_data), caption=caption,
                                reply_markup=markup_only_delete)
                else:
                    send_method(message.chat.id, BytesIO(file_data), reply_markup=markup_only_delete)
            else:
                with open(media, 'rb') as file:
                    if caption:
                        send_method(message.chat.id, file, caption=caption, reply_markup=markup_with_delete_comment)
                    else:
                        send_method(message.chat.id, file, reply_markup=markup_with_back_to_menu)

            logging.info("Displayed successfully.")


        except Exception as e:
            logging.error(f"Error posting meme: {e}")
            bot.send_message(message.chat.id, f"Error displaying meme: {e}. ID:{meme.id}")
            mark_to_delete(meme.id)

    menu_markup = types.InlineKeyboardMarkup(row_width=1)
    menu_btn = types.InlineKeyboardButton(text='В меню', callback_data='stop')
    menu_markup.add(menu_btn)
    bot.send_message(message.chat.id, "Выберите мем для удаления или нажмите 'В меню', чтобы вернуться в меню.",
                     reply_markup=menu_markup)

def send_first_10_deleted_memes(message):
    memes = db_handler.get_deleted_memes()
    print(len(memes))

    if not memes:
        menu_markup = types.InlineKeyboardMarkup(row_width=1)
        menu_btn = types.InlineKeyboardButton(text='В меню', callback_data='stop')
        menu_markup.add(menu_btn)
        bot.send_message(message.chat.id, "Нет удаленных мемов.", reply_markup=menu_markup)
        return

    # Create a persistent inline keyboard
    menu_markup = types.InlineKeyboardMarkup(row_width=1)
    menu_btn = types.InlineKeyboardButton(text='В меню', callback_data='stop')
    menu_markup.add(menu_btn)

    # Send the first 10 deleted memes
    for index, meme in enumerate(memes[:10], start=1):
        try:
            if not (meme.file_id or meme.url):
                logging.warning(f"Meme {meme.id} has no file_id or URL. Cannot post.")
                mark_to_delete(meme.id)
                continue

            if meme.file_id:
                logging.info(f"Found meme with file_id: {meme.file_id}")
                media = meme.file_id
            elif meme.url:
                logging.info(f"Found meme with URL: {meme.url}")
                media = download_media_from_queue(meme.url)

            if not media:
                logging.warning("Error displaying meme: Media not found.")
                bot.send_message(message.chat.id, f"Error displaying meme: Media not found. ID:{meme.id}")
                mark_to_delete(meme.id)
                continue

            caption = meme.my_comment
            markup = types.InlineKeyboardMarkup(row_width=1)
            btn1 = types.InlineKeyboardButton(text='Вернуть на доработку', callback_data=f'returnBackFromDeleted_{meme.id}')
            markup.add(btn1)

            if caption:
                bot.send_photo(message.chat.id, open(media, 'rb'), caption=caption, reply_markup=markup)
            else:
                bot.send_photo(message.chat.id, open(media, 'rb'), reply_markup=markup)

            logging.info(f"Meme {meme.id} displayed successfully.")

        except Exception as e:
            logging.error(f"Error displaying meme {meme.id}: {e}")
            bot.send_message(message.chat.id, f"Error displaying meme {meme.id}: {e}")

    # Send the menu message
    bot.send_message(message.chat.id, "Выберите мем для удаления или нажмите 'В меню', чтобы вернуться в меню.", reply_markup=menu_markup)

def mark_to_delete(meme_id):
    try:
        if meme_id:
            db_handler.mark_as_checked(meme_id, True)
            db_handler.mark_as_approved(meme_id, False)

    except Exception as e:
        logging.error(f"Error marking meme {meme_id} to delete: {e}")


def download_media_from_queue(url):
    try:
        response = requests.get(url)
        content_type = response.headers.get('content-type')

        if response.status_code == 200 and content_type:
            file_extension = guess_extension(content_type.split('/')[1])

            with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as media:
                media.write(response.content)

            return media.name

    except Exception as e:
        logging.error(f"Error downloading media from {url}: {e}")

    return None

def handle_meme_to_delete(message, meme_id):
    try:
        mark_to_delete(int(meme_id))
        db_handler.modify_stat('+', all_deleted_count=1)
        db_handler.modify_stat('-', published_suggested_count=1)

        # Delete only the specific message
        delete_message(chat_id=message.chat.id, message_id=message.id)

    except Exception as e:
        bot.send_message(message.chat.id, f'Произошла ошибка: {e}')

def handle_manual_meme_to_delete(message, meme_id):
    try:
        meme_id = int(meme_id)
        mark_to_delete(meme_id)

        db_handler.modify_stat('+', all_deleted_count=1)



        db_handler.modify_stat('-', published_manual_count=1)


        delete_message(chat_id=message.chat.id, message_id=message.id)

    except Exception as e:
        bot.send_message(message.chat.id, f'Произошла ошибка: {e}')


def delete_comment_for_meme_in_queue(message, meme_id):
    markup_with_add_comment = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton(text='Удалить', callback_data=f'delete_meme_{meme_id}')
    btn3 = types.InlineKeyboardButton(text='Вернуть на доработку', callback_data=f'returnBack_{meme_id}')
    markup_with_add_comment.add(btn1, btn3)

    try:
        db_handler.delete_comment(meme_id)

        # Edit the message caption and set it to an empty string
        bot.edit_message_caption(chat_id=message.chat.id, message_id=message.id, caption="")

        # Edit the message reply markup to update the inline keyboard
        bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=message.id, reply_markup=markup_with_add_comment)
    except Exception as e:
        # Handle the exception
        print(f"Error deleting comment for meme: {e}")

def move_meme_back_to_menu_from_queue(message, meme_id):

    try:
        db_handler.mark_as_checked(meme_id, False)
        db_handler.mark_as_approved(meme_id, False)
        db_handler.set_highest_load_order(meme_id)
        db_handler.modify_stat('-', published_suggested_count=1)

        delete_message(chat_id=message.chat.id, message_id=message.id)
    except Exception as e:
        # Handle the exception
        print(f"Error moving meme back to menu: {e}")

def move_meme_back_to_menu_from_deleted(message, meme_id):

    try:
        db_handler.mark_as_checked(meme_id, False)
        db_handler.mark_as_approved(meme_id, False)
        db_handler.set_highest_load_order(meme_id)
        db_handler.modify_stat('-', all_deleted_count=1)

        delete_message(chat_id=message.chat.id, message_id=message.id)
    except Exception as e:
        # Handle the exception
        print(f"Error moving meme back to menu: {e}")




def continue_with_memes_from_queue(message):
    states[message.chat.id] = 'capture_meme_to_delete'
