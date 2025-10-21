from UpdatN import NewsExtractor
import datetime

feed = NewsExtractor()
feed.feed("https://timesofindia.indiatimes.com","https://sputniknews.in","https://www.euronews.com/")