#!/usr/bin/env python3

import exchange_gateway
from datetime import datetime as dt, timedelta as td
import logging
import argparse
from libs import nikdoge

#From rico.ge "currency buy sell" to georgian lari
#buy - means exchange buys from me
#sell - means exchange sell to me

class Exchange:
    base_currency = None
    time_to_cache = None
    route_too_long = None

    exchange_info = None
    data_date = None
    last_updated = None

    parser = None
    log = None

    def __init__(self):
        filename_log = 'nikdoge_bot.log'
        filename_settings = 'nikdoge_bot_settings.json'
        settings = nikdoge.undump_json(filename_settings)

        logging.basicConfig(
            level = logging.INFO,
            format = '%(asctime)s %(name)s[%(levelname)s]: %(message)s',
            handlers = [logging.FileHandler(filename_log), logging.StreamHandler()]
        )
        self.log = logging.getLogger('Exchange handler')
        self.log.debug('Initialization of Exchange object')

        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('sequence', help='amount and currencies', nargs='*', default=None)
        self.parser.add_argument('--mid', help='calculate by middle between bid and ask', action='store_true')
        self.parser.add_argument('--table', help='calculate by middle between bid and ask', action='store_true')
        #self.parser.add_argument('--source', help='set source of data', nargs='+', default=None)

        self.base_currency = 'GEL'
        self.time_to_cache = 5*60 #in seconds, how long to cache exchange info, received from feed module
        self.route_too_long = 15 #maximum lenght of crossrate route: if 4, then "1000 RUB GEL USD EUR" is maximum

        self.refresh_exchange_data()

    def refresh_exchange_data(self):
        timestamp_now = dt.utcnow()
        exchange_data, timestamp, last_updated = self.exchange_info, self.data_date, self.last_updated

        if (exchange_data == None
        or (last_updated != None and timestamp_now > last_updated + td(seconds=self.time_to_cache))):
            self.log.info('Getting data from exchange gateway')
            exchange_data,timestamp = exchange_gateway.get_data() #time rules from inside do not work if this file is imported in final script once with this call
            exchange_data[self.base_currency] = {'buy':1,'sell':1} #Adding self.base_currency to table for consistency
            last_updated = dt.utcnow()
        else:
            self.log.info('Getting data not from exchange gateway, but what was cached earlier')

        self.exchange_info, self.data_date, self.last_updated = exchange_data,timestamp,last_updated

    def make_table(self):
        answer = f"rico.ge {dt.fromisoformat(self.data_date).strftime('%Y-%m-%d %H:%M UTC')}"+'\n'
        answer += f'CURRENCY:  buy({self.base_currency})  sell({self.base_currency})\n'
        for curr, price in self.exchange_info.items() :
            if curr == self.base_currency: break
            string = f"{curr}:  {str(price['buy'])}  {str(price['sell'])}\n"
            answer += string
        return answer

    def get_table_data(self):
        updated_time = f"{dt.fromisoformat(self.data_date).strftime('%Y-%m-%d %H:%M UTC')}"
        exchange_info = self.exchange_info
        return exchange_info, updated_time

    def analyze_input_string(self, to_analyze=list()):
        """Receives list of amount and currencies from input
        Returns amount=float(), currencies=list(), sell=bool()"""

        #converting human-readable nicknames for currencies into algorhytm-readable
        currencies_nicks_pre = {
            'RUB':['₽','rub','ruble','руб','рубль','RUR','рубас'],
            'USD':['$','usd','dollar','доллар','далар'],
            'EUR':['€','eur','euro','евро','еврик'],
            'GEL':['₾','gel','lari','лари','лар']}
        currencies_nicks = dict()
        for k,v in currencies_nicks_pre.items():
            for nick in v:
                if nick not in currencies_nicks:
                    currencies_nicks[nick] = k

        first_amount = None
        last_amount = None
        sell = True

        try:
            first_amount = float(to_analyze[0].replace(',','.',1))
        except ValueError:
            pass

        if len(to_analyze) == 1 and first_amount != None:
            raise ValueError("No currencies specified")

        try:
            last_amount = float(to_analyze[-1].replace(',','.',1))
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

        currencies_pre = [elem for elem in to_analyze[1 if first_amount != None else None:-1 if last_amount != None else None]]
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

        return amount, currencies, sell


    def calculate_change(self, amount=float(), currency_in=str(), currency_out=str(), sell=bool(), mid=bool()):
        """
        Takes initial amount of money, initial currency and goal currency
        Example: 
        self.base_currency is GEL, we know how much GEL is to sell or to buy to do convertation with EUR, RUB and USD
        If we convert EUR/GEL, RUB/GEL, GEL/USD etc. it convert straight forward
        If we convert EUR/USD, RUB/USD, RUB/EUR then it will convert through GEL as self.base_currency
        """
        if mid == True:
            if currency_out == self.base_currency:
                amount_out = amount*(self.exchange_info[currency_in]['buy']+self.exchange_info[currency_in]['sell'])/2

            elif currency_in == self.base_currency:
                amount_out = amount/((self.exchange_info[currency_out]['buy']+self.exchange_info[currency_out]['sell'])/2)
            else:
                amount_out = amount*((self.exchange_info[currency_in]['buy']+self.exchange_info[currency_in]['sell'])/2)/((self.exchange_info[currency_out]['buy']+self.exchange_info[currency_out]['sell'])/2)
            return round(amount_out,2),currency_out

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
                amount_out = amount*self.exchange_info[currency_in]['sell']/self.exchange_info[currency_out]['buy']
        return round(amount_out,2),currency_out

    def process_request(self, amount=float(), currencies=list(), sell=bool(), mid=bool()):
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
                    currencies.insert(pos, self.base_currency)
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

        connection_string = ' -> ' if mid == False else ' <-> '
        result_string = connection_string.join(result_list[::None if sell else -1])

        return result_string

    def help(self):
        return f"""exchange_handler gets string like "1000 RUB GEL" or "GEL RUB 500" and converts specified amount from one currency (to or through georgian lari - GEL) to another by best known exchange rate from rico.ge
    Last time updated data at {dt.fromisoformat(self.data_date).strftime('%Y-%m-%d %H:%M UTC')}. Will update data with next usage if hour passed.

    Variants of request:
    "10000 RUB GEL EUR" — Crosschange calculation is available;
    "RUB GEL EUR 10000" — Exchange to get 10000 EUR in the end;
    "10000 RUB GEL --mid" — Will calculate by middle between sell and buy price (Handy for fair exchange between friends).

    Known currencies: GEL (₾,lari), USD ($,dollar), EUR (€,euro), RUB (₽,ruble), ILS, GBP, TRY, CHF, CAD, AED, AMD, AZN.
    """

    def help_ru(self):
        return f"""exchange_handler получает строку типа "1000 RUB GEL" или "GEL RUB 500" и конвертирует указанное количество из одной валюты (к или через грузинский лари - GEL) в другую по наилучшему известному курсу с rico.ge
    Последний раз данные обновлялись {dt.fromisoformat(self.data_date).strftime('%Y-%m-%d %H:%M UTC')}. При следующем использовании данные будут обновлены, если они просрочены на час.

    Варианты запроса:
    "10000 RUB GEL EUR" — Работает конвертация по цепочке;
    "RUB GEL EUR 10000" — Конвертация, чтобы в конце получилось 10000 евро;
    "10000 RUB GEL --mid" — Расчёт по среднему значению между ценой продажи и ценой покупки (Полезно для честного обмена с друзьями).

    Известные валюты: GEL (₾,лари), USD ($,доллар), EUR (€,евро), RUB (₽,рубль), ILS, GBP, TRY, CHF, CAD, AED, AMD, AZN.
    По падежам валюты пока не склоняются :)
    """

    def exchange_handler(self,string=str()):
        """
        E.g.: "1000 RUB GEL" or "GEL RUB 500" or "1500 EUR GEL --mid"
        """
        args = self.parser.parse_args(string.split())
        self.log.info(args)

        self.refresh_exchange_data()
        if args.sequence == []:
            if args.table == True:
                return self.make_table()
            else:
                return 'Error: Empty sequence'
        try:
            amount, currencies, sell = self.analyze_input_string(args.sequence)
            return self.process_request(amount, currencies, sell, args.mid)
        except ValueError as e:
            self.log.exception(e)
            return 'Error: '+e.args[0]

if __name__ == '__main__':
    import sys
    exch = Exchange()
    result = exch.exchange_handler(' '.join(sys.argv[1:]))
    exch.log.info(f"{result} based on info from {exch.data_date}")
