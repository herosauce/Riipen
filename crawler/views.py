import json
import time
import os
import requests

from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

from .models import Profile, RFP
from configparser import ConfigParser
import os

#ua = UserAgent()  # From here we generate a random user agent
ua = UserAgent(use_cache_server=False)
proxies = []


def get_proxies():
    """Get proxies to avoid blocking

    Parameters:
    None

    Returns:
    List:List of proxies

   """
    proxy = []
    proxies_req = Request('https://www.sslproxies.org/')
    proxies_req.add_header('User-Agent', ua.random)
    proxies_doc = urlopen(proxies_req).read().decode('utf8')

    soup = BeautifulSoup(proxies_doc, 'html.parser')
    proxies_table = soup.find(id='proxylisttable')

    # Save proxies in the array
    for row in proxies_table.tbody.find_all('tr'):
        a = row.find_all('td')[0].string + row.find_all('td')[1].string

        proxy.append({'https': a})

        proxies.append({
            'ip': row.find_all('td')[0].string,
            'port': row.find_all('td')[1].string
        })

    return proxies


def get_individual_result_from_linkedin(url, driver):
    """
    Scrape data from linkedin and create a dictionary with user profile details

    Parameters:
    url: url for which scrapping will happen
    driver: Selenium web driver

    Returns:
    Dict: A dictionary with user profile details

   """
    individual_user_data = {}
    individual_user_data[url] = {}
    companies = []
    certifications = []
    profile_name = ""
    current_location = ""

    driver.get(url)
    # Depends on how fast your server loads javascript and htmls
    # This code is to load entire html code, not only source code
    time.sleep(5)
    body = driver.find_element_by_tag_name("body")
    last_height = driver.execute_script(
        "return document.body.scrollHeight")
    while True:
        body.send_keys(Keys.PAGE_DOWN)
        time.sleep(5)
        new_height = driver.execute_script(
            "return document.body.scrollHeight")
        if new_height == last_height:
            break
        else:
            last_height = new_height

    source = driver.page_source
    soup = BeautifulSoup(source, 'lxml')

    # Extract name and current location then find rest of the attributes
    info_divs = soup.findAll(class_="display-flex mt2")
    for info in info_divs:
        profile_name = info.find(class_="inline t-24 t-black t-normal break-words").get_text().strip()
        current_location = info.find(class_="t-16 t-black t-normal inline-block").get_text().strip()
        break  # It will be done in first attempt only

    # Find all profile sections, It will find all headings like Experiences, Companies, Licenses etc
    all_divs = soup.findAll(class_="pv-profile-section-pager")

    for div in all_divs:
        headers = div.findAll('h2')
        for h in headers:
            if h.has_attr('class') and h['class'][0] == 'pv-profile-section__card-heading':
                extractedText = h.get_text().strip()
                if (extractedText == 'Experience'):
                    insideDivs = div.findAll('div')
                    for d in insideDivs:
                        # pv-entity_summary-info pv-entity_summary-info--background-section
                        if d.has_attr('class') and d['class'][0] == 'pv-entity__summary-info' and d['class'][
                            1] == 'pv-entity__summary-info--background-section':
                            pAll = d.findAll('p')

                            for p in pAll:
                                if p.get_text().strip() != 'Company Name':
                                    companies.append(p.get_text().strip())

                if (extractedText == 'Licenses & Certifications'):
                    # <h3 class="t-16 t-bold">Epic Beaker Anatomic Pathology</h3>
                    insideHeaders = div.findAll('h3')
                    for h3 in insideHeaders:
                        if h3.has_attr('class') and h3['class'][0] == 't-16' and h3['class'][1] == 't-bold':
                            certifications.append(h3.get_text().strip())

    try:

        individual_user_data[url]['current_employer'] = companies[0]

    except:
        individual_user_data[url]['current_employer'] = 'None'

    individual_user_data[url]['companies'] = companies
    individual_user_data[url]['certifications'] = certifications
    individual_user_data[url]['name'] = profile_name
    individual_user_data[url]['current_location'] = current_location

    return individual_user_data


