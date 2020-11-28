### Discord Tak Bot
This bot takes messages with commands in [Portable Tak Notation](https://ustak.org/portable-tak-notation/), executes them on a board and then sends a message with the new board state.

![Screenshot](readme/screenshot.png)

### How to play
Commands start with a `$` and the rest is as usual e.g. `$a1` to place a flat in the lower left corner or `$f6` for the top right one.

### How to run
#### Requirements
- A discord bot token [how to create a bot](https://discordpy.readthedocs.io/en/latest/discord.html)
- Bot access to your server with the following priviliges
  - Go to [discord apps](https://discord.com/developers/applications), select your app, go to `OAuth2` and in the URL generator set
    - `scope=bot`
    - `Bot Permissions`
      - `General`
        - `Manage Channels`
        - `Create Instant Invite`
      - `Text Permissions`
        - `Send Messages`
        - `Manage Messages`
        - `Embed Links`
        - `Attach Files`
  - Visit the generated URL, select the server you want the bot to have access to and grant it
- Python3 `3.7.6` (I'm not very versed around python's versioning and compatibility, these are just the versions I use)
  - `discord.py 1.5.1`
  - `discord.py-stubs 1.5.1.2` (types, recommended for development only)
  - `Pillow 7.0.0` (PIL / Python Image Library)

#### Run
- Configure `botsettings.json` with your bot token
  - If you are a dev, create a copy of `botsettings.json` called `botsettings.dev.json` which will be ignored by git.
- Run `python3 main.py`

### TODO
- [ ] Create and configure game commands
  - [ ] Move game to private channel that are just created for these games
  - [ ] Maintain multiple games, one per channel
  - [ ] Create certain gamestate from PTN as a starting point for the game
- [ ] Let users only play their own color
- [ ] If a move fails the board may be left in a half-way state
  - This can happen when moving a stack and part of that is dropping stones on standing/cap stones. This aborts the move but it doesn't undo what has already happened.
- [ ] Persist game state between restarts
- [ ] Recognise game ending positions and winner
  - [ ] Road
  - [ ] Board full
  - [ ] All stones used
  - [ ] Resignation
- [ ] Add link to [ptn.ninja](https://ptn.ninja/) to allow users to play around before committing to a move
- [ ] Allow multiple users to control one side?
- [ ] Undo move?
