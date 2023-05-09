import re

from panflute import RawInline, Str, run_filter


def action(element, document):
    if isinstance(element, Str):
        text = re.sub(pattern=r"\(\#(\d+)\)", repl="(:pr:`\\1`)", string=element.text)
        return RawInline(text=text, format="rst")


def main(doc=None):
    return run_filter(action, doc=doc)


if __name__ == "__main__":
    main()
