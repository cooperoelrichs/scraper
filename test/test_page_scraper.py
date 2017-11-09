import unittest
import bs4
from scraper.page_scraper import PageScraper
import real_estate.real_estate_property as rep
from scraper.test.open_json import open_json_file


def open_test_html(file_path):
    x = None
    with open(file_path, 'r') as f:
        x = f.read()
    return x


def open_html_as_soup(file_path):
    html = open_test_html(file_path)
    soup = bs4.BeautifulSoup(html, "html.parser")
    return soup


class TestPageScraper(unittest.TestCase):
    TEST_DATA_DIR = 'scraper/test/data'
    TEST_HTML_FILE = TEST_DATA_DIR + '/test_html.json'

    def test_check_for_no_results(self):
        no_results = open_html_as_soup(
            self.TEST_DATA_DIR + '/test_no_results.html')
        has_results = open_html_as_soup(
            self.TEST_DATA_DIR + '/test_has_results.html')

        self.assertTrue(PageScraper.check_for_no_results(no_results))
        self.assertFalse(PageScraper.check_for_no_results(has_results))

    def assert_equal_with_summary(self, provided, expected):
        self.assertEqual(
            provided, expected,
            '\n%s\nv.\n%s' % (provided.summarise(), expected.summarise())
        )

    def zip_eq_len(self, x1, x2):
        self.assertEqual(len(x1), len(x2), 'Test lists are not equal length.')
        return zip(x1, x2)

    def test_extract_price(self):
        tests = [
            ('$429,000', [429000]),
            ('$429,000+', [429000]),
            ('$1,000,000,000+', [1000000000]),
            ('Offers Over $429,000+', [429000]),
            ('995,000', [995000]),
            ('$279,000 - $900,000', [279000, 900000]),
            ('$279,000 - $9,000,000', [279000, 9000000]),
            ('Price guide $340,000 - $380,000', [340000, 380000]),
            ('offers over $580,000 considered', [580000]),
            ('...10 Sep 2016 (On Site)', None),
            ('...on 17 September 2016', None),
            ('... 3rd September at 12pm', None),
            ('...10th September', None),
            ('...22/9/2016 @12:30pm', None),
            ('...16 On Site at 10.30am', None)
        ]

        for string, expected in tests:
            parsed = PageScraper.extract_prices(string, PageScraper.MIN_PRICE)
            self.assertEqual(parsed, expected)

    def test_residential_sale_type(self):
        tests = open_json_file(self.TEST_HTML_FILE)['sales.listing_info']
        expecteds = [
            rep.Auction(False),
            rep.PrivateTreaty([528000], False),
            rep.Auction(False),
            rep.PrivateTreaty([799000], True),
            rep.SaleTypeParseFailed(),
            rep.UnableToFindSaleTypeText()
        ]

        for listing_info, expected in self.zip_eq_len(tests, expecteds):
            soup = bs4.BeautifulSoup(listing_info, "html.parser")
            parsed = PageScraper.residential_sale_type(soup, False)
            self.assertEqual(parsed, expected)

    def test_match_under_contract(self):
        tests = [
            ('Under Contract', True),
            ('Auction on 10/10/10', False),
            ('Prop is under contract', True)
        ]

        for string, expected in tests:
            parsed = PageScraper.check_for_match(
                string, PageScraper.UNDER_CONTRACT_REGEX)
            self.assertEqual(parsed, expected)

    def test_new_apartment_project(self):
        article = open_json_file(self.TEST_HTML_FILE)['new_apartment_project']
        article_soup = bs4.BeautifulSoup(article, "html.parser")
        children = PageScraper.scrape_new_apartment_project(article_soup)

        self.assertEqual(len(children), 4)
        self.assertIs(type(children[0]), rep.Property)

        child_0 = rep.Property(
            sale_type=rep.PrivateTreaty([349900], False),
            details=rep.Details(rep.TownHouse(), 2, 2, 1, None, None),
            address_text=rep.AddressText(
                '1/Cnr Bernard Heinze Avenue, Moncrieff, ACT 2914')
        )
        self.assert_equal_with_summary(children[0], child_0)

    def test_residential_property(self):
        article = open_json_file(self.TEST_HTML_FILE)['residential_property']
        article_soup = bs4.BeautifulSoup(article, "html.parser")
        residential = PageScraper.scrape_residential_property(article_soup)

        expected = rep.Property(
            sale_type=rep.Negotiation(True),
            details=rep.Details(rep.House(), 4, 2, 2, None, None),
            address_text=rep.AddressText(
                '51 Wootton Crescent, Gordon, ACT 2906')
        )

        self.assertIs(type(residential), rep.Property)
        self.assert_equal_with_summary(residential, expected)

    def test_residential_land(self):
        article = open_json_file(self.TEST_HTML_FILE)['residential_land']
        article_soup = bs4.BeautifulSoup(article, "html.parser")
        land = PageScraper.scrape_residential_land(article_soup)

        expected = rep.Property(
            sale_type=rep.Auction(False),
            details=rep.Details(rep.Land(), None, None, None, None, None),
            address_text=rep.AddressText(
                '25 Toorale Terrace, Lawson, ACT 2617')
        )

        self.assertIs(type(land), rep.Property)
        self.assert_equal_with_summary(land, expected)

    def test_house_land_package(self):
        article = open_json_file(self.TEST_HTML_FILE)['house_land_package']
        article_soup = bs4.BeautifulSoup(article, "html.parser")
        prop = PageScraper.scrape_house_land_package(article_soup)

        expected = rep.Property(
            sale_type=rep.OffPlan([799990], False),
            details=rep.Details(rep.House(), 4, 2, 2, None, None),
            address_text=rep.AddressText(
                '4 Barolits Street, Denman Prospect, ACT 2611')
        )

        self.assertIs(type(prop), rep.Property)
        self.assert_equal_with_summary(prop, expected)

    def test_rural_property(self):
        article = open_json_file(self.TEST_HTML_FILE)['rural_property']
        article_soup = bs4.BeautifulSoup(article, "html.parser")
        prop = PageScraper.scrape_rural_property(article_soup)

        expected = rep.Property(
            sale_type=rep.Negotiation(False),
            details=rep.Details(rep.Rural(), 3, 2, 2, None, None),
            address_text=rep.AddressText(
                '1076 Spring Range Road, Hall, ACT 2618')
        )

        self.assertIs(type(prop), rep.Property)
        self.assert_equal_with_summary(prop, expected)

    def test_deduce_sale_type(self):
        tests = [
            ('Tenders Thursday 1st September', True, False, rep.Tender(True)),
            ('$4,999,000+', True, False, rep.PrivateTreaty([4999000], True)),
            ('AUCTION 10 Sept 2016', True, False, rep.Auction(True)),
            ('995,000', False, False, rep.PrivateTreaty([995000], False)),
            ('Ove $665,000', False, False, rep.PrivateTreaty([665000], False)),
            ('$799,990', False, True, rep.OffPlan([799990], False)),
            ('Price by negotiation', False, False, rep.Negotiation(False)),
            ('', False, True, rep.OffPlan(None, False)),
            ('Auction', False, False, rep.Auction(False)),
            ('tender', True, False, rep.Tender(True)),
            ('by Negotiation', False, False, rep.Negotiation(False)),
            ('by Negotiaton', True, False, rep.Negotiation(True)),
            ('Contact Agent', False, False, rep.ContactAgent(False)),
            ('$9,999,999', True, False, rep.PrivateTreaty([9999999], True)),
            ('99,999', False, False, rep.PrivateTreaty([99999], False)),
            ('', False, False, rep.SaleTypeParseFailed()),
            ('UnableToFindSaleTypeText', False, False,
             rep.UnableToFindSaleTypeText())
        ]

        for string, status, off_plan, expected in tests:
            sale_type = PageScraper.deduce_sale_type(string, status, off_plan)
            self.assertIs(type(sale_type), type(expected))
            self.assert_equal_with_summary(sale_type, expected)

    def test_create_property_details(self):
        tests = [
            (
                rep.Auction(True),
                {'bedrooms': 3, 'bathrooms': 1, 'car spaces': 1},
                rep.Details(rep.Auction(True), 3, 1, 1, None, None)
            ),
            (
                rep.PrivateTreaty(1, True),
                {'bedrooms': 3, 'bathrooms': 1},
                rep.Details(rep.PrivateTreaty(1, True), 3, 1, None, None, None)
            )
        ]

        for property_type, features, expected in tests:
            details = PageScraper.create_property_details(
                property_type, features)
            self.assertIs(type(details), rep.Details)
            self.assertEqual(details, expected)

    def test_check_if_under_contract(self):
        tests = open_json_file(self.TEST_HTML_FILE)['sales.property_stats']
        expecteds = [
            False, False, False, False, True, True, False, True, True, True,
            True, False
        ]

        for test, expected in self.zip_eq_len(tests, expecteds):
            property_stats = bs4.BeautifulSoup(test, "html.parser").div
            under_contract = PageScraper.check_if_under_contract(
                property_stats)
            self.assertTrue(under_contract == expected,
                            'property_stats - %s' % test)

    def test_find_sale_type_text(self):
        tests = open_json_file(self.TEST_HTML_FILE)['sales.property_stats']
        expecteds = [
            'Contact Agent',
            '$415,000',
            'By Negotiation',
            'Auction 10am Sat 10 Sep 2016 (On Site)',
            'Under Contract',
            'Under Offer',
            'PENTHOUSE',
            'UNDER CONTRACT',
            'UNDER OFFER',
            'By Negotiation',
            'Under Offer',
            'UnableToFindSaleTypeText'
        ]

        for test, expected in self.zip_eq_len(tests, expecteds):
            property_stats = bs4.BeautifulSoup(test, "html.parser").div
            sale_type_text = PageScraper.find_sale_type_text(
                property_stats)
            self.assertEqual(sale_type_text, expected,
                             'property_stats - %s' % test)

    def test_maybe_extract_property_features(self):
        tests = open_json_file(self.TEST_HTML_FILE)['sales.listing_info']
        expecteds = [
            {'bedrooms': 4, 'bathrooms': 2, 'car spaces': 2},
            {'bedrooms': 3, 'bathrooms': 2, 'car spaces': 2},
            {'bedrooms': 2, 'bathrooms': 1, 'car spaces': 2},
            {},
            {},
            {}
        ]

        for listing_info, expected in self.zip_eq_len(tests, expecteds):
            soup = bs4.BeautifulSoup(listing_info, "html.parser")
            parsed = PageScraper.maybe_extract_property_features(soup)
            self.assertEqual(parsed, expected)

    def test_feature_value_to_int(self):
        self.assertEqual(
            PageScraper.feature_value_to_int('1', [], ''),
            1
        )
        self.assertEqual(
            PageScraper.feature_value_to_int('11 m² (approx)', [], ''),
            11
        )
        with self.assertRaises(ValueError):
            PageScraper.feature_value_to_int('1x', [], '')
