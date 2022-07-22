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

@bot.message_handler(commands=["exchange"])
def exchange(message, res=False):
    analyze = message.text.split('/exchange ',1)
    send_help = False
    if len(analyze)<2:
        send_help = True
    elif 'help' in analyze[1]:
        send_help = True
    else:
        response = exch.georgian_exchange(analyze[1])
        bot.send_message(message.chat.id, response)
    if send_help:
        response = 'Georgian exchange\nCommand ' + exch.help().replace('georgian_exchange','/exchange')
        bot.send_message(message.chat.id, response)
    return

@bot.message_handler(commands=["обмен"])
def exchange_ru(message, res=False):
    analyze = message.text.split('/обмен ',1)
    send_help = False
    if len(analyze)<2:
        send_help = True
    elif 'помощь' in analyze[1]:
        send_help = True
    else:
        response = exch.georgian_exchange(analyze[1])
        bot.send_message(message.chat.id, response)
    if send_help:
        response = 'Грузинский обменник\nКоманда ' + exch.help_ru().replace('georgian_exchange','/обмен')
        bot.send_message(message.chat.id, response)
    return

## Handling text
#@bot.message_handler(content_types=["text"])
#def handle_text(message):
#    bot.send_message(message.chat.id, f'{message.text}? Что бы это могло значить?')

# Launch the bot
log.info('Starting Nikdoge Telegram bot')
while True:
    try:
        bot.polling(none_stop=True, interval=0)
    except requests.exceptions.ReadTimeout:
        log.info("requests.exceptions.ReadTimeout exception happened")
        time.sleep(10)
        pass
