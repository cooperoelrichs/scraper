import re
import bs4
import real_estate.real_estate_property as rep


class PageScraper(object):
    MIN_PRICE = 10000
    UNDER_CONTRACT_REGEX = '.*(under contract|under offer)(?i)'

    def html_to_soup(html):
        return bs4.BeautifulSoup(html, "html.parser")

    def no_results_check(soup, page_num):
        no_results = PageScraper.check_for_no_results(soup)
        if no_results:
            print("Found the 'no results' page, final page is number %i" %
                  (page_num - 1))
        return no_results

    def check_for_no_results(soup):
        ds_contents = PageScraper.get_ds_contents(soup)
        search_results = ds_contents.find(
            'form', {'id': 'searchResultsForm'}, recursive=False
        )

        err = RuntimeError('HTML not understood.')

        if search_results is not None:
            no_results = search_results.find(
                'div', {'id': 'noresults'}, recursive=False
            )
            if no_results is not None:
                return True
            else:
                raise(err)
        else:
            results = PageScraper.get_results(ds_contents)
            if results is not None:
                return False
            else:
                raise(err)

    def find_articles(soup):
        ds_contents = PageScraper.get_ds_contents(soup)
        results = PageScraper.get_results(ds_contents)

        articles = results.find(
            'div', {'id': 'searchResultsTbl'}
        ).find_all(
            'article', recursive=False
        )

        PageScraper.num_articles_check(results, len(articles))
        return articles

    def get_ds_contents(soup):
        return soup.find(
            'body', {'id': 'searchResults'}
        ).find(
            'div', {'id': 'DSContents'}
        )

    def get_results(ds_contents):
        return ds_contents.find('div', {'id': 'results'}, recursive=False)

    def num_articles_check(results, articles_len):
        results_info_text = results.find(
            'div', {'id': 'resultsInfo'}
        ).find(
            'p'
        ).get_text()

        results_on_page_search = re.search('(\d+) - (\d+)', results_info_text)
        num_articles_lower = int(results_on_page_search.group(1))
        num_articles_upper = int(results_on_page_search.group(2))
        num_articles_on_page = num_articles_upper - num_articles_lower + 1

        if num_articles_on_page != articles_len:
            raise(RuntimeError(
                'Inconsistent number of articles on page: ' +
                '%i v. %i' % (num_articles_on_page, articles_len)
            ))

    def create_properties(articles):
        properties = []
        for article in articles:
            data_content_type = article['data-content-type']

            if data_content_type == 'residential':
                residential = PageScraper.scrape_residential_property(article)
                properties.append(residential)
            elif data_content_type == 'new apartment project':
                child_properties = PageScraper.scrape_new_apartment_project(
                    article)
                for child_property in child_properties:
                    properties.append(child_property)
            elif data_content_type == 'residential land':
                land = PageScraper.scrape_residential_land(article)
                properties.append(land)
            elif data_content_type == 'house land package':
                package = PageScraper.scrape_house_land_package(article)
                properties.append(package)
            elif data_content_type == 'rural':
                package = PageScraper.scrape_rural_property(article)
                properties.append(package)
            else:
                package = rep.DataContentTypeNotSupported(data_content_type)
                properties.append(package)
        return properties

    def scrape_residential_property(article):
        listing_info = PageScraper.get_listing_info(article)

        sale_type = PageScraper.residential_sale_type(listing_info, False)
        vcard_name_soup = PageScraper.find_vcard_name_soup(listing_info)
        property_type = PageScraper.extract_property_type(vcard_name_soup)
        features = PageScraper.extract_property_features(listing_info)
        details = PageScraper.create_property_details(
            property_type, features)
        address_text = PageScraper.get_address_text(article)
        residential_property = rep.Property(sale_type, details, address_text)
        return residential_property

    def scrape_residential_land(article):
        listing_info = PageScraper.get_listing_info(article)

        sale_type = PageScraper.residential_sale_type(listing_info, False)
        features = PageScraper.maybe_extract_property_features(listing_info)
        vcard_name_soup = PageScraper.find_vcard_name_soup(listing_info)
        property_type = PageScraper.extract_property_type(vcard_name_soup)
        details = PageScraper.create_property_details(property_type, features)
        address_text = PageScraper.get_address_text(article)
        residential_land = rep.Property(sale_type, details, address_text)
        return residential_land

    def scrape_new_apartment_project(article):
        project_wrapper = article.find(
            'div', {'class': 'resultBodyWrapper projectWrapper rui-clearfix'}
        )

        children = article.find(
            'div', {'class': 'project-child-listings'}
        ).find_all(
            'a', recursive=False
        )

        child_properties = []
        for child in children:
            sale_type = PageScraper.new_project_sale_type(child)

            features_soup = child.find(
                'div', {'class': 'child'}
            ).find(
                'div', {'class': 'features'}
            )

            property_type = PageScraper.extract_property_type(child)
            features = PageScraper.extract_property_features(
                features_soup)
            details = PageScraper.create_property_details(
                property_type, features)
            address_text = PageScraper.get_address_text(child)

            child_properties.append(
                rep.Property(sale_type, details, address_text)
            )

        return child_properties

    def scrape_house_land_package(article):
        listing_info = PageScraper.get_listing_info(article)

        sale_type = PageScraper.residential_sale_type(listing_info, True)
        vcard_name_soup = PageScraper.find_vcard_name_soup(listing_info)
        property_type = PageScraper.extract_property_type(vcard_name_soup)
        features = PageScraper.extract_property_features(listing_info)
        details = PageScraper.create_property_details(
            property_type, features)
        address_text = PageScraper.get_address_text(article)
        residential_property = rep.Property(sale_type, details, address_text)
        return residential_property

    def scrape_rural_property(article):
        listing_info = PageScraper.get_listing_info(article)

        sale_type = PageScraper.residential_sale_type(listing_info, False)
        vcard_name_soup = PageScraper.find_vcard_name_soup(listing_info)

        property_type_text = PageScraper.get_property_type_text(
            vcard_name_soup)
        if property_type_text in (
            'other', 'mixed+farming', 'cropping', 'horticulture', 'dairy',
            'livestock', 'farmlet', 'viticulture'
        ):
            property_type = rep.Rural()
        elif property_type_text in ('lifestyle',):
            property_type = rep.PropertyTypeNotSupported(
                property_type_text, vcard_name_soup
            )
        else:
            raise ValueError(
                "Rural property type text was not 'other', it was: %s" %
                property_type_text
            )

        features = PageScraper.maybe_extract_property_features(listing_info)
        details = PageScraper.create_property_details(
            property_type, features)
        address_text = PageScraper.get_address_text(article)

        residential_property = rep.Property(sale_type, details, address_text)
        return residential_property

    def get_listing_info(article):
        return article.find(
            'div', {'class': 'listingInfo rui-clearfix'}
        )

    def extract_property_type(soup_with_href):
        property_type_text = PageScraper.get_property_type_text(soup_with_href)

        if property_type_text == 'house':
            return rep.House()
        elif (property_type_text == 'townhouse' or
                property_type_text == 'villa' or
                property_type_text == 'terrace'):
            return rep.TownHouse()
        elif (property_type_text == 'unit' or
                property_type_text == 'apartment' or
                property_type_text == 'flat'):
            return rep.Unit()
        elif property_type_text == 'serviced+apartment':
            return rep.ServicedApartment()
        elif property_type_text == 'studio':
            return rep.Studio()
        elif property_type_text == 'residential+land':
            return rep.Land()
        elif property_type_text == 'duplex+semi+detached':
            return rep.Duplex()
        elif property_type_text == 'retirement+living':
            return rep.RetirementLiving()
        elif property_type_text == 'unitblock':
            return rep.UnitBlock()
        elif property_type_text == 'acreage+semi+rural':
            return rep.SemiRural()
        elif property_type_text == 'other':
            return rep.NotSpecified()
        else:
            return rep.PropertyTypeNotSupported(
                property_type_text, soup_with_href)

    def get_property_type_text(soup):
        return re.search(
            '^\/property-(\w+\+?\w*\+?\w*\+?\w*)', soup['href']
        ).group(1)

    def find_vcard_name_soup(listing_info):
        return listing_info.find(
            'div', {'class': 'vcard'}
        ).find(
            'a', {'class': 'name'}
        )

    def maybe_extract_property_features(soup):
        property_features = PageScraper.get_property_features_soup(soup)
        if property_features is None:
            return {}
        else:
            return PageScraper.parse_property_features(property_features)

    def get_property_features_soup(soup):
        return soup.find(
            'dl', {'class': 'rui-property-features rui-clearfix'}
        )

    def extract_property_features(soup):
        property_features = PageScraper.get_property_features_soup(soup)
        return PageScraper.parse_property_features(property_features)

    def parse_property_features(features_soup):
        names = PageScraper.find_and_get_all_text(features_soup, ['dt'])
        names = [x.lower() for x in names]
        values = [
            int(x) for x in
            PageScraper.find_and_get_all_text(features_soup, ['dd'])
        ]
        features = dict(zip(names, values))
        return features

    def create_property_details(property_type, features):
        property_details = rep.Details(
            property_type=property_type,
            bedrooms=features.get('bedrooms', None),
            bathrooms=features.get('bathrooms', None),
            garage_spaces=features.get('car spaces', None),
            land_area=None,
            floor_area=None
        )
        return property_details

    def find_and_get_all_text(soup, inputs):
        return [x.get_text() for x in soup.find_all(*inputs)]

    def residential_sale_type(listing_info, off_plan):
        property_stats = PageScraper.get_property_stats(listing_info)
        under_contract = PageScraper.check_if_under_contract(property_stats)
        sale_type_text = PageScraper.find_sale_type_text(
            property_stats)
        sale_type = PageScraper.deduce_sale_type(
            sale_type_text, under_contract, off_plan)
        return sale_type

    def search_for_price_text(property_stats):
        return property_stats.find(
            'p', {'class': 'priceText'}, recursive=False
        )

    def get_property_stats(listing_info):
        return listing_info.find(
            'div', {'class': 'propertyStats'}
        )

    def find_sale_type_text(property_stats):
        price_search = PageScraper.search_for_price_text(property_stats)
        contact_agent_search = property_stats.find(
            'p', {'class': 'contactAgent'}, recursive=False
        )
        type_search = property_stats.find(
            'p', {'class': 'type'}, recursive=False
        )

        if price_search is not None and price_search.has_attr("title"):
            return price_search['title']
        elif price_search is not None:
            return price_search.get_text()
        elif type_search is not None:
            return type_search.get_text()
        elif contact_agent_search is not None:
            return contact_agent_search.get_text()
        else:
            return 'UnableToFindSaleTypeText'

    def new_project_sale_type(child):
        price_text = child.find(
            'div', {'class': 'child'}
        ).find(
            'div', {'class': 'priceAndPropertyTypeContainer'}
        ).find(
            'span', {'class': 'price rui-truncate'}
        ).get_text()

        sale_type = PageScraper.deduce_sale_type(price_text, False, False)
        return sale_type

    def deduce_sale_type(sale_text, under_contract, off_plan):
        prices = PageScraper.extract_prices(sale_text, PageScraper.MIN_PRICE)

        if off_plan:
            return rep.OffPlan(prices, under_contract=under_contract)
        elif re.match('^(?i)auction', sale_text) is not None:
            return rep.Auction(under_contract=under_contract)
        elif re.match('^(?i)tender', sale_text) is not None:
            return rep.Tender(under_contract=under_contract)
        elif PageScraper.check_for_sale_by_negotiation(sale_text):
            return rep.Negotiation(under_contract=under_contract)
        elif prices is not None:
            return rep.PrivateTreaty(prices, under_contract=under_contract)
        elif re.match('^(?i)contact agent', sale_text) is not None:
            return rep.ContactAgent(under_contract)
        elif sale_text == 'UnableToFindSaleTypeText':
            return rep.UnableToFindSaleTypeText()
        else:
            return rep.SaleTypeParseFailed()

    def check_for_sale_by_negotiation(sale_text):
        if (re.match('(?i)(price )?by negotiation', sale_text) is not None or
                re.match('(?i)by negotiaton', sale_text) is not None or
                re.match('(?i)by negotation', sale_text) is not None):
            # Found typos when scraping from the website
            return True
        else:
            return False

    def extract_prices(price_text, min_price):
        dollar_price_regex = '(\$\d+(,\d+)*)'
        dollarless_price_regex = '(\d+(,\d+)*)'

        if re.search(dollar_price_regex, price_text) is not None:
            return PageScraper.text_to_prices(dollar_price_regex, price_text)
        elif re.search(dollarless_price_regex, price_text) is not None:
            prices = PageScraper.text_to_prices(
                dollarless_price_regex, price_text)
            prices = [x for x in prices if x >= min_price]
            if len(prices) != 0:
                return prices
            else:
                return None
        else:
            return None

    def check_for_missed_prices(price_text):
        digits_regex = '(\d+,?\d*)'
        if re.search(digits_regex, price_text) is not None:
            digit_strings = re.findall(digits_regex, price_text)
            numbers = [int(x.replace(',', ''))for x in digit_strings]
            if any([x > 999 for x in numbers]):
                print(
                    'Note: Possible price will be missed: %s' % price_text
                )

    def text_to_prices(regex, price_text):
        price_strings = re.findall(regex, price_text)
        prices = [
            int(x.replace('$', '').replace(',', ''))
            for x, _ in price_strings
        ]
        return prices

    def check_if_under_contract(property_stats):
        return PageScraper.check_if_under_special(
            property_stats, PageScraper.UNDER_CONTRACT_REGEX
        )

    def check_if_under_special(property_stats, regex):
        searches = PageScraper.under_special_searches(property_stats)
        tests = [PageScraper.maybe_check_for_match(x, regex) for x in searches]
        return any(tests)

    def under_special_searches(property_stats):
        type_search = property_stats.find('p', {'class': 'type'})
        price_search = PageScraper.search_for_price_text(property_stats)
        return [type_search, price_search]

    def maybe_check_for_match(search, regex):
        if search is not None:
            text = search.get_text()
            return PageScraper.check_for_match(text, regex)
        else:
            return False

    def check_for_match(text, regex):
        if re.match(regex, text) is not None:
            return True
        else:
            return False

    def find_and_parse_address(article):
        # address_text = PageScraper.find_address_text(article)
        # address = PageScraper.parse_address(address_text)
        # return address
        raise RuntimeError('This method has been deprecated.')

    def get_address_text(article):
        return rep.AddressText(PageScraper.find_address_text(article))

    def find_address_text(article):
        photoviewer_search = article.find(
            'div', {'class': 'photoviewer'}
        )

        property_image_search = article.find(
            'div', {'class': 'propertyImage'}
        )

        if photoviewer_search is not None:
            return photoviewer_search.find('a').find(
                'img', recursive=False
            )['alt']
        elif property_image_search is not None:
            return property_image_search.find('img', recursive=False)['alt']
        else:
            raise RuntimeError('Could not find address text.')
