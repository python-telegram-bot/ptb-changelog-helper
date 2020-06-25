#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from fetch_github import REPO, DEVELOPERS
from configparser import ConfigParser

PR_URL = 'https://github.com/python-telegram-bot/python-telegram-bot/pull/'

# Prepare some patterns
version_pattern = r"(Version [0-9.]*\n=*\n\*Released [0-9-]*\*)"

cc_pattern = re.compile(
    r"([A-Z](?:[A-Z0-9]*[a-z][a-z0-9]*[A-Z]|[a-z0-9]*[A-Z][A-Z0-9]*[a-z])[A-Za-z0-9]*) ",
    flags=re.MULTILINE)
cc_rst_replace = "``\\1`` "
cc_md_replace = "`\\1` "
cc_html_replace = "<code>\\1</code> "
code_pattern = re.compile(
    r"([a-zA-Z][a-zA-Z0-9.]*(?:(?:[_.]+[a-zA-Z0-9.]+)+(?:\([a-zA-Z0-9_.]*\))?)|[a-zA-Z]["
    r"a-zA-Z0-9.]*\([a-zA-Z0-9_.]*\))",
    flags=re.MULTILINE)
code_rst_replace = "``\\1``"
code_md_replace = "`\\1`"
code_html_replace = "<code>\\1</code>"
pr_pattern = re.compile(r"(#([0-9]*))", flags=re.MULTILINE)
pr_rst_replace = "`\\1`_"
pr_md_replace = rf"[\1]({PR_URL}\2)"
pr_html_replace = rf'<a href="{PR_URL}\2">\1</a>'


def pr_html_user_mention_replace(match_obj):
    pr = int(match_obj.group().strip('#'))
    user = REPO.get_pull(pr).user
    if user not in DEVELOPERS:
        return f'<a href="{PR_URL}{pr}">#{pr}</a> by <a href="{user.html_url}">{user.login}</a>'
    else:
        return f'<a href="{PR_URL}{pr}">#{pr}</a>'


# Some preparations for the different outputs
docs_patterns = {cc_pattern: cc_rst_replace, code_pattern: code_rst_replace,
                 pr_pattern: pr_rst_replace}
release_patterns = {cc_pattern: cc_md_replace, code_pattern: code_md_replace}
channel_patterns = {cc_pattern: cc_html_replace, code_pattern: code_html_replace,
                    pr_pattern: pr_html_user_mention_replace}

# Read Changelog
with open('CHANGES.rst', 'r') as file:
    changelog = file.read()

# get latest versions part
tmp = re.split(version_pattern, changelog)
version_header = tmp[1]
body = tmp[2]

# Generate the different files


def apply_patterns(text, p_r_dict):
    for p, r in p_r_dict.items():
        text = re.sub(p, r, text, 0)
    return text


# First for the docs
docs_text = apply_patterns(version_header + body, docs_patterns)
links = []
for match in re.finditer(pr_pattern, docs_text):
    links.append(f'.. _`{match.group()}`: {PR_URL}{match.group(1)}')
docs_text += '\n'.join(links)

# For the GitHub release
release_text = apply_patterns(version_header + body, release_patterns)

# For the Telegram channel
config = ConfigParser()
config.read('config.ini')
version_number = config['Release']['version_number']
header = f"We've just released v{version_number}.\nThank you to everyone who contributed to " \
         f"this release.\n\nAs usual, upgrade using <code>pip install -U " \
         f"python-telegram-bot</code>. "
channel_text = header + apply_patterns(body, channel_patterns)

# Save tests
with open('docs.rst', 'w') as file:
    file.write(docs_text)
with open('release.md', 'w') as file:
    file.write(release_text)
with open('channel.html', 'w') as file:
    file.write(channel_text)
