from scraper.page_scraper import PageScraper


class SalesScraper(object):
    def scrape_pages(htmls, quiet=False):
        scrapings = []

        if not quiet:
            print('Scraping from %i pages.' % len(htmls))

        for i, html in enumerate(htmls):
            soup = PageScraper.html_to_soup(html)
            scrapings.extend(SalesScraper.scrape_page(soup))
        return scrapings

    def scrape_page(soup):
        articles = PageScraper.find_articles(soup)
        properties = PageScraper.create_properties(articles)
        return properties
