from mcstatus import MinecraftServer

def get_player_names(players: list):
    [ p.name for p in (status.players.sample or [])]

# If you know the host and port, you may skip this and use MinecraftServer("example.org", 1234)
server = MinecraftServer.lookup("localhost:25565")

# 'status' is supported by all Minecraft servers that are version 1.7 or higher.
status = server.status()
# import pdb; pdb.set_trace()
print(f"The server has {status.players.online} players out of {status.players.max} and replied in {status.latency} ms")
print(f"The players are {get_player_names(status.players.sample)}")


