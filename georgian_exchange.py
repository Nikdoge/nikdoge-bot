#!/usr/bin/env python3

#From rico.ge "currency buy sell" to georgian lari
#buy - means exchange buys from me
#sell - means exchange sell to me
#Not convenient for me, but it is how it's organized on exchange
DATA_DATE = '2022.05.08' #Date when data from exchange obtained
RICOGE = '''USD 	3.0200 	3.0350
EUR 	3.1850 	3.2050
RUR 	0.0364 	0.0464
ILS 	0.7640 	0.9040
GBP 	3.7000 	3.7800
TRY 	0.1530 	0.2230
CHF 	3.0220 	3.1020
CAD 	2.2400 	2.3600
AED 	0.6740 	0.8240
AMD 	0.0044 	0.0074
AZN 	1.7110 	1.8110'''.replace('RUR','RUB',1).splitlines()
#Damn ricoge
#RUR (810) — российский рубль до деноминации 1998 года;
#RUB (643) — российский рубль после деноминации 1998 года;
BASE_CURRENCY = 'GEL'
RICOGE.append(f'{BASE_CURRENCY} 1 1') #Adding BASE_CURRENCY to table for consistency
EXCHANGE_INFO = None
ROUTE_TOO_LONG = 15 #maximum lenght of crossrate route: if 4, then "1000 RUB GEL USD EUR" is maximum

def process_exchange_info(exchange_text):
    exchange_info = dict()
    for line in exchange_text:
        line = line.split()
        exchange_info[line[0]] = {'buy':float(line[1]),'sell':float(line[2])}
    return exchange_info

EXCHANGE_INFO = process_exchange_info(RICOGE)

def analyze_input_string(string):
    DEFAULT_CURRENCY = 'RUB'
    currencies_nicks_pre = {
        'RUB':['₽','rub','ruble','руб','рубль','RUR'],
        'USD':['$','usd','dollar','доллар'],
        'EUR':['€','eur','euro','евро'],
        'GEL':['₾','gel','lari','лари']}
    currencies_nicks = dict()
    for k,v in currencies_nicks_pre.items():
        for nick in v:
            if nick not in currencies_nicks:
                currencies_nicks[nick] = k

    fail = False
    is_whole = False
    if len(string) == 0: fail = True
    elif ' ' not in string: 
        #maybe it is only number or number is joined by currency
        is_whole = True
        #fail = True 
    if fail: return 100, [DEFAULT_CURRENCY] #КОСТЫЛЬ
    
    listing = ['']
    if not is_whole:
        listing = string.split()
    else:
        for letter in string:
            if letter.isdigit():
                listing[0] += letter
            else:
                break
        if len(string)>len(listing[0]):
            if len(listing) == 1:
                listing.append('')
            for letter in string[len(listing[0]):]:
                listing[1] += letter
    if len(listing[0]) == 0 or not listing[0].isdigit(): fail = True #Found no digits for amount
    if fail: return 100, [DEFAULT_CURRENCY] #КОСТЫЛЬ

    #first elem should be hadled as amount, other (if they are in place) - as crossrate route
    amount = float(listing[0])
    currencies = []

    if len(listing) > 1:
        for currency in listing[1:]:
            if currency not in EXCHANGE_INFO and currency not in currencies_nicks: 
                pass
            elif currency in EXCHANGE_INFO: currencies.append(currency)
            elif currency in currencies_nicks: currencies.append(currencies_nicks[currency])
            #elif currency in currencies_nicks_non_strict: currencies.append(currencies_nicks_non_strict[currency]) #here .startswith can be used

            if len(currencies) > ROUTE_TOO_LONG: break

    if len(currencies) == 0: currencies = [DEFAULT_CURRENCY]

    return amount, currencies

