from bs4 import BeautifulSoup
import re

class BSParser:
    """
    This class handles the BeautifulSoup / Html element for a particular card from the
    results of the gatherer search. We assume self.element  is a <tr /> with class = 'cardItem'
    e.g. parser = BSParser(page_soup.find("tr", attrs = {"class": "cardItem"}))
    """
    def __init__(self, element: BeautifulSoup):
        self.element = element

    def parse_card_element() -> dict:
        return {
            "name": self.element.find("span", attrs = {"class": "cardTitle"}).a.text,
            "mana_cost": [symbol["alt"] for symbol in self.element.find("span", attrs = {"class": "manaCost"}).find_all("img")],
            "converted_mana_cost": float(self.element.find("span", attrs = {"class": "convertedManaCost"}).text),
            "type_data": self._parse_typeline(self.element.find("span", attrs = {"class": "typeLine"}).text),
            "typeline": self.element.find("div", attrs = {"class": "rulesText"}),
            "rules_text": self._clean_rules_text(self.element.find("div", attrs = {"class": "rulesText"})),
            "editions": self._get_editions_metadata(self.element.find("td", attrs = {"class": "setVersions"}))
        }

    def get_url_args(url: str) -> dict:
        url_args = {}
        if "?" not in url: return url_args
        for pair in url.split("?")[-1].split("&"):
            if "=" not in pair: continue
            key, val = pair.split("=")
            url_args[key] = val
        return url_args

    def _parse_typeline(typeline: str) -> dict:
        return {
            "types": {
                "supertypes": typeline.split("  \u2014")[0].split(" ")[:-1], # I gave up on the regex
                "type": typeline.split("  \u2014")[0].split(" ")[-1],
                "subtypes": typeline.split("  \u2014 ")[-1].split("\r\n")[0].split(" ") if "\u2014" in typeline else []
            },
            "stats": {
                "power": self._re_handle(r"(?<=\().*(?=\/)", typeline), # "(?<=\()" look at chars after (, ".*" any number of arbitrary chars, "(?=\/)" look at chars before /
                "toughness": self._re_handle(r"(?<=\/).*(?=\))", typeline), #"(?<=\/)" look at chars after /, ".*" any number of arbitrary chars, "(?=\))" look at chars before )
                "loyalty": self._re_handle(r"(?<=\()[^/]*(?=\))", typeline) # match any number of non / chars between ( and )
            }
        }

    def _clean_rules_text(rules_element: BeautifulSoup) -> str:
        for img in rules_element.find_all("img"):
            img.replace_with(f'%{img.get("alt")}%')
        return rules_element.text

    def _get_editions_metadata(set_versions_element: BeautifulSoup) -> dict:
        editions = []
        for link in set_versions_element.find_all("a"):
            editions.append({
                "multiverse_id": int(self.get_url_args(link["href"])["multiverseid"]),
                "set": link.img["alt"].split("(")[0].strip(),
                "rarity": link.img["alt"].split("(")[-1].replace(")", ""),
            })
        return editions

    def _re_handle(pattern: str, string: str):
        result = re.search(pattern, string)
        if result:
            return result.group(0)
        else:
            None