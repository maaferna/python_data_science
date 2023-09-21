from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from django.http import JsonResponse
import urllib.request, urllib.parse, urllib.error
import xml.etree.ElementTree as ET
from lxml import etree
from collections import Counter
import re

import ssl
import os
import string

from .forms import *
from .models import *
from .utils import *


#External libraries
import requests
from bs4 import BeautifulSoup
import tweepy
from decouple import config
import pandas as pd


# Create your views here.

def index(request):
    context = {}
    return render(request, "index.html", context)

def calculate_overtime(request):
    if request.method == 'POST':
        form = OvertimeForm(request.POST)
        if form.is_valid():
            employee = form.save()
            return render(request, 'overtime_result.html', context={'employee':employee})
    else:
        form = OvertimeForm()

    return render(request, 'overtime_form.html', {'form': form})

def overtime_list(request):
    employees = Overtime.objects.all()
    context = {'employees':employees, }
    return render(request, 'overtime_list.html', context)

def result_overtime(request, employee_id):
    
    try:
        employee = Overtime.objects.get(pk=employee_id)
        overtime_pay = calculate_overtime_pay(employee)
        context = { 'employee': employee, 'overtime_pay': overtime_pay}
        return render(request, 'overtime_result.html', context)
    except Overtime.DoesNotExist:
        return render('overtime_result.html')


#Create a simple scraper to get information from a web page.
def scrape_data(request):
    # URL of the web page you want to scrape
    url = "https://portfolio-mparraf.herokuapp.com"
    module_dir = os.path.dirname(__file__)
    parent_directory = os.path.dirname(module_dir)

    # Send an HTTP GET request to the URL
    response = requests.get(url)

    if response.status_code == 200:
        #Module to analyze files with text formatting HTML.
        soup = BeautifulSoup(response.content, 'html.parser')

        #Extract data of links referenced in this web page. This code pre-processes data and sends to the template an object that contains a list of anchors.
        links = [{ 'data': url +link.get('data'), 'title': link.get('title') } for link in soup.find_all('object')]
        # Render scraped data of all links in this web page.
        context = { 'links': links }
        return render(request, 'scraper/scraped_links.html', context)
    else:
        # Handle the case where the request was not successful
        return render(request, 'scraper/scraper_error.html')
    

def get_tweets(request):
    # Authenticate with Twitter API
    print(settings.TWITTER_BEARER_TOKEN)
    client = tweepy.Client(settings.TWITTER_BEARER_TOKEN, 
                           access_token=settings.TWITTER_API_KEY,
                            access_token_secret=settings.TWITTER_ACCESS_TOKEN,
                            consumer_key=settings.TWITTER_API_SECRET_KEY,
                            consumer_secret=settings.TWITTER_ACCESS_TOKEN_SECRET)
    tweet_text = 'This is a tweet from my Django app using Tweepy and Twitter API v2.'

    # Create the tweet
    tweet = client.create_tweet(text=tweet_text)
    tweet_id = tweet.id_str  # Get the ID of the created tweet
    response_data = {'success': True, 'tweet_id': tweet_id}
   
    return JsonResponse(response_data)

