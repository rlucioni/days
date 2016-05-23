from bs4 import BeautifulSoup
import requests


url = 'https://en.wikipedia.org/wiki/May_21'


def scrape(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    uls = soup.find_all('ul')
    events_section = uls[1]

    events = []
    for event in events_section.children:
        if event != '\n':
            # http://www.fileformat.info/info/unicode/char/2013/index.htm
            events.append(event.text.split(' – '))

    return events