def calculate_change(amount=float(),currency_in=str(),currency_out=str()):
    """
    Takes initial amount of money, initial currency and goal currency
    If there is crossrate through BASE_CURRENCY, calculates crossrate silently
    Example: 
    BASE_CURRENCY is GEL, we know how much GEL is to sell or to buy to do convertation with EUR, RUB and USD
    If we convert EUR/GEL, RUB/GEL, GEL/USD etc. it convert straight forward
    If we convert EUR/USD, RUB/USD, RUB/EUR then it will convert through GEL as BASE_CURRENCY
    """
    #print(amount,currency_in,currency_out)
    if currency_out == BASE_CURRENCY:
        amount_out = amount*EXCHANGE_INFO[currency_in]['buy']

    elif currency_in == BASE_CURRENCY:
        amount_out = amount/EXCHANGE_INFO[currency_out]['sell']
    else:
        #amount_out = calculate_change(amount,currency_in,BASE_CURRENCY)[0]/calculate_change(amount,BASE_CURRENCY,currency_out)[0]
        amount_out = amount*EXCHANGE_INFO[currency_in]['buy']/EXCHANGE_INFO[currency_out]['sell']
    #We could make the function, that will find crossrate route, not only in/GEL/out
    return round(amount_out,3),currency_out

def process_request(amount=float(), currencies=list()):
    """
    Takes initial amount of money and list of currencies to convert through
    List can have 1 element, then the specified currency will be converted to BASE_CURRENCY (GEL)
    """
    processing_amount = amount
    processing_currency = currencies[0]
    result_string = f'{processing_amount} {processing_currency}'

    if len(currencies) == 1:
        result_string += " -> {} {}".format(*calculate_change(processing_amount,processing_currency,BASE_CURRENCY))
    else:
        for currency in currencies[1:]:
            processing_amount, processing_currency = calculate_change(processing_amount,processing_currency,currency)
            result_string += " -> {} {}".format(processing_amount, processing_currency)

    return result_string

def help():
    return f"""georgian_exchange gets string like "1000 RUB GEL" or "500 GEL RUB" and converts specified amount from one currency (to or through georgian lari - GEL) to another by best exchange rate known from rico.ge at {DATA_DATE} (will be reloading automaticly later).

Variants of request:
"1000" = "1000 RUB GEL" — Default convertation route is RUB -> GEL;
"100 EUR" = "100 EUR GEL" — Default goal currency is GEL;
"10000 RUB GEL EUR" — Crosschange calculation is available;
"10000 RUB EUR" — Exchange is based on georgian lari anyway so as previous this will also be processed through GEL, but not showing it.

Known currencies: GEL (₾,lari), USD ($,dollar), EUR (€,euro), RUB (₽,ruble), ILS, GBP, TRY, CHF, CAD, AED, AMD, AZN.
"""

def help_ru():
    return f"""georgian_exchange получает строку типа "1000 RUB GEL" или "500 GEL RUB" и конвертирует указанное количество из одной валюты (к или через грузинский лари - GEL) в другую по наилучшему известному курсу с rico.ge на {DATA_DATE} (потом будет обновляться автоматически).

Варианты запроса:
"1000" = "1000 RUB GEL" — Маршрут конвертации по умолчанию RUB -> GEL;
"100 EUR" = "100 EUR GEL" — Целевая валюта по умолчанию GEL;
"10000 RUB GEL EUR" — Работает конвертация по цепочке;
"10000 RUB EUR" — Обмен в любом случае базирован на грузинском лари, так что как и в предыдущем примере эта конвертация пройдёт через GEL, только втихую.

Известные валюты: GEL (₾,лари), USD ($,доллар), EUR (€,евро), RUB (₽,рубль), ILS, GBP, TRY, CHF, CAD, AED, AMD, AZN.
По падежам валюты пока не склоняются :)
"""

if __name__ == '__main__':
    import sys
    string = ' '.join(sys.argv[1:])
    print(process_request(*analyze_input_string(string)))

def georgian_exchange(string=str()):
    """
    E.g.: "1000 RUB GEL" or "500 GEL RUB" or "1500 EUR GEL"
    """
    return process_request(*analyze_input_string(string))

