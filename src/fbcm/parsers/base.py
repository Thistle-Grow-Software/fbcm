from bs4 import Tag


class ParserBase:
    """Shared utility methods for BeautifulSoup-based parsers."""

    @staticmethod
    def get_tag_with_title_containing(tag: Tag, search_str: str) -> Tag | None:
        return tag.find("span", title=lambda t: t and search_str in t)

    @staticmethod
    def get_tag_with_text(search_space: Tag, tag_name: str, text: str) -> Tag | None:
        return search_space.find(tag_name, string=lambda s: text in s.lower())

    @staticmethod
    def get_text_following_label(
        label_tag: Tag | None, expected_sibling_name: str = "span"
    ) -> str | None:
        if label_tag is None:
            return None
        return label_tag.find_next_sibling(expected_sibling_name).get_text(strip=True)
