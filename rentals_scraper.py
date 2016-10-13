import re
from scraper.page_scraper import PageScraper
import real_estate.real_estate_property as rep


class RentalsScraper(object):
    MIN_PRICE = 50
    UNDER_APPLICATION_REGEX = '.*(under application)(?i)'

    def scrape_pages(pages):
        num_pages = len(pages)
        scrapings = []
        for i, soup in enumerate(pages):
            print('Scraping from page %i of %i.' % (i + 1, num_pages))
            scrapings.extend(RentalsScraper.scrape_page(soup))
        return scrapings

    def scrape_page(soup):
        articles = PageScraper.find_articles(soup)
        properties = RentalsScraper.create_properties(articles)
        return properties

    def create_properties(articles):
        properties = []
        for i, article in enumerate(articles):
            data_content_type = article['data-content-type']

            if data_content_type == 'rental':
                residential = RentalsScraper.scrape_rental_property(article)
                properties.append(residential)
            else:
                package = rep.DataContentTypeNotSupported(data_content_type)
                properties.append(package)
        return properties

    def scrape_rental_property(article):
        listing_info = PageScraper.get_listing_info(article)
        sale_type = RentalsScraper.rental_sale_type(listing_info)
        vcard_name_soup = PageScraper.find_vcard_name_soup(listing_info)
        property_type = PageScraper.extract_property_type(vcard_name_soup)
        features = PageScraper.extract_property_features(listing_info)
        details = PageScraper.create_property_details(
            property_type, features)
        address = PageScraper.find_and_parse_address(article)
        residential_property = rep.Property(sale_type, details, address)
        return residential_property

    def rental_sale_type(listing_info):
        property_stats = PageScraper.get_property_stats(listing_info)
        under_application = RentalsScraper.check_if_under_application(
            property_stats)
        sale_type_text = PageScraper.find_sale_type_text(property_stats)
        sale_type = RentalsScraper.deduce_rental_type(sale_type_text,
            under_application)
        return sale_type

    def check_if_under_application(property_stats):
        return PageScraper.check_if_under_special(
            property_stats, RentalsScraper.UNDER_APPLICATION_REGEX
        )

    def deduce_rental_type(sale_text, under_application):
        prices = PageScraper.extract_prices(
            sale_text, RentalsScraper.MIN_PRICE)

        if prices is not None:
            return rep.Rental(prices, under_application)
        elif PageScraper.check_for_sale_by_negotiation(sale_text):
            return rep.RentalNegotiation(under_application)
        elif prices is None and under_application is True:
            return rep.RentalUnderApplication()
        else:
            return rep.RentalTypeParseFailed(sale_text)
