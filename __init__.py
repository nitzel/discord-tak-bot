from discordtakbot import DiscordTakBot
from readconfig import Config

# Configs are attempted to be read in this order until one succeeds.
# This allows a dev to have a config that isn't checked in to the repository
CONFIG_FILES = ["botsettings.dev.json", "botsettings.json"]


if __name__ == "__main__":
    config = None
    for config_file in CONFIG_FILES:
        print(f"Attempting to read config from '{config_file}'")
        try:
            config = Config.load(config_file)
            print(f"Successfully read config from '{config_file}'")
            break
        except FileNotFoundError:
            print(f"Cannot read config from '{config_file}' because it does not exist'")
    if not config:
        exit("Failed read configuration")

    initial_moves = [
        "a2", "a1",
        "b1", "a2-",
        "b1<", "b1",
        "Ca2", "b2",
        "a2-", "b3",
        "3a1>111"
    ]

    bot = DiscordTakBot(config.tak, initial_moves=initial_moves)
    bot.run(config.discord.token)
