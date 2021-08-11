import requests
from bs4 import BeautifulSoup
import imagehash
import cv2

import deck

import json, logging, traceback, os, collections

GATHERER_PAGES = "https://gatherer.wizards.com/Pages/Search/Default.aspx?name=+[]"
IMAGE_URL = "https://gatherer.wizards.com/Handlers/Image.ashx"
DATA_FILE = os.path.join("data", "cards.json")
IMAGES_DIR = os.path.join("data", "card_images")

def get_hamming_spread(ref_multiverse_id: str) -> collections.Counter:
    # This is just to get an idea of how close together 
    deltas = []
    with open(os.path.join("data", "id_map.json")) as j:
        data = json.load(j)
    ref_phash = imagehash.hex_to_hash(data.get(ref_multiverse_id))
    for hex in data.values():
        target_phash = imagehash.hex_to_hash(hex)
        deltas.append(ref_phash - target_phash)
    return collections.Counter(sorted(deltas))

def compute_all_phashs():
    with open(DATA_FILE, "r") as j:
        data = json.load(j)

    phash_map = {}
    id_map = {}
    for card in data.get("cards"):
        for edition in card.get("editions"):
            card_image = cv2.imread(os.path.join(IMAGES_DIR, f"{edition.get('multiverse_id')}.jpeg"))
            phash = deck.MagicCard()._compute_phash(card_image)
            phash_map[phash.__str__()] = edition.get("multiverse_id")
            id_map[edition.get("multiverse_id")] = phash.__str__()
        print(card.get("name"), end="\r")

    with open("data/phash_map.json", "w") as j:
        json.dump(phash_map, j)
    with open("data/id_map.json", "w") as j:
        json.dump(id_map, j)

def scrape_card_image(multiverse_id: str, directory: str):
    image_path = os.path.join(directory, f"{multiverse_id}.jpeg")
    if not os.path.exists(directory): os.makedirs(directory, exist_ok = True)
    if os.path.exists(image_path):
        logging.info(f"image already exists at: {image_path}")
    else:
        response = requests.get(IMAGE_URL, params={"multiverseid": multiverse_id, "type": "card"})
        with open(image_path, "wb") as img_file:
            img_file.write(response.content)

def scrape_all_card_images():
    with open(DATA_FILE, "r") as j:
        data = json.load(j)

    while True:
        num_retries = 0
        try:
            for card in data.get("cards"):
                logging.info(f"scraping images for {card.get('name')} - {len(card.get('editions'))} different editions")
                for edition in card.get("editions"):
                    scrape_card_image(edition.get('multiverse_id'), IMAGES_DIR)
            break
        
        except Exception as e:
            logging.exception(e)
            traceback.print_exc()
            num_retries += 1
            if num_retries >= 10: logging.warn("10 retries exceeded, ending scrape"); break

def scrape_all_cards_metadata():
    soup = BeautifulSoup(requests.get(GATHERER_PAGES).content, "html.parser") 
    num_pages = int(deck.BSParser.get_url_args(soup.find_all("div", attrs = {"class": "pagingcontrols"})[-1].find_all("a")[-1]["href"]).get("page")) + 1
    
    # load in cards already downloaded
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as j:
            data = json.load(j)
    else:
        data = {"completed_pages": [], "cards": []}

    try:
        for page_number in range(num_pages):
            # dont pull pages when we already have the data, might need to change this as new sets are released
            if page_number in data["completed_pages"]: logging.info(f"Page {page_number}/{num_pages-1} already pulled, skipping ..."); continue
            # Here we download the page and parse the results
            logging.info(f"Grabbing page: {page_number}/{num_pages-1}")
            page_soup = BeautifulSoup(requests.get(GATHERER_PAGES, params={"page": page_number}).content, "html.parser")
            for card_element in page_soup.find_all("tr", attrs = {"class": "cardItem"}):
                json_card = deck.BSParser(card_element).parse_card_element()
                # Ensure we dont duplicate cards already in our collection
                if not list(filter(lambda x: x["name"] == json_card["name"], data["cards"])):
                    data["cards"].append(json_card)
                else:
                    logging.info(f"[{json_card['name']}] already present - discarding..")
            data["completed_pages"].append(page_number)
    
    except Exception as e:
        logging.error(e)
        traceback.print_exc()

    finally:
        with open(DATA_FILE, "w") as j:
            json.dump(data, j, indent=4)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    spread = get_hamming_spread("73935")
    print(spread.keys())
    print(spread.values())