import re
from bs4 import BeautifulSoup
import requests

SUPPORTED_SITES = ['officemag', 'tdglobus', 'citilink']
# сити линк
class SiteParts:
    def __init__(self, url):
        self.__parts = dict()
        f = open('partsOfSites.txt', 'r')
        for line in f.readlines():
            l = line.replace('\n', '').split('=')
            self.__parts[l[0]] = l[1]

        self.__url = url
        self.__nameSite = self.__extract_domain(url)

        if SUPPORTED_SITES.__contains__(self.__nameSite):
            self.__isSupSite = True
            self.__price_element = self.__getPartsOfSite('_price')
            self.__price_class = self.__getPartsOfSite('_class_price')
            self.__price_best_class = self.__getPartsOfSite('_class_price_best')
            self.__name_element = self.__getPartsOfSite('_name')
            self.__name_class = self.__getPartsOfSite('_class_name')
        else:
            self.__isSupSite = False

    def __extract_domain(self, url):
        pattern = r'(?:https?:\/\/)?(?:www\.)?([^\/\n\.]+)'
        match = re.search(pattern, url)
        return match.group(1) if match else None

    def __getPartsOfSite(self, part):
        return self.__parts[self.__nameSite + part]

    def get_inf(self):
        if self.__isSupSite:
            response = requests.get(self.__url)
            bs = BeautifulSoup(response.text, "lxml")

            try:
                price = bs.find(self.__price_element, class_=self.__price_class).text.replace('\xa0', '').replace('\x20', '')
                pattern = r'(\d+(?:[.,]\d+)?)'
                match = re.search(pattern, price)
                price = float(match.group().replace(',', '.'))
            except AttributeError:
                price = ''

            try:
                price_best = bs.find(self.__price_element, class_=self.__price_best_class).text.replace('\xa0', '').replace('\x20', '')
                pattern = r'(\d+(?:[.,]\d+)?)'
                match = re.search(pattern, price_best)
                price_best = float(match.group().replace(',', '.'))
            except AttributeError:
                price_best = ''


            try:
                # price = bs.find(self.__price_element, class_=self.__price_class).text.replace('\xa0', '')
                name = bs.find(self.__name_element, class_=self.__name_class).text.replace('\n', '')
                # print(name)
            except AttributeError:
                # print('no name')
                # print(AttributeError.name)
                # price = ''
                name = ''
        else:
            price_best =''
            price = ''
            name = ''

        return price, price_best, name
