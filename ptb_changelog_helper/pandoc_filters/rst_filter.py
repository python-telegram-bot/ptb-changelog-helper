import re

from panflute import Doc, Element, RawInline, Str, run_filter


def action(
    element: Element, document: Doc | None  # pylint: disable=unused-argument
) -> Element | list[Element] | None:
    if isinstance(element, Str):
        text = re.sub(pattern=r"\(\#(\d+)\)", repl="(:pr:`\\1`)", string=element.text)
        return RawInline(text=text, format="rst")
    return None


def main(doc: Doc | None = None) -> Doc | None:
    return run_filter(action, doc=doc)


if __name__ == "__main__":
    main()
