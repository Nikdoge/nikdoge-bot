#!/usr/bin/env python3

import exchange_gateway
from datetime import datetime as dt, timedelta as td
import logging
import argparse
from libs import nikdoge

#From rico.ge "currency buy sell" to georgian lari
#buy - means exchange buys from me
#sell - means exchange sell to me

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

class Exchange:
    base_currency = None
    time_to_cache = None
    route_too_long = None
    exchange_info = None
    data_date = None
    last_updated = None

    def __init__(self):
        log.info('Initialization of Exchange object')
        self.base_currency = 'GEL'
        self.time_to_cache = 5*60 #in seconds, how long to cache exchange info, received from feed module
        self.route_too_long = 15 #maximum lenght of crossrate route: if 4, then "1000 RUB GEL USD EUR" is maximum

        self.exchange_info, self.data_date, self.last_updated = self.get_exchange_data()

    def get_exchange_data(self):
        timestamp_now = dt.utcnow()
        exchange_data, timestamp, last_updated = self.exchange_info, self.data_date, self.last_updated

        if (exchange_data == None
        or (last_updated != None and timestamp_now > last_updated + td(seconds=self.time_to_cache))):
            log.info('Getting data from exchange gateway')
            exchange_data,timestamp = exchange_gateway.get_data() #time rules from inside do not work if this file is imported in final script once with this call
            exchange_data[self.base_currency] = {'buy':1,'sell':1} #Adding self.base_currency to table for consistency
            last_updated = dt.utcnow()
        else:
            log.info('Getting data not from exchange gateway, but what was cached earlier')

        return exchange_data,timestamp,last_updated

    def get_table(self):
        answer = f"rico.ge {dt.fromisoformat(self.data_date).strftime('%Y-%m-%d %H:%M UTC')}"+'\n'
        answer += f'CURRENCY:  buy({self.base_currency})  sell({self.base_currency})\n'
        for k,v in self.exchange_info.items() :
            if k == self.base_currency: break
            string = f"{k}:  {str(v['buy'])}  {str(v['sell'])}\n"
            answer += string

        return answer

    def analyze_input_string(self,string):
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

        parser = argparse.ArgumentParser()
        parser.add_argument('elements',help='amount and currencies',nargs='+')
        parser.add_argument('--mid',help='calculate by middle between bid and ask',action='store_true')
        args = parser.parse_args(string.split())
        log.info(args)

        first_amount = None
        last_amount = None
        sell = True
        mid = args.mid

        try:
            first_amount = float(args.elements[0].replace(',','.',1))
        except ValueError:
            pass
        if len(args.elements) == 1:
            return first_amount, [DEFAULT_CURRENCY], sell, mid

        try:
            last_amount = float(args.elements[-1].replace(',','.',1))
        except ValueError:
            pass

        if (first_amount == None and last_amount == None):
            raise ValueError("No amount found on start or end of input")
            
        if (first_amount != None and last_amount != None):
            raise ValueError("Found amount both on start or end of input")
            
        if first_amount == None:
            sell = False
            amount = last_amount
        else:
            amount = first_amount

        currencies_pre = [elem for elem in args.elements[1 if first_amount != None else None:-1 if last_amount != None else None]]
        currencies = []
        for currency in currencies_pre:
            if currency not in self.exchange_info and currency not in currencies_nicks: 
                pass
            elif currency in self.exchange_info: currencies.append(currency)
            elif currency in currencies_nicks: currencies.append(currencies_nicks[currency])
            #elif currency in currencies_nicks_non_strict: currencies.append(currencies_nicks_non_strict[currency]) #here .startswith can be used

            if len(currencies) > self.route_too_long: break
        
        if len(currencies) == 0: 
            raise ValueError("Found no known currencies")

        return amount, currencies, sell, mid


    def calculate_change(self,amount=float(),currency_in=str(),currency_out=str(), sell=bool(), mid=bool()):
        """
        Takes initial amount of money, initial currency and goal currency
        If there is crossrate through self.base_currency, calculates crossrate silently
        Example: 
        self.base_currency is GEL, we know how much GEL is to sell or to buy to do convertation with EUR, RUB and USD
        If we convert EUR/GEL, RUB/GEL, GEL/USD etc. it convert straight forward
        If we convert EUR/USD, RUB/USD, RUB/EUR then it will convert through GEL as self.base_currency
        """
        if sell == True:
            if currency_out == self.base_currency:
                amount_out = amount*self.exchange_info[currency_in]['buy']

            elif currency_in == self.base_currency:
                amount_out = amount/self.exchange_info[currency_out]['sell']
            else:
                #amount_out = calculate_change(amount,currency_in,self.base_currency)[0]/calculate_change(amount,self.base_currency,currency_out)[0]
                amount_out = amount*self.exchange_info[currency_in]['buy']/self.exchange_info[currency_out]['sell']
            #We could make the function, that will find crossrate route, not only in/GEL/out
        else:
            if currency_out == self.base_currency:
                amount_out = amount*self.exchange_info[currency_in]['sell']

            elif currency_in == self.base_currency:
                amount_out = amount/self.exchange_info[currency_out]['buy']
            else:
                #amount_out = calculate_change(amount,currency_in,self.base_currency)[0]/calculate_change(amount,self.base_currency,currency_out)[0]
                amount_out = amount*self.exchange_info[currency_in]['sell']/self.exchange_info[currency_out]['buy']
        return round(amount_out,2),currency_out

    def process_request(self,amount=float(), currencies=list(), sell=bool(), mid=bool()):
        """
        Takes initial amount of money and list of currencies to convert through
        List can have 1 element, then the specified currency will be converted to self.base_currency (GEL)
        """

        def add_base_currency(currencies):
            #adding base currency between all non-base currencies
            pos_need_base_currency = []
            for i,currency in enumerate(currencies):
                if i == 0: 
                    previous_currency = currency
                    continue
                if currency != self.base_currency and previous_currency != self.base_currency:
                    pos_need_base_currency.append(i)
                previous_currency = currency
            if pos_need_base_currency != []:
                for pos in pos_need_base_currency[::-1]:
                    currencies.insert(pos,self.base_currency)
            return currencies

        processing_amount = amount
        processing_currency = currencies[0 if sell else -1]
        result_list = [f'{processing_amount} {processing_currency}']
        if sell == False: currencies = currencies[::-1]

        if len(currencies) == 1:
            result_list.append("{} {}".format(*self.calculate_change(processing_amount, processing_currency, self.base_currency, sell, mid)))
        else:
            currencies = add_base_currency(currencies)
            #calculating change
            for currency in currencies[1:]:
                processing_amount, processing_currency = self.calculate_change(processing_amount, processing_currency, currency, sell, mid)
                result_list.append("{} {}".format(processing_amount, processing_currency))

        result_string = ' -> '.join(result_list[::None if sell else -1])

        return result_string

    def help(self):
        return f"""georgian_exchange gets string like "1000 RUB GEL" or "500 GEL RUB" and converts specified amount from one currency (to or through georgian lari - GEL) to another by best exchange rate known from rico.ge at {dt.fromisoformat(self.data_date).strftime('%Y-%m-%d %H:%M UTC')}.

    Variants of request:
    "1000" = "1000 RUB GEL" — Default convertation route is RUB -> GEL;
    "100 EUR" = "100 EUR GEL" — Default goal currency is GEL;
    "10000 RUB GEL EUR" — Crosschange calculation is available;
    "10000 RUB EUR" — Exchange is based on georgian lari anyway so as previous this will also be processed through GEL, but not showing it.

    Known currencies: GEL (₾,lari), USD ($,dollar), EUR (€,euro), RUB (₽,ruble), ILS, GBP, TRY, CHF, CAD, AED, AMD, AZN.
    """

    def help_ru(self):
        return f"""georgian_exchange получает строку типа "1000 RUB GEL" или "500 GEL RUB" и конвертирует указанное количество из одной валюты (к или через грузинский лари - GEL) в другую по наилучшему известному курсу с rico.ge на {dt.fromisoformat(self.data_date).strftime('%Y-%m-%d %H:%M UTC')}.

    Варианты запроса:
    "1000" = "1000 RUB GEL" — Маршрут конвертации по умолчанию RUB -> GEL;
    "100 EUR" = "100 EUR GEL" — Целевая валюта по умолчанию GEL;
    "10000 RUB GEL EUR" — Работает конвертация по цепочке;
    "10000 RUB EUR" — Обмен в любом случае базирован на грузинском лари, так что как и в предыдущем примере эта конвертация пройдёт через GEL, только втихую.

    Известные валюты: GEL (₾,лари), USD ($,доллар), EUR (€,евро), RUB (₽,рубль), ILS, GBP, TRY, CHF, CAD, AED, AMD, AZN.
    По падежам валюты пока не склоняются :)
    """

    def georgian_exchange(self,string=str()):
        """
        E.g.: "1000 RUB GEL" or "500 GEL RUB" or "1500 EUR GEL"
        """
        self.exchange_info, self.data_date, self.last_updated = self.get_exchange_data()
        try:
            new_here = self.analyze_input_string(string)
            return self.process_request(*new_here)
        except ValueError as e:
            log.exception(e)
            return 'Error: '+e.args[0]

if __name__ == '__main__':
    import sys
    string = ' '.join(sys.argv[1:])
    exch = Exchange()
    exch.exchange_info, exch.data_date, exch.last_updated = exch.get_exchange_data()
    try:
        new_here = exch.analyze_input_string(string)
        log.info(f"{exch.process_request(*new_here)} based on info from {exch.data_date}")
    except ValueError as e:
        log.exception(e)