import base64
from pathlib import Path
import telebot
from my_token import TOKEN
import sqlite3

bot = telebot.TeleBot(TOKEN)

con = sqlite3.connect('models.db', check_same_thread=False)
cur = con.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS models (
id VARCHAR(256),
username VARCHAR(256),
'name' VARCHAR(256),
age VARCHAR(256),
height VARCHAR(256),
measurement VARCHAR(256),
city VARCHAR(256),
instagran VARCHAR(256),
contact VARCHAR(256))
""")

cur.execute("""CREATE TABLE IF NOT EXISTS pictures (
id VARCHAR(256),
picture BLOB,
caption VARCHAR(256))
""")


@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, f'Привет!\n'
                          f'На связи агентство Genom Management.\n'
                          f'Если хочешь попасть в нашу семью и стать моделью - заполни анкету по ссылке '
                          f'/become_a_model')


@bot.message_handler(commands=['become_a_model'])
def main(message):
    msg = bot.send_message(message.chat.id, 'Спасибо, что решил(а) заполнить анкету!\nКак тебя зовут?')
    bot.register_next_step_handler(msg, fio_step)


def fio_step(message):
    user_info = {}
    user_info['id'] = str(message.from_user.id)
    user_info['username'] = str(message.from_user.username)
    user_info['name'] = message.text
    msg = bot.send_message(message.chat.id, 'Сколько тебе лет?')
    bot.register_next_step_handler(msg, age_step, user_info)


def age_step(message, user_info):
    user_info['age'] = message.text
    msg = bot.send_message(message.chat.id, 'Введи cвой рост')
    bot.register_next_step_handler(msg, height_step, user_info)


def height_step(message, user_info):
    user_info['height'] = message.text
    msg = bot.send_message(message.chat.id, 'Введи cвои параметры в формате:\n'
                                            'обхваты груди-талии-бедер\n'
                                            'Например: 85-60-89')
    bot.register_next_step_handler(msg, measurements_step, user_info)


def measurements_step(message, user_info):
    user_info['measurements'] = message.text
    msg = bot.send_message(message.chat.id, 'Введи, пожалуйста, cвой город')
    bot.register_next_step_handler(msg, city_step, user_info)


def city_step(message, user_info):
    user_info['city'] = message.text
    msg = bot.send_message(message.chat.id, 'Введи ник своего инстаграма.\n'
                                            'Если инстграма нет - поставь прочерк')
    bot.register_next_step_handler(msg, instagram_step, user_info)


def instagram_step(message, user_info):
    user_info['instagram'] = message.text
    msg = bot.send_message(message.chat.id, 'Введи cвой ник в телеграме или номер телефона, чтобы мы могли с тобой связаться)')
    bot.register_next_step_handler(msg, contact_step, user_info)


def contact_step(message, user_info):
    user_info['contact'] = message.text

    cur.execute("DELETE FROM models WHERE id = ?", (user_info['id'], ))

    bot.send_message(message.chat.id, 'Спасибо, что заполнил(а) анкету, остался последний шаг.\n'
                                      'Отправь нам несколько фотографий своего лица без макияжа с естественным освещением.\n'
                                      'Вот примеры фото:')
    photo = open('1.jpg', 'rb')
    bot.send_photo(message.chat.id, photo)
    photo.close()
    photo = open('2.jpg', 'rb')
    bot.send_photo(message.chat.id, photo)
    photo.close()
    photo = open('3.jpg', 'rb')
    bot.send_photo(message.chat.id, photo)
    photo.close()
    photo = open('4.jpg', 'rb')
    bot.send_photo(message.chat.id, photo)
    photo.close()
    photo = open('5.jpg', 'rb')
    bot.send_photo(message.chat.id, photo)
    photo.close()

    data = []
    for c in user_info.values():
        data.append(c)

    cur.execute("INSERT INTO models VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
    con.commit()


@bot.message_handler(content_types=['photo'])
def save_photo(message):

    Path(f'files/{message.chat.id}/photos').mkdir(parents=True, exist_ok=True)

    file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    src = f'files/{message.chat.id}/' + file_info.file_path
    with open(src, 'wb') as new_file:
        new_file.write(downloaded_file)

    with open(f'files/{message.chat.id}/' + file_info.file_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())

    cur.execute('INSERT INTO pictures VALUES (?, ?, ?)', (message.chat.id, encoded_string, str(message.caption)))
    con.commit()

    cur.execute("""SELECT * FROM models WHERE id = ?""", (message.from_user.id, ))
    a = cur.fetchall()
    info = ''
    for tpl in a:
        for c in tpl:
            info += c + '\n'

    bot.send_message('284868574', info)
    flag = True
    n = -1
    while flag:
        n += 1
        try:
            photo = open(f'files/{message.chat.id}/photos/file_{n}.jpg', "rb")
            bot.send_photo('284868574', photo)
            photo.close()
        except Exception:
            flag = False

    bot.send_message(message.chat.id, 'Спасибо! Мы получили твою анкету и скоро с тобой свяжемся.')


bot.polling()
con.close()
