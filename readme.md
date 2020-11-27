### Discord Tak Bot
This bot takes messages with commands in [Portable Tak Notation](https://ustak.org/portable-tak-notation/), executes them on a board and then sends a message with the new board state.

![Screenshot](readme/screenshot.png)

### How to play
Commands start with a `$` and the rest is as usual e.g. `$a1` to place a flat in the lower left corner or `$f6` for the top right one.

### How to run
#### Requirements
- A discord bot token
  - Privileges
    - *todo*
- Add the bot to your server
- Python3
  - DiscordPy
  - PIL
  - BytesIO
  - *todo*
- Run `python3 main.py`

### ToDo
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
