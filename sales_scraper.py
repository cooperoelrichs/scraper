from scraper.page_scraper import PageScraper


class SalesScraper(object):

    import memory_profiler
    # @profile
    def scrape_pages(pages, quiet=False):
        scrapings = []

        if not quiet:
            print('Scraping from %i pages.' % len(pages))
            
        for i, soup in enumerate(pages):
            scrapings.extend(SalesScraper.scrape_page(soup))
        return scrapings

    # @profile
    def scrape_page(soup):
        articles = PageScraper.find_articles(soup)
        properties = PageScraper.create_properties(articles)
        return properties
