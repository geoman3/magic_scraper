import requests
from bs4 import BeautifulSoup

import json, logging, traceback, re, os

IMAGE_URL = "https://gatherer.wizards.com/Handlers/Image.ashx"
GATHERER_PAGES = "https://gatherer.wizards.com/Pages/Search/Default.aspx?name=+[]"
DATA_FILE = "cards.json"

def get_url_args(url: str) -> dict:
    url_args = {}
    if "?" not in url: return url_args
    for pair in url.split("?")[-1].split("&"):
        if "=" not in pair: continue
        key, val = pair.split("=")
        url_args[key] = val
    return url_args

def re_handle(pattern: str, string: str):
    result = re.search(pattern, string)
    if result:
        return result.group(0)
    else:
        None

def parse_typeline(typeline: str) -> dict:
    return {
        "types": {
            "supertypes": typeline.split("  \u2014")[0].split(" ")[:-1], # I gave up on the regex
            "type": typeline.split("  \u2014")[0].split(" ")[-1], # I gave up on the regex
            "subtypes": typeline.split("  \u2014 ")[-1].split("\r\n")[0].split(" ") if "\u2014" in typeline else []
        },
        "stats": {
            "power": re_handle(r"(?<=\().*(?=\/)", typeline), # "(?<=\()" look at chars after (, ".*" any number of arbitrary chars, "(?=\/)" look at chars before /
            "toughness": re_handle(r"(?<=\/).*(?=\))", typeline), #"(?<=\/)" look at chars after /, ".*" any number of arbitrary chars, "(?=\))" look at chars before )
            "loyalty": re_handle(r"(?<=\()[^/]*(?=\))", typeline) # match any number of non / chars between ( and )
        }
    }

def clean_rules_text(rules_element: BeautifulSoup) -> str:
    for img in rules_element.find_all("img"):
        img.replace_with(f'%{img.get("alt")}%')
    return rules_element.text

def get_editions_metadata(set_versions_element: BeautifulSoup) -> dict:
    editions = []
    for link in set_versions_element.find_all("a"):
        editions.append({
            "multiverse_id": int(get_url_args(link["href"])["multiverseid"]),
            "set": link.img["alt"].split("(")[0].strip(),
            "rarity": link.img["alt"].split("(")[-1].replace(")", ""),
        })
    return editions

def parse_card_element(element: BeautifulSoup) -> dict:
    return {
        "name": element.find("span", attrs = {"class": "cardTitle"}).a.text,
        "mana_cost": [symbol["alt"] for symbol in element.find("span", attrs = {"class": "manaCost"}).find_all("img")],
        "converted_mana_cost": float(element.find("span", attrs = {"class": "convertedManaCost"}).text),
        "type_data": parse_typeline(element.find("span", attrs = {"class": "typeLine"}).text),
        "typeline": element.find("div", attrs = {"class": "rulesText"}),
        "rules_text": clean_rules_text(element.find("div", attrs = {"class": "rulesText"})),
        "editions": get_editions_metadata(element.find("td", attrs = {"class": "setVersions"}))
    }

def scrape_card_image(multiverse_id: str, directory: str = "card_images"):
    response = requests.get(IMAGE_URL, params={"multiverseid": multiverse_id, "type": "card"})
    if not os.path.exists(directory): os.mkdir(directory)
    with open(os.path.join(directory, f"{multiverse_id}.jpeg"), "wb") as img_file:
        img_file.write(response.content)

def scrape_all_card_images():
    with open(DATA_FILE, "r") as j:
        data = json.load(j)

    for card in data.get("cards"):
        logging.info(f"scraping images for {card.get('name')} - {len(card.get('editions'))} different editions")
        for edition in card.get("editions"):
            if not os.path.exists(os.path.join("card_images", f"{edition.get('multiverse_id')}.jpeg")):
                scrape_card_image(edition.get('multiverse_id'))
            else:
                logging.info(f"image already exists for multiverse id: {edition.get('multiverse_id')}")

def scrape_all_cards_metadata():
    soup = BeautifulSoup(requests.get(GATHERER_PAGES).content, "html.parser") 
    num_pages = int(get_url_args(soup.find_all("div", attrs = {"class": "pagingcontrols"})[-1].find_all("a")[-1]["href"]).get("page")) + 1
    
    with open(DATA_FILE, "r") as j:
        data = json.load(j)

    try:
        for page_number in range(num_pages):
            if page_number in data["completed_pages"]: logging.info(f"Page {page_number}/{num_pages-1} already pulled, skipping ..."); continue

            logging.info(f"Grabbing page: {page_number}/{num_pages-1}")
            page_soup = BeautifulSoup(requests.get(GATHERER_PAGES, params={"page": page_number}).content, "html.parser")
            for card_element in page_soup.find_all("tr", attrs = {"class": "cardItem"}):
                card = parse_card_element(card_element)
                if not list(filter(lambda x: x["name"] == card["name"], data["cards"])):
                    data["cards"].append(card)
                else:
                    logging.info(f"[{card['name']}] already present - discarding..")

            data["completed_pages"].append(page_number)
    
    except Exception as e:
        logging.error(e)
        traceback.print_exc()

    finally:
        with open(DATA_FILE, "w") as j:
            json.dump(data, j, indent=4)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scrape_all_card_images()
