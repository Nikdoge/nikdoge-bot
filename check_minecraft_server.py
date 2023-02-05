from mcstatus import JavaServer

#SERVER_ADDRESS = "server.nikdoge.ru:25565"

class Checker:
    server_address = None
    server = None
    timestamp = None
    players_amount = None
    players_amount_grew = None

    def __init__(self, server_address_port):
        self.server_address = server_address_port
        self.players_amount = 0
        self.players_amount_grew = False
        # You can pass the same address you'd enter into the address field in minecraft into the 'lookup' function
        # If you know the host and port, you may skip this and use JavaServer("example.org", 1234)
        self.server = JavaServer.lookup(self.server_address)


    def get_status(self):
        # 'status' is supported by all Minecraft servers that are version 1.7 or higher.
        # Don't expect the player list to always be complete, because many servers run
        # plugins that hide this information or limit the number of players returned or even
        # alter this list to contain fake players for purposes of having a custom message here.
        status = self.server.status()
        return status.players.online, status.latency


    def get_players(self):
        # 'query' has to be enabled in a server's server.properties file!
        # It may give more information than a ping, such as a full player list or mod information.
        query = self.server.query()
        return query.players.names


    def refresh_data(self):
        self.server = JavaServer.lookup(self.server_address)
        players_amount_new, latency_new = self.get_status()

        if players_amount_new > self.players_amount:
            self.players_amount_grew = True
        else:
            self.players_amount_grew = False

        self.players_amount = players_amount_new

    def get_fresh_players_info(self):
        self.refresh_data()
        if self.players_amount_grew:
            players = self.get_players()
            return f"Currently playing on minecraft server: {', '.join(players)}"
        else:
            return None

            
