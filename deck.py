from bs4 import BeautifulSoup
import re, os, json
from PIL import Image
import imagehash
import numpy as np

class BSParser:
    """
    This class handles the BeautifulSoup / Html element for a particular card from the
    results of the gatherer search. We assume self.element  is a <tr /> with class = 'cardItem'
    e.g. parser = BSParser(page_soup.find("tr", attrs = {"class": "cardItem"})) and return
    a json representation of it.
    """
    def __init__(self, element: BeautifulSoup):
        self.element = element

    def parse_card_element(self) -> dict:
        return {
            "name": self.element.find("span", attrs = {"class": "cardTitle"}).a.text,
            "mana_cost": [symbol["alt"] for symbol in self.element.find("span", attrs = {"class": "manaCost"}).find_all("img")],
            "converted_mana_cost": float(self.element.find("span", attrs = {"class": "convertedManaCost"}).text),
            "type_data": self._parse_typeline(self.element.find("span", attrs = {"class": "typeLine"}).text),
            "typeline": self.element.find("div", attrs = {"class": "rulesText"}),
            "rules_text": self._clean_rules_text(self.element.find("div", attrs = {"class": "rulesText"})),
            "editions": self._get_editions_metadata(self.element.find("td", attrs = {"class": "setVersions"}))
        }

    def get_url_args(self, url: str) -> dict:
        url_args = {}
        if "?" not in url: return url_args
        for pair in url.split("?")[-1].split("&"):
            if "=" not in pair: continue
            key, val = pair.split("=")
            url_args[key] = val
        return url_args

    def _parse_typeline(self, typeline: str) -> dict:
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

    def _clean_rules_text(self, rules_element: BeautifulSoup) -> str:
        for img in rules_element.find_all("img"):
            img.replace_with(f'%{img.get("alt")}%')
        return rules_element.text

    def _get_editions_metadata(self, set_versions_element: BeautifulSoup) -> dict:
        editions = []
        for link in set_versions_element.find_all("a"):
            editions.append({
                "multiverse_id": int(self.get_url_args(link["href"])["multiverseid"]),
                "set": link.img["alt"].split("(")[0].strip(),
                "rarity": link.img["alt"].split("(")[-1].replace(")", ""),
            })
        return editions

    def _re_handle(self, pattern: str, string: str) -> str:
        result = re.search(pattern, string)
        if result:
            return result.group(0)
        else:
            None

class MagicCard:
    """
    Parent class to ReferenceCard and CandidateCard
    """
    def __init__(self):
        pass

    def _compute_phash(self, card_cutout: np.ndarray) -> imagehash.ImageHash:
        """
        common phash function between the ref and candidate cards
        """
        return imagehash.phash(Image.fromarray(card_cutout))

class ReferenceCard(MagicCard):
    """
    Represents a reference card with a known phash / multiverse id
    """
    def __init__(self, multiverse_id) -> None:
        super().__init__()
        self.multiverse_id = multiverse_id

    def compute_ref_phash(self) -> imagehash.ImageHash:
        return self._compute_phash(
            self.get_ref_image(
                self.multiverse_id
            ))

    def get_ref_image(self, images_dir: str = os.path.join("data", "card_images")):
        filepath = os.path.join(images_dir, f"{self.multiverse_id}.jpeg")
        assert os.path.exists(filepath), f"Could not find image at: {filepath}"
        return Image.open(filepath)

    def get_ref_phash(self, data_path: str = os.path.join("data", "id_map.json")):
        with open(data_path, "r") as j:
            hex_str = json.load(j).get(self.multiverse_id)
        return imagehash.hex_to_hash(hex_str)

class CandidateCard(MagicCard):
    """
    Meant to represent a candidate card image to be identified
    """
    def __init__(self, candidate_image: np.ndarray) -> None:
        super().__init__()
        self.candidate_image = candidate_image

    def compute_candidate_phash(self, apply_processing = True) -> imagehash.ImageHash:
        candidate = self.candidate_image
        if apply_processing:
            candidate = self.process_image(candidate)
        return self._compute_phash(candidate)

    def process_image(self, image: np.ndarray) -> np.ndarray:
        # TO DO
        return image