# Authors:
# Nikhil Kumar & Pravat Bhusal

# url imports
import urllib.request, urllib.error
from urllib.parse import urlparse, parse_qs

# file imports
import os
import json
from bs4 import BeautifulSoup

# verify that urlopen worked successfully without any errors
def request_is_valid(url):
    try:
        req = urllib.request.urlopen(url)

    # most common case for when the URL is not found on the server
    except urllib.error.HTTPError as e:
        # print error code and a message that the URL was not found on the server
        print('HTTPError: {}'.format(e.code))
        print('The requested URL was not found on the server.')
        return False

    # second case for when the error is not HTTP-specific (e.g. connection refused)
    except urllib.error.URLError as e:
        # print the error and a message for the user signifying an unknown problem has occurred
        print('URLError: {}'.format(e.reason))
        print('A connection to the server could not be made. Please try again later')
        return False

    # success, no other operations required by the function
    else:
        return True

# parse a meals URL
def parse_meals(url):
    if request_is_valid(url):
        # receive the domain of the URL
        parsed_url = urlparse(url)
        domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_url)

        # dictionary to store the meals
        meals = dict()

        # makes a request to the given URL and stores the response
        response = urllib.request.urlopen(url)

        # reads in the response and creates a variable out of it to be used as a parser
        html_doc = response.read()
        soup = BeautifulSoup(html_doc, 'html.parser')
        for source_text in soup.find_all('div', {"class": "jumbotron"}):
            # map each meal's URL into the meals dictionary
            meal = str(source_text.h1.strong.text)
            meals[meal] = domain + 'location?meal=' + meal

        # converts the meals dictionary into JSON
        meals_json = json.dumps(meals)
        return meals_json
    else:
        return "An error occurred when receiving the meals from the URL."

# parse a location URL
def parse_locations(url):
    if request_is_valid(url):
        # receive the domain of the URL
        parsed_url = urlparse(url)
        domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_url)

        # parse the meal from the URL
        meal = parse_qs(parsed_url.query)['meal'][0]

        # dictionary to store the locations
        locations = dict()

        # makes a request to the given URL and stores the response
        response = urllib.request.urlopen(url)

        # reads in the response and creates a variable out of it to be used as a parser
        html_doc = response.read()
        soup = BeautifulSoup(html_doc, 'html.parser')
        for source_text in soup.find_all('div', {"class": "jumbotron"}):
            # map each location URL into the locations dictionary
            location = str(source_text.h1.strong.text)
            locations[location] = domain + 'select?meal=' + meal + '&loc=' + location

        # converts the locations dictionary into JSON
        locations_json = json.dumps(locations)
        return locations_json
    else:
        return "An error occurred when receiving the locations from the URL."

# parse a URL menu
def parse_menu(url):
    if request_is_valid(url):
        # makes a request to the given URL and stores the response
        response = urllib.request.urlopen(url)

        # reads in the response and creates a variable out of it to be used as a parser
        html_doc = response.read()
        soup = BeautifulSoup(html_doc, 'html.parser')

        # store all the sections with nutrition facts
        nutrition = parse_nutrition(soup)

        # process line function
        def process_line(line, start_char, end_char, start_shift, end_shift):
            start = line.find(start_char)
            end = line.find(end_char)
            result = line[start + start_shift : end - end_shift]
            return result

        # dictionary to store the categories with the foods
        menu = dict()

        # dictionary to store the filters
        filters = dict()

        # finds all the td tags in the HTML text
        for source_text in soup.find_all('td'):

            # splits the HTML text into separate lines of text
            lines = str(source_text).split('\n')

            # parses the HTML table line by line
            food_index = 0
            for line in lines:
                # append the food categories
                if line.startswith('<td class="name lead station'):
                    category = process_line(line, ';', '</td>', 3, 0)
                    menu[category] = dict()

                # append the food names
                if line.startswith('<span>') and 'Calories' not in line:
                    food_name = process_line(line, '>', '</', 1, 0)
                    menu[category][food_name] = list()

                # append the food icons
                if line.startswith('<img alt='):
                    img_url = process_line(line, 'src=', 'width', 5, 2)
                    menu[category][food_name].append(img_url)

                    # add the filter (food icon) into the dictionary
                    filter = img_url.split("/")[-1]
                    filter = os.path.splitext(filter)[0].capitalize()
                    filters[filter] = img_url

        # converts the menu dictionary into JSON
        foods = dict(Nutrition=format_nutrition(menu, nutrition),
                    Filters=filters,
                    Menu=menu)
        foods_json = json.dumps(foods)
        return foods_json
    else:
        return "An error occurred when receiving the menu from the URL."

# parse the nutrition facts from html
def parse_nutrition(html):
    # store all the sections with nutrition facts
    nutrition = list()

    # loop through each nutrition facts section
    for source_text in html.find_all('section', {"class": "performance-facts"}):
        serving_size = source_text.find('p').text
        item_facts = [serving_size]

        # loop through each nutrition fact
        for fact in source_text.find_all('th'):
            fact_str = ""
            for text in fact.find_all(text=True):
                fact_str += text

            # add the nutrition facts into an Array
            fact_str = fact_str.strip()
            item_facts.append(fact_str)

        # append the item's facts into the nutrition
        nutrition.append(item_facts)

    return nutrition

# format the nutrition Array into a dictionary of food names
def format_nutrition(menu, nutrition):
    nutrition_dict = dict()

    # iterate through each category in the menu
    for category in menu:
        foods = menu[category]

        # iterate through each food in the category
        for food in foods:
            # add the food and its nutrition facts into the dictionary
            nutrition_dict[food] = nutrition[len(nutrition_dict)]

    return nutrition_dict