def xml_books(request):
    #If It need acces altrough url
    url = ''
    module_dir = os.path.dirname(__file__)
    parent_directory = os.path.dirname(module_dir)

    # Ignore SSL certificate errors
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # Desired value to match
    desired_value = "ARTURO PEREZ-REVERTE"
    xml_file_path = parent_directory + '/static/datasets/books.xml'
    print(xml_file_path)
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
    except:
        print("Error to upload file")
    #response = requests.get(url)
    #if response.status_code == 200:
        #xml_data = response.content
        #root = ET.fromstring(xml_data)
        #root2 = etree.fromstring(xml_data)
    

    '''
    # Load and compile the XSD schema
    #xsd = etree.XMLSchema(etree.parse(xml_file_path))

    # Validate the XML document against the XSD schema
    is_valid = xsd.validate(root2)

    if is_valid:
        print("XML document is valid against the schema.")
        # Print the schema as a string
        print(etree.tostring(xsd.schema, pretty_print=True).decode('utf-8'))
    else:
        print("XML document is not valid against the schema.")
    '''

    books = [] 

    # Iterate through all book elements
    for book in root.findall(".//item"):
        author_element = book.find("auth")
        title_element = book.find("book")
        if request.GET.get("author_name", None) != None and request.GET.get("title", None) != None:
            author_name = request.GET.get("author_name")
            title = request.GET.get("title")
            # Check if the author element exists and its text contains the filter substring
            if author_element is not None and author_name.strip().lower() in author_element.text.strip().lower() and title.strip().lower() in title_element.text.strip().lower():
                # Extract the data element and store in dictionary variable
                try:
                    book_info = {
                        "id": book.find("isbn").text,
                        "title": book.find("book").text,
                        "language": book.find("lang").text.capitalize(),
                        "price": book.find("euro").text,
                        "publish_date": book.find("year").text,
                        "description": book.find("about").text,
                        "publisher": book.find("publ").text.capitalize(),
                        "tags": book.find("tags").text,
                        "img": 'https://' + book.find("img_url").text,
                        "page": book.find("page").text
                    }
                except:
                    continue
                # Store dictionarty to books list.Pass if book register not contain text
                if book_info["description"] == None:
                    pass
                else:
                    books.append(book_info)
                
        
        context = {'books': books, 'author': author_name}


    return render(request, 'xml/index.html', context)

def regex(request):
    module_dir = os.path.dirname(__file__)
    parent_directory = os.path.dirname(module_dir)
    file_path = parent_directory + '/static/datasets/Regex sample file.txt'
    # Open and read the text file
    with open(file_path, 'r') as file:
        contents = file.read()

    with open(file_path, 'r') as file:  
        contents_by_line = file.readlines()
        
    # Use regular expression to find all numbers
    numbers = re.findall(r'\d+', contents)
    # Use regular expression to find all line to contain only a number.
    line_with_digits = []
    for line in contents_by_line:
        # Use regular expression to check if the line is a number
        if re.match(r'^\d+$', line.strip()):
            line_with_digits.append(line.strip())

    #Define Regex expresion
    url_pattern = r'\b(?:https?://|www\.)\S+\b'

    #Search in text to find all the URL that begin with www. / https or http.
    found_urls = []
    found_urls_with_startwish = []
    try:
        matches = re.finditer(url_pattern, contents)
        for match in matches:
            found_urls.append(match.group(0))
        
        #Find line that begin with some text
        for line in contents_by_line:
            line.rstrip()
            if line.startswith("Terminology:"):
                found_urls_with_startwish.append(line)

    except FileNotFoundError:
        print("File not found.")

    print(found_urls_with_startwish)
    context = {}

    return render(request, 'regex/index.html', context)


def file_analytic(request):
    file_path = parent_directory + '/static/datasets/Regex sample file.txt'
    # Open and read the text file
    languages = ['Java', 'C++', 'PHP', 'Ruby', 'Basic', 'Perl', 'JavaScript', 'Python']
    # Initialize the dictionary with zero counts for each language
    analytics = {lan: 0 for lan in languages}

    with open(file_path, 'r') as file:
        contents = file.readlines()

    for line in contents:
        for lan in languages:
            if lan in line:
                analytics[lan] += 1

    # Sort the dictionary by value
    lst = list()
    for key, val in list(analytics.items()):
        lst.append((val, key))

    lst.sort(reverse=True)

    for key, val in lst[:10]:
        print(key, val)
    
    context = {}

    return render(request, 'regex/index.html', context)


