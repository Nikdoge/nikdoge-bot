#!/usr/bin/env python3

# bot.py
import discord, asyncio
from libs import nikdoge
from discord.ext import commands
from datetime import datetime as dt
import logging

FFMPEG_EXECUTABLE = nikdoge.undump_json('nikdoge_bot_settings.json')['FFMPEG_EXECUTABLE']#"C:/Program Files/ffmpeg/bin/ffmpeg.exe"
FILENAME_LOG = 'nikdoge_bot.log'

logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s %(name)s[%(levelname)s]: %(message)s',
    handlers = [
        logging.FileHandler(FILENAME_LOG),
        logging.StreamHandler()
    ]
)
log = logging.getLogger('Dogger')
client = commands.Bot(command_prefix='.')

@client.event
async def on_ready():
    log.info(f'{client.user} is connected to the following guilds:')
    for guild in client.guilds:
        log.info(f'{guild.id}: {guild.name}')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('.help3') or message.content.startswith('.nikdogebot') or message.content.startswith('.nikdoge bot'):
        help_text_en = """Nikdoge Bot is only on the start of its way to the bright future, and atm it's pretty dumb
        .help3 .nikdogebot - help on Nikdoge Bot
        .woofe - answers "woofe indeed"
        .rokk - prints rokk ebol
        .zdravstvuite - says Hello in RYTP style in your voice channel
        .georgian - prints georgian letters
        .exchange .обмен - georgian exchange"""
        help_text_ru = """Nikdoge Bot только в начале своего пути к светлому будущему, и пока что весьма мало полезен
        .help3 .nikdogebot - помощь по Nikdoge Bot
        .woofe - отвечает "woofe indeed"
        .rokk - печатает весь рокк ебол
        .zdravstvuite - говорит Здравствуйте в RYTP-манере в твой голосовой канал
        .georgian - печатает грузинский алфавит
        .exchange .обмен - грузинский обменник (без аргументов печатает помощь по команде)"""
        embed=discord.Embed(
            title="Nikdoge Bot help",
            description=help_text_ru,
            color=0xFF5733)
        await message.channel.send(embed=embed)
        return

    if message.content.startswith('.exchange'):
        import georgian_exchange
        analyze = message.content.split('.exchange ',1)
        send_help = False
        if len(analyze)<2:
            send_help = True
        elif 'help' in analyze[1]:
            send_help = True
        else:
            response = georgian_exchange.georgian_exchange(analyze[1])
            await message.channel.send(response)
        if send_help:
            response = 'Georgian exchange\nCommand ' + georgian_exchange.help().replace('georgian_exchange','.exchange')
            embed=discord.Embed(description=response, color=0xFF5733)
            await message.channel.send(embed=embed)
        return

    if message.content.startswith('.обмен'):
        import georgian_exchange
        analyze = message.content.split('.обмен ',1)
        send_help = False
        if len(analyze)<2:
            send_help = True
        elif 'help' in analyze[1]:
            send_help = True
        else:
            response = georgian_exchange.georgian_exchange(analyze[1])
            await message.channel.send(response)
        if send_help:
            response = 'Грузинский обменник\nКоманда ' + georgian_exchange.help_ru().replace('georgian_exchange','.обмен')
            embed=discord.Embed(description=response, color=0xFF5733)
            await message.channel.send(embed=embed)
        return

    if message.content.startswith('.woofe'):
        response = 'woofe indeed'
        await message.channel.send(response)
        return

    if message.content.startswith('.rokk'):
        response = '''
        Р О К К
        Е Б О Л
        М У П Ю
        О В И Ч
        Н И R Е
        Т👠🔑Й
        '''
        await message.channel.send(response)
        return

    if message.content.startswith('.zdravstvuite'):
        log.info('zdravstvuite called')
        user = message.author
        # only play music if user is in a voice channel
        if user.voice != None:
            voice_channel=user.voice.channel
            # grab user's voice channel
            log.info(f"{message.created_at.isoformat()}: {user.nick} in {voice_channel.name}")
            # create StreamPlayer
            vc = await voice_channel.connect()
            vc.play(discord.FFmpegPCMAudio(source='zdravstvuite.mp3', executable=FFMPEG_EXECUTABLE), after=lambda e: log.info('done', e))
            while vc.is_playing():
                await asyncio.sleep(1)
            # disconnect after the player has finished
            vc.stop()
            await vc.disconnect()
        else:
            await log.info(f"{message.created_at.isoformat()}: {user.nick} not in voice channel")
        return

    if message.content.startswith('.georgian'):
        response = '''Ა а, Ბ б, Გ г, Დ д, Ე э, Ვ в, Ზ з, Თ т, Ი и, Კ к', Ლ л, Მ м, Ნ н, Ო о, Პ п', Ჟ ж, Რ р, Ს с, Ტ т', Უ у, Ფ п, Ქ к, Ღ гх, Ყ кх, Შ ш, Ჩ ч, Ც ц, Ძ дз, Წ ц', Ჭ ч', Ხ хъ, Ჯ дж, Ჰ х'''
        await message.channel.send(response)
        return


log.info('Starting Nikdoge Discord bot')
client.run(nikdoge.undump_json('nikdoge_bot_settings.json')['DISCORD_TOKEN'])
