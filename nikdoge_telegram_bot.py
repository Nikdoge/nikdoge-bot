import telebot
import requests
import time
from libs import nikdoge
from datetime import datetime as dt
import logging
import exchange_handler

FILENAME_LOG = 'nikdoge_bot.log'

logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s %(name)s[%(levelname)s]: %(message)s',
    handlers = [
        logging.FileHandler(FILENAME_LOG),
        logging.StreamHandler()
    ]
)
log = logging.getLogger('Telegram bot')
bot = telebot.TeleBot(nikdoge.undump_json('nikdoge_bot_settings.json')['TELEGRAM_TOKEN']) # Creating bot instance
exch = exchange_handler.Exchange()

@bot.message_handler(commands=["start","help"])
def start(message, res=False):
    bot.send_message(message.chat.id, 
    """На данный момент этот бот поддерживает только команду /exchange или /обмен
Ввод команды без аргументов вызовет справку по ней"""
    )

@bot.message_handler(commands=["exchange","обмен"])
def exchange(message, res=False):
    analyze_list = message.text.split(' ')
    response = None
    send_help = False
    lang = 'ru' if analyze_list[0] == '/обмен' else 'en'
    analyze = ' '.join(analyze_list[1:])

    if len(analyze_list) < 2:
        if message.chat.type == "private":
            # should handle input string separately
            send_help = True #temp
        else:
            send_help = True
    elif 'help' in analyze_list or 'помощь' in analyze_list:
        send_help = True
    else:
        response = exch.exchange_handler(analyze)

    if send_help:
        if lang == 'ru':
            response = 'Грузинский обменник\nКоманда ' + exch.help_ru().replace('exchange_handler','/обмен')
        else:
            response = 'Georgian exchange\nCommand ' + exch.help().replace('exchange_handler','/exchange')

    bot.send_message(message.chat.id, response)
    return

# Launch the bot
log.info('Starting Nikdoge Telegram bot')
while True:
    try:
        bot.polling(none_stop=True, interval=0)
    except requests.exceptions.ReadTimeout:
        log.info("requests.exceptions.ReadTimeout exception happened")
        time.sleep(10)
        pass
    else:
        log.info('Breaking from loop')
        break