def data_cleaning(request):
    file_path = parent_directory + '/static/datasets/olympics.csv'
    df = pd.read_csv(file_path, index_col=0, skiprows=1)
    df_sorted = df.sort_values(by='Combined total', ascending=False)  # Change 'ascending' to False retrieve the countries with more medals gotten.
    # The type of medals area is defined with a number (01: Gold, 02: Silver, 03:Bronze). The next line was used to rename the column name and retrieve data with a better description.
    for col in df_sorted.columns:
        if col[:2]=='01':
            df_sorted.rename(columns={col:'Gold'+col[4:]}, inplace=True)
        if col[:2]=='02':
            df_sorted.rename(columns={col:'Silver'+col[4:]}, inplace=True)
        if col[:2]=='03':
            df_sorted.rename(columns={col:'Bronze'+col[4:]}, inplace=True)
        if col[:1]=='№':
            df_sorted.rename(columns={col:'#'+col[1:]}, inplace=True)
    
    # To extract the ID of country was applied the split() function in the column name.
    names_ids = df_sorted.index.str.split('\s\(') # split the index by '('
    df_sorted.index = names_ids.str[0] # the [0] element is the country name (new index) 
    df_sorted['ID'] = names_ids.str[1].str[:3] # the [1] element is the abbreviation or ID (take first 3 characters from that)
    df = pd.DataFrame(df_sorted)
    # Rename the column at position 0 (Column1) to 'New Name'
    # Assuming you have your DataFrame df already defined
    df_html = df[1:].to_html(classes='table table-bordered table-striped', index=True)
    answer= []
    max_difference_gold = abs(df['Gold'][1:] - df['Gold.1'][1:]).idxmax()
    # Filter the DataFrame to get the row for "Max Gol difference"
    gb_row = df.loc[max_difference_gold]
    # Get the 'Gold_Difference' value for "Max Gol difference"
    gold_difference_gb = gb_row['Gold'] - gb_row['Gold.1']
    # Add a condition to filter only Countries that gained at least one Gold medal for each season (Summer Winter).
    condition = (df['Gold'] >=1) & (df['Gold.1'] >=1)
    new_df = df[condition]

    # This function generates a Series named 'Points.' This Series represents a weighted value system, where each gold medal (Gold.2) is assigned a weight of 3 points, silver medals (Silver.2) carry 2 points, and bronze medals (Bronze.2) contribute 1 point. The function should return the resulting column as a Series object, with the country names serving as the indices.
    df['Points'] = pd.Series(df['Gold.2'] * 3 + df['Silver.2'] * 2 + df['Bronze.2'])

    answer.append(max_difference_gold)
    answer.append(gold_difference_gb)
    context = {'data': df_html}

    # The country that has won the most gold medals in summer games is ____. Using idxmax()
    print(df['Gold'][1:].idxmax())
    print((abs(df['Gold'][1:] - df['Gold.1'][1:])).idxmax())
    print((abs(new_df['Gold'] - new_df['Gold.1'])/new_df['Gold.2']).idxmax())
    print(df['Points'][1:])
    #
    return render(request, 'pandas/data-cleaning.html', context)


def data_cleaning_census(request):
    file_path = parent_directory + '/static/datasets/census.csv'
    df = pd.read_csv(file_path)
    # Identify the state that encompasses the greatest number of counties. The {{ result.0 }} is the State with more Counties in the United State they are {{ result.1 }}
    greatest_counties = df.groupby(['STNAME']).sum()['COUNTY'].idxmax()
    quantity_greatest_county = df.groupby(['STNAME']).sum()['COUNTY'].max()
    print(greatest_counties, quantity_greatest_county)
        # Find the top ten populous states in descendent order, using the column CENSUS2010POP. To make more complex was filtered with code 50 to group by Counties
    # The key for SUMLEV is as follows:
    # 040 = State and/or Statistical Equivalent
    # 050 = County and /or Statistical Equivalent
    condition_state = df['SUMLEV'] == 50  # Select only STATE, Drop rows that contain state data
    new_condition_state = df[condition_state]
    # Sort the county-level data by state ('STNAME') and population ('CENSUS2010POP') in descending order
    most_population_state = new_condition_state.sort_values(['STNAME', 'CENSUS2010POP'], ascending=[True, False])
    # Calculate the total population for each state and sort them in descending order
    population = most_population_state.groupby('STNAME').agg('sum').sort_values('CENSUS2010POP', ascending=False)
    highest_state = population.head(10).reset_index()

    print(highest_state[['STNAME', 'CENSUS2010POP']])

    context = {}
    return render(request, 'pandas/data-cleaning.html', context)