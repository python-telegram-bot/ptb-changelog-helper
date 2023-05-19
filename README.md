# ptb-release-helper
*A little something to help PTB devs with their releases.* 

Logging changes from the commit history is a tiresome process and even more so, if you need the log in different markup languages.
The devs of [`python-telegram-bot`](https://python-telegram-bot.org) have to fear no more!

## What it does/How it's used:

1. Install the python requirements by `pip install -r requirements.txt`.
2. Install [pandoc](https://pandoc.org/installing.html) and make sure it's in your `PATH`. This tool was tested with pandoc 3.1.2.
3. Save a copy of `example_main.py` as `main.py` and fill in your configurations:
   * `new_version`: The version that you are about to release
   * `github_token`: A GitHub GraphQL token with read access to the PTB organisation
   * `bot_token`: A Telegram Bot token
   * `telegram_chat_id`: A chat ID the bot can send messages to, preferably yours
   * `ptb_dir`: The path to your local clone of the PTB repository
4. Run `python main.py`. This fetches the current changelog and guides you through the next steps. In the end, you will have a message on Telegram ready to be copied to the PTB channel and the PTB repository will be ready for the release commit.

That's it. Happy releasing! 🙂
    