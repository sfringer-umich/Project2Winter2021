#################################
##### Name: Sarah Fringer
##### Uniqname: sfringer
#################################

from bs4 import BeautifulSoup
import requests
import re
import json
import secrets # file that contains your API key

CACHE_FILENAME = "project2_cache.json"
CACHE_DICT = {}

class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category="No Category", name="No Name", address="No Address", zipcode="No Zipcode", phone="No Phone Number"):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone
    
    def info(self):
        ''' This function prints out information such as the category, name,
            address, zipcode, and phone number of the national site  

        Parameters
        ----------
        None 

        Returns
        -------
        The information of the object in the format: name (category): address zip  
        '''

        return self.name + " " + "(" + self.category + "): " + self.address + " " + self.zipcode


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    dict = {}
    url = "https://www.nps.gov/index.htm"
    
    if url in CACHE_DICT.keys():
        print("Using Cache")
        return CACHE_DICT[url]
    
    else:
        print("Fetching")
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        state_elements = soup.find_all(id='HERO')
        state_items = state_elements[0].find_all('li')

        for item in state_items:
            html_tag = item.find('a')
            state = item.text.strip()

            state_link = html_tag['href']
            dict[state] = "https://www.nps.gov" + state_link
        
        dict =  {i.lower(): j for i, j in dict.items()}
        response = requests.get(url)
        CACHE_DICT[url] = dict
        save_cache(CACHE_DICT)
        return CACHE_DICT[url]
    
    return dict


def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    
    if site_url in CACHE_DICT.keys():
        print("Using Cache")

    else:
        print("Fetching")
        response = requests.get(site_url)
        CACHE_DICT[site_url] = response.text
        save_cache(CACHE_DICT)
    
    soup = BeautifulSoup(CACHE_DICT[site_url], 'html.parser')
    park_type = (soup.find('span',{'class':'Hero-designation'}).text) if (soup.find('span',{'class':'Hero-designation'})) else "No Type"
    park_name = (soup.find('a',{'class':'Hero-title'}).text) if (soup.find('a',{'class':'Hero-title'})) else "No Name"
    park_number = (soup.find('span',{'class':'tel'}).text) if (soup.find('span',{'class':'tel'})) else "No Number"
    park_number = park_number.strip()
    park_zip = (soup.find('span',{'itemprop':'postalCode'}).text) if (soup.find('span',{'itemprop':'postalCode'})) else "No Zip"
    park_zip = park_zip.strip()
    park_state = (soup.find('span',{'itemprop':'addressRegion'}).text) if (soup.find('span',{'itemprop':'addressRegion'})) else "No State"
    park_city = (soup.find('span',{'itemprop':'addressLocality'}).text) if (soup.find('span',{'itemprop':'addressLocality'})) else "No City"
    park_address = park_city + ", " + park_state
    instance = NationalSite(park_type, park_name, park_address, park_zip, park_number)

        
    return instance



def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    park_list
        a list of national site instances
    '''
    
    if state_url in CACHE_DICT.keys():
        print("Using Cache")

    else:
        print("Fetching")
        response = requests.get(state_url)
        CACHE_DICT[state_url] = response.text
        save_cache(CACHE_DICT)
        
    soup = BeautifulSoup(CACHE_DICT[state_url], 'html.parser')
    BASE_URL = "https://www.nps.gov"
    park_list = []

    ## For each park listed
    park_listing_parent = soup.find('div', class_='col-md-9 col-sm-12 col-xs-12 stateCol')
    park_listing_divs = park_listing_parent.find_all('div', recursive=False)
    park_url_items = park_listing_divs[1].find_all('h3')

    for item in park_url_items:   
        ## extract the park details URL
        park_link_tag = item.find('a')
        park_details_path = park_link_tag['href']
        park_details_url = BASE_URL + park_details_path

        park_instance = get_site_instance(park_details_url)
        park_list.append(park_instance)

    return park_list
    


def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    field_dict = {}
    zipcode = site_object.zipcode

    if zipcode in CACHE_DICT.keys():
        print("Using Cache")
        if zipcode == "No Zip":
            print("This site did not contain a zip code. Therefore we could not find any nearby places. Please try again!")
        if len(CACHE_DICT[zipcode]) == 0:
            print("There are no nearby places within the radius of the site. Please try again")
        return CACHE_DICT[zipcode]

    else:
        print("Fetching")
        if zipcode == "No Zip":
            print("This site did not contain a zip code. Therefore we could not find any nearby places. Please try again!")
            field_dict = {}

        else:
            response = requests.get("http://www.mapquestapi.com/search/v2/radius?key=" + str(secrets.API_KEY) + "&origin=" + str(zipcode) + "&radius=10&maxMatches=10&ambiguities=ignore&outFormat=json")
            
            json_str = response.text
            json_dict = json.loads(json_str)
            if 'searchResults' not in json_dict:
                print("There are no nearby places within the radius of the site. Please try again")
                field_dict = {}
            
            else:
                sR_dict = json_dict['searchResults']
                fields_info = []
                counter = 1

                for j in sR_dict:
                    fields_info.append(j['fields'])

                for i in fields_info:
                    place_name = i['name']
                    place_category = i['group_sic_code_name']

                    if i['address'] == "":
                        place_street = "No Address"
                    else: 
                        place_street = i['address']
                    
                    if i['city'] == "":
                        place_city = "No City"
                    else: 
                        place_city = i['city']
                    
                    field_dict[counter] = (place_name + " " + "(" + place_category + "): " + place_street + ", " + place_city)
                    counter += 1

        CACHE_DICT[zipcode] = field_dict
        save_cache(CACHE_DICT)
        return CACHE_DICT[zipcode]
            
    return field_dict

 
def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close() 


if __name__ == "__main__":
    CACHE_DICT = open_cache()
    dict = build_state_url_dict()
    num_input = ""

    while True:
        if num_input == "exit":
            break
        
        user_input = str(input("Enter a state name (e.g. Michigan, michigan), or \'exit' to quit: "))
        print("\n")
        user_input = user_input.lower()

        if user_input == "exit":
            print("Bye!")
            print("\n")
            break
        
        try:
            if user_input != "exit" and user_input in dict.keys():
                print('-' * 40)
                print("List of national sites in", user_input)
                print('-' * 40)
                counter = 1
                park_list = get_sites_for_state(dict[user_input])
            
                for i in park_list:
                    print("[",counter,"]", i.info())
                    counter += 1
                print("\n")

                while True:
                    num_input = input("Choose the number for detail search or \'exit' or back: ")
                    print("\n")

                    try:
                        num_input = int(num_input)

                        if num_input < counter:
                            nearby_place_instance = park_list[num_input-1]
                            field_dict = get_nearby_places(nearby_place_instance)
                            
                            if len(field_dict) == 0:
                                print("\n")
                            
                            else:
                                print('-' * 40)
                                print("Places near", nearby_place_instance.name)
                                print('-' * 40)

                                for i in field_dict.values():
                                    print("-", i)
                                print("\n")
                        
                        else:
                            print("[Error] Invalid Input")
                            print("\n")

                    except ValueError:
                        if num_input == "exit":
                            print("Bye!")
                            print("\n")
                            break
                        
                        elif num_input == "back":
                            break
                        
                        else:
                            print("[Error] Invalid Input")
            
            elif user_input != "exit" and user_input not in dict.keys():
                print("[Error] Enter proper state name")
                print("\n")
            
        except ValueError:
            print("Invalid Input!")
            break
            
      

     
    


    
    
    


        
