import unittest
import bs4
from scraper.page_scraper import PageScraper
from scraper.rentals_scraper import RentalsScraper
import real_estate.real_estate_property as rep
from scraper.test.open_json import open_json_file

from scraper.test.test_page_scraper import populate_state_and_postcode


class TestRentalsScraper(unittest.TestCase):
    TEST_HTML_FILE = 'scraper/test/data/test_html.json'

    def assert_equal_with_summary(self, test, expected):
        self.assertEqual(
            test, expected,
            '\n%s\nv.\n%s' % (test.summarise(), expected.summarise())
        )

    def zip_eq_len(self, x1, x2):
        self.assertEqual(len(x1), len(x2), 'Test lists are not equal length.')
        return zip(x1, x2)

    def test_extract_price(self):
        tests = [
            ('$400', [400]),
            ('$99 per week', [99]),
            ('400', [400])
        ]

        for string, expected in tests:
            parsed = PageScraper.extract_prices(
                string, RentalsScraper.MIN_PRICE)
            self.assertEqual(parsed, expected)

    def test_rental_sale_type(self):
        tests = open_json_file(self.TEST_HTML_FILE)[
            'rentals.listing_info']
        expecteds = [
            rep.Rental([750], False),
            rep.Rental([300], False),
            rep.Rental([400], False),
            rep.RentalTypeParseFailed('20'),
            rep.RentalNegotiation(False),
            rep.RentalUnderApplication(),
        ]

        for listing_info, expected in self.zip_eq_len(tests, expecteds):
            soup = bs4.BeautifulSoup(listing_info, "html.parser")
            parsed = RentalsScraper.rental_sale_type(soup)
            self.assertIs(type(parsed), type(expected))
            self.assert_equal_with_summary(parsed, expected)

    def test_rental_property(self):
        state = 'nsw'
        pc = 1000

        article = open_json_file(self.TEST_HTML_FILE)['rental_property']
        article_soup = bs4.BeautifulSoup(article, "html.parser")
        rental = RentalsScraper.scrape_rental_property(article_soup)

        expected = rep.Property(
            sale_type=rep.Rental([300], False),
            details=rep.Details(rep.Unit(), 1, 1, 1, None, None),
            address_text=rep.AddressText(
                '132/2  Windjana Street, Harrison, ACT 2914'
            )
        )

        rental, expected = populate_state_and_postcode(
            [rental, expected], 'test_state', 9999
        )

        self.assertIs(type(rental), rep.Property)
        self.assert_equal_with_summary(rental, expected)

    def test_find_sale_type_text(self):
        tests = open_json_file(self.TEST_HTML_FILE)['rentals.property_stats']
        expecteds = ['$750', '$300 per week', '400', '20']

        for test, expected in self.zip_eq_len(tests, expecteds):
            property_stats = bs4.BeautifulSoup(test, "html.parser").div
            sale_type_text = PageScraper.find_sale_type_text(property_stats)
            self.assertEqual(sale_type_text, expected,
                             'property_stats - %s' % test)