@csrf_exempt
def crawler(request, query):
    """
    Use google custom engine to search linkedin profiles 
    with relevant certifications input given by user
    
    Parameters:
    request: HTTP request
    query: User selection from UI
    
    Returns:
    The web page with all relevant user profiles

   """
    name_list = []

    # making a request to a google custom search engine
    custom_search_engine_url = "https://www.googleapis.com/customsearch/v1"

    linkedin_url_list = set()

    for i in range(0, 1):
        PARAMS = {'key': 'AIzaSyByUxDR0YO701YOETlSJZn6bfFNWIjtQBM', 'cx': '009462381166450434430:ecyvn9zudgu',
                  'q': query, 'start': i * 10}

        # sending get request and saving the response as response object
        r = requests.get(url=custom_search_engine_url, params=PARAMS)

        # extracting data in json format
        custom_search_engine_data = r.json()

        for j in range(len(custom_search_engine_data['items'])):
            linkedin_url_list.add(custom_search_engine_data['items'][j]['link'])

    dicty = {}

    # logged in to linkedin
    parser = ConfigParser()
    parser.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'credentials.ini'))

    email = parser.get('credentials', 'email')
    password = parser.get('credentials', 'password')
    driver = webdriver.Chrome(ChromeDriverManager().install())
    login_to_linkedIn(driver, email, password)

    all_availableData_inDb = Profile.objects.all()
    urls_in_database = []

    for data in all_availableData_inDb:
        urls_in_database.append(data.linkedin_url)

    for linkedin_url in linkedin_url_list:
        if (linkedin_url not in urls_in_database):
            temp = get_individual_result_from_linkedin(linkedin_url, driver)
            
            profile_model = Profile()

            URL = list(temp.keys())[0]
            profile_model.name = temp[URL]['name']
            profile_model.linkedin_url = URL
            profile_model.companies = json.dumps(temp[URL]['companies'])
            profile_model.current_job = temp[URL]['current_employer']
            profile_model.certifications = json.dumps(temp[URL]['certifications'])
            profile_model.is_updated = False
            profile_model.save()
        

    driver.quit()
    return result(request, query)


def home(request):
    """Request to load landing page

    Parameters:
    request : HTTP request

    Returns:
    Landing page

   """
    template_name = 'home.html'
    return render(request, template_name)


def rfp_result(request):
    """
    Request to load RFP results

    Parameters:
    request : HTTP request

    Returns:
    returns RFP result page

   """
    template_name = 'rfp_data.html'
    query_set = RFP.objects.all()

    return render(request, template_name, {'licenses': query_set})


def result(request, query):
    """
    As per the user slection on UI, the result will be shown in a new web page.
    Data will be taken from database

    Parameters:
    request : HTTP request
    query: User selection for certifications

    Returns:
    Returns result page on UI
   """
    template_name = 'index.html'
    query_set = Profile.objects.all()
    key = query
    key_list = key.split()
    if key == 'epic beaker anatomic pathology':
        query_set = query_set.filter(certifications__icontains=key_list[2])

    if key == 'epic beaker clinical pathology':
        query_set = query_set.filter(certifications__icontains=key_list[2])

    if key == 'epic cupid':
        query_set = query_set.filter(certifications__icontains=key_list[1])

    if key == 'epic radiant':
        query_set = query_set.filter(certifications__icontains=key_list[1])

    return render(request, template_name, {'profiles': query_set, 'key': query})


def login_to_linkedIn(driver, username, password):
    """Helper method to login to linkedin

    Parameters:
    driver: Selenium driver
    username: Linkedin user id
    password: Linkedin password

   """
    linkedin_homeurl = "https://www.linkedin.com"
    login_url = linkedin_homeurl + '/login'
    driver.get(login_url)
    time.sleep(3)
    driver.find_element_by_id('username').send_keys(username)
    driver.find_element_by_id('password').send_keys(password)
    driver.find_element_by_xpath("//button[contains(text(), 'Sign in')]").click()


@csrf_exempt
def update_result(request, query):
    # Get all data from existing data base
    """
    Update the profiles exist in database

    Parameters:
    request: HTTP request
    query: User selection from UI

    Returns:
    Returns a result page with values

   """

    all_availableData_inDb = Profile.objects.all()
    key = query
    query_set = all_availableData_inDb.filter(certifications__icontains=key)

    user_list = []
    for query in query_set:
        single_user = {}
        linkedin_url = query.linkedin_url
        single_user[linkedin_url] = {}
        single_user[linkedin_url]['certifications'] = query.certifications
        single_user[linkedin_url]['companies'] = query.companies
        single_user[linkedin_url]['current_job'] = query.current_job
        single_user[linkedin_url]['name'] = query.name
        single_user[linkedin_url]['is_updated'] = query.is_updated
        user_list.append(single_user)

    driver = webdriver.Chrome(ChromeDriverManager().install())
    parser = ConfigParser()
    parser.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'credentials.ini'))

    email = parser.get('credentials', 'email')
    password = parser.get('credentials', 'password')

    login_to_linkedIn(driver, email, password)

    for i in range(0, len(user_list)):
        linkedin_url = list(((user_list[i]).keys()))
        linkedin_url = linkedin_url[0]
        profile_info = user_list[i].values()

        # Scrapping from linkedin to reload the data in db in case of any change

        individual_info = get_individual_result_from_linkedin(linkedin_url, driver)
        is_updated = False

        # compare the existing data with retrived data
        if (individual_info[linkedin_url]['name'] != user_list[i][linkedin_url]['name']):
            is_updated = True
        elif (individual_info[linkedin_url]['certifications'] != json.loads(
                user_list[i][linkedin_url]['certifications'])):
            is_updated = True
        elif (individual_info[linkedin_url]['companies'] != json.loads(user_list[i][linkedin_url]['companies'])):
            is_updated = True
        elif (individual_info[linkedin_url]['current_employer'] != user_list[i][linkedin_url]['current_job']):
            is_updated = True
        else:
            is_updated = False

        profile_model = Profile.objects.get(linkedin_url=linkedin_url)
        # update if required
        if (is_updated):
            profile_model.name = individual_info[linkedin_url]['name']
            profile_model.linkedin_url = linkedin_url
            profile_model.companies = json.dumps(individual_info[linkedin_url]['companies'])
            profile_model.current_job = individual_info[linkedin_url]['current_employer']
            profile_model.certifications = json.dumps(individual_info[linkedin_url]['certifications'])

        profile_model.is_updated = is_updated
        profile_model.save()

    driver.quit()
    return result(request, key)


