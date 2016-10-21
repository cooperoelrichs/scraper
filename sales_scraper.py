from scraper.page_scraper import PageScraper


class SalesScraper(object):
    def scrape_pages(pages):
        num_pages = len(pages)
        scrapings = []
        for i, soup in enumerate(pages):
            print('Scraping from page %i of %i.' % (i + 1, num_pages))
            scrapings.extend(SalesScraper.scrape_page(soup))
        return scrapings

    def scrape_page(soup):
        articles = PageScraper.find_articles(soup)
        properties = PageScraper.create_properties(articles)
        return properties
