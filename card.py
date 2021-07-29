from bs4 import BeautifulSoup
import requests

GATHERER_URL = "https://gatherer.wizards.com/Pages/Search/Default.aspx"
GATHERER_ARGS = "page=0&name=+[]"
CARD_URL_TEMPLATE = "https://gatherer.wizards.com/Pages/Card/Details.aspx"



class MagicCard:
    def __init__(self, name: str, multiverse_ids: list):
        self.gatherer_link = gatherer_link