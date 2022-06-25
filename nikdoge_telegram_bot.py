import telebot
from libs import nikdoge
from datetime import datetime as dt

# Creating bot instance
bot = telebot.TeleBot(nikdoge.undump_json('nikdoge_bot_settings.json')['TELEGRAM_TOKEN'])

@bot.message_handler(commands=["start","help"])
def start(message, res=False):
    bot.send_message(message.chat.id, 
    """На данный момент этот бот поддерживает только команду /exchange или /обмен
Ввод команды без аргументов вызовет справку по ней"""
    )

@bot.message_handler(commands=["exchange"])
def exchange(message, res=False):
    import georgian_exchange
    analyze = message.text.split('/exchange ',1)
    send_help = False
    if len(analyze)<2:
        send_help = True
    elif 'help' in analyze[1]:
        send_help = True
    else:
        response = georgian_exchange.georgian_exchange(analyze[1])
        bot.send_message(message.chat.id, response)
    if send_help:
        response = 'Georgian exchange\nCommand ' + georgian_exchange.help().replace('georgian_exchange','/exchange')
        bot.send_message(message.chat.id, response)
    return

@bot.message_handler(commands=["обмен"])
def exchange_ru(message, res=False):
    import georgian_exchange
    analyze = message.text.split('/обмен ',1)
    send_help = False
    if len(analyze)<2:
        send_help = True
    elif 'помощь' in analyze[1]:
        send_help = True
    else:
        response = georgian_exchange.georgian_exchange(analyze[1])
        bot.send_message(message.chat.id, response)
    if send_help:
        response = 'Грузинский обменник\nКоманда ' + georgian_exchange.help_ru().replace('georgian_exchange','/обмен')
        bot.send_message(message.chat.id, response)
    return

## Handling text
#@bot.message_handler(content_types=["text"])
#def handle_text(message):
#    bot.send_message(message.chat.id, f'{message.text}? Что бы это могло значить?')

# Launch the bot
start_timestamp = dt.utcnow().isoformat()
print(f'[{start_timestamp}] Starting Nikdoge Telegram bot')
bot.polling(none_stop=True, interval=0)
