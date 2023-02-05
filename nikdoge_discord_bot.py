#!/usr/bin/env python3

import discord
import asyncio
from libs import nikdoge
from discord.ext import commands, tasks
import logging
import exchange_handler
import check_minecraft_server

FFMPEG_EXECUTABLE = nikdoge.undump_json('nikdoge_bot_settings.json')['FFMPEG_EXECUTABLE']#"C:/Program Files/ffmpeg/bin/ffmpeg.exe"
FILENAME_LOG = 'nikdoge_bot.log'
COMMAND_PREFIX = '/'

logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s %(name)s[%(levelname)s]: %(message)s',
    handlers = [
        logging.FileHandler(FILENAME_LOG),
        logging.StreamHandler()
    ]
)
log = logging.getLogger('Discord bot')

description = '''Nikdoge's personal bot.'''

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, description=description, intents=intents)

exch = exchange_handler.Exchange()
nms_checker = check_minecraft_server.Checker("server.nikdoge.ru:25565")

@bot.command(pass_context=True)
async def nikdogebot(ctx):
    await help3.invoke(ctx)

@bot.command()
async def help3(ctx):
    help_text_en = f"""Nikdoge Bot is only on the start of its way to the bright future, and atm it's pretty dumb
    {COMMAND_PREFIX}nikdogebot - help on Nikdoge Bot
    {COMMAND_PREFIX}woofe - answers "woofe indeed"
    {COMMAND_PREFIX}rokk - prints rokk ebol
    {COMMAND_PREFIX}zdravstvuite - says Hello in RYTP style in your voice channel
    {COMMAND_PREFIX}georgian - prints georgian letters
    {COMMAND_PREFIX}exchange {COMMAND_PREFIX}ex {COMMAND_PREFIX} - georgian exchange"""
    help_text_ru = f"""Nikdoge Bot только в начале своего пути к светлому будущему, и пока что весьма мало полезен
    {COMMAND_PREFIX}nikdogebot - помощь по Nikdoge Bot
    {COMMAND_PREFIX}woofe - отвечает "woofe indeed"
    {COMMAND_PREFIX}rokk - печатает весь рокк ебол
    {COMMAND_PREFIX}zdravstvuite - говорит Здравствуйте в RYTP-манере в твой голосовой канал
    {COMMAND_PREFIX}georgian - печатает грузинский алфавит
    {COMMAND_PREFIX}exchange {COMMAND_PREFIX}ex {COMMAND_PREFIX} - грузинский обменник (без аргументов печатает помощь по команде)"""
    embed=discord.Embed(
        title="Nikdoge Bot help",
        description=help_text_ru,
        color=0xFF5733)
    await ctx.send(embed=embed)

@bot.command(pass_context=True)
async def ex(ctx):
    await exchange.invoke(ctx)

@bot.command(pass_context=True)
async def обмен(ctx):
    await exchange.invoke(ctx)

@bot.command()
async def exchange(ctx, *, arg: str = []):
    embed = None
    response = None
    send_help = False
    lang = 'ru'
    input_string = arg
    if input_string == []:
        send_help = True
    else:
        response = exch.exchange_handler(input_string)
    
    if send_help:
        if lang == 'ru':
            description = 'Грузинский обменник\nКоманда ' + exch.help_ru().replace('exchange_handler',COMMAND_PREFIX+'обмен')
        else:
            description = 'Georgian exchange\nCommand ' + exch.help().replace('exchange_handler',COMMAND_PREFIX+'exchange')
        embed=discord.Embed(description=description, color=0xFF5733)
    
    await ctx.send(response,embed=embed)

@bot.command()
async def woofe(ctx):
    response = 'woofe indeed'
    await ctx.send(response)

@bot.command()
async def rokk(ctx):
        response = '''Р О К К
Е Б О Л
М У П Ю
О В И Ч
Н И R Е
Т👠🔑Й'''
        await ctx.send(response)
        return

@bot.command()
async def zdravstvuite(ctx):
        log.info('zdravstvuite called')
        response = '''Простите, извините, "здравствуйте" временно не работает; мы обязательно с этим разберёмся!'''
        await ctx.send(response)
        return
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

@bot.command()
async def georgian(ctx):
    response = '''Ა а, Ბ б, Გ г, Დ д, Ე э, Ვ в, Ზ з, Თ т, Ი и, Კ к', Ლ л, Მ м, Ნ н, Ო о, Პ п', Ჟ ж, Რ р, Ს с, Ტ т', Უ у, Ფ п, Ქ к, Ღ гх, Ყ кх, Შ ш, Ჩ ч, Ც ц, Ძ дз, Წ ц', Ჭ ч', Ხ хъ, Ჯ дж, Ჰ х'''
    await ctx.send(response)


#https://stackoverflow.com/questions/62069138/how-to-let-a-bot-post-send-a-message-every-5-minutes-or-because-of-another-event
@tasks.loop(seconds=20)
async def my_background_task():

    #await bot.wait_until_ready() # ensures cache is loaded
    channel = bot.get_channel(763862682054557756) # NMS:status # replace with target channel id
    answer_string = nms_checker.get_fresh_players_info()
    if answer_string:
        log.info(answer_string)
        await channel.send(answer_string)
    #else:
    #    log.info("NMS players amount unchanged")


@bot.event
async def on_ready():
    log.info(f'{bot.user} (ID: {bot.user.id}) is connected to the following guilds:')
    for guild in bot.guilds:
        log.info(f'{guild.id}: {guild.name}')
    my_background_task.start()
        

@bot.listen('on_message')
async def whatever_you_want_to_call_it(message):
    if message.content.startswith('.help3'):
        response = 'Maybe try /nikdogebot instead'
        await message.channel.send(response)


log.info('Starting Nikdoge Discord bot')
bot.run(nikdoge.undump_json('nikdoge_bot_settings.json')['DISCORD_TOKEN'])
