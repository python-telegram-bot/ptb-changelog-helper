#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from configparser import ConfigParser
from github import Github

config = ConfigParser()
config.read('config.ini')
token = config['GitHub']['token']
username = config['GitHub']['username']
password = config['GitHub']['password']

if token:
    github = Github(token)
else:
    github = Github(username, password)

REPO = github.get_repo('python-telegram-bot/python-telegram-bot')
ORG = github.get_organization('python-telegram-bot')
DEVELOPERS = [m for m in ORG.get_members()]


def get_changelog():
    return REPO.get_contents('CHANGES.rst').decoded_content.decode('utf-8')


def get_commits_since_release():
    pattern = re.compile(r"^Bump (version|) to v[0-9.]*$", flags=re.IGNORECASE)
    all_commits = REPO.get_commits()
    relevant_commits = []

    for commit in all_commits:
        if re.match(pattern, commit.commit.message):
            break
        relevant_commits.append(commit.commit.message.split('\n')[0])

    return [f'- {commit}' for commit in relevant_commits]
