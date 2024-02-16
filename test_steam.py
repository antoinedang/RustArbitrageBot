import steampy
from steampy.client import SteamClient

steam_id = 76561199539234298
api_key = "7363287E484125113FBCCE410388052C"
steam_client = SteamClient(api_key=api_key)

with open(file="steam_guard.json", mode="r") as x:
    print(x.read())


steam_client.login(username="MoneyGangOnTop", password="Gumball1*", steam_guard=f"steam_guard.json")

print(steam_client.is_session_alive())