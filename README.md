ptb-release-helper
==================
*A little something to help PTB devs with their releases.* 


Logging changes from the commit history is a tiresome process and even more so, if you need the log in different formattings.
The devs of [`python-telegram-bot`](https://python-telegram-bot.org) have to fear no more!

## What it does/How it's used:

0. Install the requirements by `pip install -r requirements.txt`.
1. Open `config.ini` fill it as such:
    ```ini
    [Release]
    version_number = The number of the release we're going to make, e.g. 12.9
    
    [GitHub]
    token = Your GitHub OAuth-Token with read acces to the PTB organisation
    username = Alternatively for basic authentication your username …
    password = … and password
    
    [Telegram]
    token = A Bot token
    chat_id = A chat ID the bot can send messages to, preferably yours
    ```
   Some notes on that:
   * The GitHub credentials are used to fetch data from GitHub. Read access to the PTB organisation is desirable, as the authorship of PRs in the TG announcement should only be stated for non-organisation members and there are developers in the organization, who are not not publicly visible.
   * Bot token and chat id are used to send the HTML-formatted announcement for the [Telegram Channel](https://t.me/pythontelegrambotchannel). If the Bot is admin in that channel, you *could* send the announcement there directly. But sending it to yourself should be preferred, in case something goes wrong.
   
2. Run `python prepare_changelog.py`. This fetches the current changelog from the repo and saves it as `CHANGES.rst`. It also prepares the changelog for the to be released version by adding a header and including the description of all merged PRs since the last `Bump to vX.Y`-commit.
3. Rearrange and rephrase `CHANGES.rst` to your liking. As the complete changelog is downloaded, you'll have plenty of releases to take inspiration from.

    What you *don't* need to do is:
    * Add links to the PRs or authors of the PRs
    * Format code as monospace
    
4. Run `python generate_release_notes.py`. This generates three different versions of the release notes prepared in step 3:

    * `docs.rst`:
 
        Release notes formatted as reStructuredText, ready to be be copy-pasted back into the original `CHANGES.rst` for publication in the [docs](https://python-telegram-bot.readthedocs.io).
       
    * `release.md`:
 
        Release notes formatted as GitHub-Markdown, ready to be be copy-pasted into the release notes on [GitHub](https://github.com/python-telegram-bot/python-telegram-bot/releases/new).
        
    * `channel.html`:
 
        Release notes formatted as Telegram-HTML. This one will also mention all PR-authors, who are not members of PTB with the corresponding PRs. Send this via a bot with `parse_mode=HTML`.
        
    While `generate_release_notes.py` tries quite hard to ease your workflow by regexing *all the things*, it might still not be perfect, so please check the output before releasing.
    
5. To make the announcement on the Telegram channel
    1. run `python send_telegram.py` to send the text in `channel.html` to the configured chat.
    2. If that chat wasn't the PTB channel already, just copy the text and paste it into the channel.
    
That's it. Happy releasing! 🙂
    