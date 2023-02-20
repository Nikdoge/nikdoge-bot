from mcstatus import JavaServer

#SERVER_ADDRESS = "server.nikdoge.ru:25565"
USE_QUERY_PROTOCOL = False

class Checker:
    server_address = None
    server = None
    timestamp = None
    players = None
    players_changed = None
    players_amount = None
    players_amount_grew = None
    query_success = None

    def __init__(self, server_address_port):
        self.server_address = server_address_port

        self.players_amount = 0
        self.players = set()

        self.players_amount_grew = False
        self.players_changed = False
        self.query_success = False

        # You can pass the same address you'd enter into the address field in minecraft into the 'lookup' function
        # If you know the host and port, you may skip this and use JavaServer("example.org", 1234)
        self.server = JavaServer.lookup(self.server_address)


    def _get_status(self):
        # 'status' is supported by all Minecraft servers that are version 1.7 or higher.
        # Don't expect the player list to always be complete, because many servers run
        # plugins that hide this information or limit the number of players returned or even
        # alter this list to contain fake players for purposes of having a custom message here.
        status = self.server.status()
        return status #status.players.online, status.latency


    def _get_players(self):
        # 'query' has to be enabled in a server's server.properties file!
        # It may give more information than a ping, such as a full player list or mod information.
        query = self.server.query()
        return query.players.names


    def refresh_data(self):
        self.server = JavaServer.lookup(self.server_address) #must catch exceptions like ValueError('%r does not appear to be an IPv4 or IPv6 address'), help_command = None
        use_query_protocol = USE_QUERY_PROTOCOL
        # Try to use query protocol if enabled
        if use_query_protocol == True:
            try:
                self.query_success = True
                players_new = set(self._get_players())
                players_amount_new = len(players_new)
            except TimeoutError as e:
                self.query_success = False
                use_query_protocol = False
        # Use status protocol if query disabled or failed
        if use_query_protocol == False:
            status = self._get_status()
            players_new = set([elem.name for elem in status.players.sample])
            players_amount_new = status.players.online
        # Analyze data
        if use_query_protocol:
            # In query protocol we can trust player list, so we compare it
            if players_new != self.players:
                self.players_changed = True
                if len(players_new) >= len(self.players):
                    self.players_amount_grew = True
                else:
                    self.players_amount_grew = False
            else:
                self.players_changed = False
                self.players_amount_grew = False
        else:
            # In status protocol we can trust only player amount
            if players_amount_new > self.players_amount:
                self.players_changed = True
                self.players_amount_grew = True
            else:
                self.players_changed = False #kinda wrong here, it could change
                self.players_amount_grew = False
        # Output result to class object
        self.players_amount = players_amount_new
        self.players = players_new


    def get_fresh_entering_players_info(self):
        '''Returning string with amount and list of players if some new player joined'''
        self.refresh_data()
        if self.players_amount_grew:
            return f"{self.players_amount} player(s) on minecraft server: {', '.join(sorted(self.players))}"
        else:
            return None


    def get_fresh_players_info(self):
        '''Returning string with amount and list of players if player list changed'''
        self.refresh_data()
        if self.players_changed:
            return f"{self.players_amount} player(s) on minecraft server: {', '.join(sorted(self.players))}"
        else:
            return None
