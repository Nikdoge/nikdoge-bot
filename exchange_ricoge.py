#parsing exchange rates from rico.ge
from time import time
import urllib3
from bs4 import BeautifulSoup
from libs import nikdoge
from datetime import timedelta as td, datetime as dt
import logging

OFFSET = 40*60 #in seconds, after which time to try reload data from online
SAVE_FILE_NAME = 'exchange_ricoge.json'
ONLINE_RESOURCE = 'https://www.rico.ge'
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

def get_data_online():
    exchange_data = None
    timestamp = dt.utcnow().isoformat()

    #downloading
    http = urllib3.PoolManager()
    url = ONLINE_RESOURCE
    try:
        resp = http.request('GET', url)
    except urllib3.exceptions.MaxRetryError:
        log.info('Failed to download info from ricoge, data will not be updated')
        return exchange_data, timestamp #fail connecting
    if resp.status != 200: 
        log.info('Failed to download info from ricoge, data will not be updated')
        return exchange_data, timestamp #fail connecting

    #transforming
    decoded = resp.data.decode('utf-8')
    soup = BeautifulSoup(decoded, 'lxml')

    array = []
    table_materials = soup.select('tr')
    for tr in table_materials[1:]:
        array.append(tr.text.split())

    #checking for adequacity
    FAIL_TRESHOLD = 0
    fail = 0
    if len(array)<3: fail += 1
    for elem in array:
        if len(elem) != 3:
            fail += 1
    #also good idea to check for digits and availability of usd and eur
    if fail > 0:
        log.info('Data from ricoge appears to be broken')
        return exchange_data, timestamp

    #prepare info to return
    exchange_data = {}
    for elem in array:
        #THIS IS VERY SPECIFIC TO RICOGE
        #Damn ricoge
        #RUR (810) — российский рубль до деноминации 1998 года;
        #RUB (643) — российский рубль после деноминации 1998 года;
        exchange_data['RUB' if elem[0] == 'RUR' else elem[0]] = {
            'buy':float(elem[1]),
            'sell':float(elem[2])
        }
    
    return exchange_data, timestamp

def get_data():
    try:
        saved_content = nikdoge.undump_json(SAVE_FILE_NAME)
    except FileNotFoundError:
        saved_content = None
    
    timestamp_now = dt.utcnow()
    if (saved_content 
    and 'timestamp' in saved_content
    and 'update attempt timestamp' in saved_content
    and 'data' in saved_content):
        timestamp_upd_atmpt = dt.fromisoformat(saved_content['update attempt timestamp'])
        if timestamp_now > timestamp_upd_atmpt + td(seconds=OFFSET):
            #Time passed
            log.info('It came time to update ricoge data: downloaded and stored')
            exchange_data, timestamp = get_data_online()
            save_data(exchange_data, timestamp)
        else:
            #Time didn't pass
            log.info("Getting ricoge info from file, because time to update data didn't come yet")
            exchange_data,timestamp = saved_content['data'],saved_content['timestamp']
    else: 
        log.info('Found no stored ricoge data: downloaded and stored')
        exchange_data,timestamp = get_data_online()  
        save_data(exchange_data, timestamp)
    return exchange_data,timestamp

def get_data_offline():
    #maybe it will be usable for someone
    try:
        saved_content = nikdoge.undump_json(SAVE_FILE_NAME)
        exchange_data,timestamp = saved_content['data'],saved_content['timestamp']
    except (FileNotFoundError,KeyError):
        exchange_data = timestamp = None
    return exchange_data,timestamp

def save_data(exchange_data,timestamp):
    #store data
    if exchange_data:
        #if we downloaded new data
        filescheme = {
            'timestamp' : timestamp, #is what we show as timestamp of info
            'update attempt timestamp' : timestamp, #is from where we count some CONSTANT time not to try download data again
            'data' : exchange_data #exchange data itself
        }
        
        nikdoge.dump_json(filescheme,filename=SAVE_FILE_NAME)
    else:
        #if we didnt download data successfully, when only writing timestamp
        content = nikdoge.undump_json(SAVE_FILE_NAME)
        content['update attempt timestamp'] = timestamp
        nikdoge.dump_json(content,filename=SAVE_FILE_NAME)

if __name__ == '__main__':
    exchange_data,timestamp = get_data()
