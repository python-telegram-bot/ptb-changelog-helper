#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime as dtm
from fetch_github import get_changelog, get_commits_since_release
from configparser import ConfigParser

# Get version number from config file
config = ConfigParser()
config.read('config.ini')
version_number = config['Release']['version_number']

# Build the text to be inserted
insertion = []
version_header = f'\nVersion {version_number}'
insertion.append(version_header)
insertion.append((len(version_header) - 1) * '=')
insertion.append(f'*Released {dtm.date.today().strftime("%Y-%m-%d")}*\n')
insertion.append('\n'.join(get_commits_since_release()))

# insert
changelog = get_changelog().split('\n')
new_changelog = changelog[0:3]
new_changelog.extend(insertion)
new_changelog.extend(changelog[3:])
new_changelog = '\n'.join(new_changelog)

# Save to file
with open('CHANGES.rst', 'w') as file:
    file.write(new_changelog)