def get_contracts(driver):
    """
    Get all contracts url through scrapping from websites

    Parameters:
    driver: Chrome web driver

    Returns:
    return list of contract urls

   """
    url = "https://apps.des.wa.gov/DESContracts"

    driver.get(url)
    time.sleep(5)
    # This is to load all contracts in a single page
    driver.find_element_by_xpath("//select[@name='contractsTable_length']").send_keys('All')
    time.sleep(5)
    source = driver.page_source
    soup = BeautifulSoup(source, 'lxml')

    # get a list of contract url and titles
    contracts = []
    url = ""
    title = ""
    allTables = soup.findAll("table", {"class", "table table-striped table-bordered dataTable no-footer"})
    base_url = "https://apps.des.wa.gov"
    for table in allTables:
        # Find all Trs and then extract number and link
        allTrs = table.findAll('tr')
        for tr in allTrs:
            # Extract first td, as each row will have only one link to extract
            allTds = tr.findAll('td')
            for td in allTds:
                url = base_url + td.find('a')['href']
                contracts.append(url)
                url = ""
                break
    return contracts


def get_contract_description(contract_url, driver):
    """
    Extract description, number for each URL

    Parameters:
    contract_url : list of contract url
    driver: Selenium driver

    Returns:
    Return all contract details

   """
    driver.get(contract_url)
    contract_details = {}
    contract_details[contract_url] = {}
    title = driver.find_element_by_class_name("h3")
    contract_details[contract_url]["Title"] = title.text
    number = driver.find_element_by_xpath('/html/body/div[2]/div[2]/div[1]')
    id = number.text.split(":")
    contract_details[contract_url]["Contract#"] = id[1]
    desc = driver.find_element_by_xpath('/html/body/div[2]/div[3]/div')
    contract_details[contract_url]["Description"] = desc.text
    try:
        web_elements = []
        web_elements.append(driver.find_element_by_xpath('/html/body/div[2]/div[4]/div/div/div[1]'))
        web_elements.append(driver.find_element_by_xpath('/html/body/div[2]/div[4]/div/div/div[2]'))
        web_elements.append(driver.find_element_by_xpath('/html/body/div[2]/div[4]/div/div/div[3]'))
        web_elements.append(driver.find_element_by_xpath('/html/body/div[2]/div[5]/div/div/div[1]'))
        web_elements.append(driver.find_element_by_xpath('/html/body/div[2]/div[5]/div/div/div[2]'))
        web_elements.append(driver.find_element_by_xpath('/html/body/div[2]/div[5]/div/div/div[3]'))
        web_elements.append(driver.find_element_by_xpath('/html/body/div[2]/div[6]/div/div/div[1]'))
        web_elements.append(driver.find_element_by_xpath('/html/body/div[2]/div[6]/div/div/div[2]'))

        for x in web_elements:
            word = x.text.split(":")
            contract_details[contract_url][word[0]] = word[1]

    finally:
        return contract_details


def crawler_rpf(request):
    """
    Main method to initiate crawling for RFPs
    
    Parameters:
    request: HTTP request

    Returns:
    RFP web page

   """
    driver = webdriver.Chrome(ChromeDriverManager().install())
    all_contracts = get_contracts(driver)
    # Get existing data from database
    all_availableData_inDb = RFP.objects.all()
    urls_in_database = []
    
    for data in all_availableData_inDb:
        urls_in_database.append(data.url)
        
    
    for contract in all_contracts:
        if (contract not in urls_in_database):
            individual_element = get_contract_description(contract, driver)
            rpf_instance = RFP()
            url = list(individual_element.keys())[0]
            rpf_instance.url = url
            rpf_instance.title = individual_element[url]['Title']
            rpf_instance.contract_number = individual_element[url]['Contract#']
            rpf_instance.description = individual_element[url]['Description']
            rpf_instance.save()

    driver.quit()

    return rfp_result(request)
