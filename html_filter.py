import re

from panflute import BulletList, Header, Link, Para, Plain, Str, Strong, run_filter

LINE_BREAK = Str("\n")


def build_pr_link(number: str):
    return f"https://github.com/python-telegram-bot/python-telegram-bot/pull/{number}"


def action(element, document):
    if isinstance(element, Str):
        if match := re.match(pattern=r"\((\#(\d+))\)", string=element.text):
            return [
                Str("("),
                Link(Str(match.group(1)), url=build_pr_link(match.group(2))),
                Str(")"),
            ]
    if isinstance(element, Header):
        return Plain(Strong(*element.content))
    if isinstance(element, Para):
        return Plain(LINE_BREAK, *element.content, LINE_BREAK)
    if isinstance(element, BulletList):
        # BulletList contains a list of LineItem
        # Each of those contains a Plain element (at least in our use case)
        lines = [e.content[0] for e in element.content]
        for line in lines:
            line.content.insert(0, Str("• "))
        return [Plain(LINE_BREAK), *lines, Plain(LINE_BREAK)]
    return element


def main(doc=None):
    return run_filter(action, doc=doc)


if __name__ == "__main__":
    main()
