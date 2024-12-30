import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
from tqdm import tqdm
import pickle
import os
import re

class MangaScraper():

    def __init__(self) -> None:
        pass

    def get_post_content_details(self, url: str):

        response = requests.get(url)
        html_content = response.text
        soup = BeautifulSoup(html_content, 'lxml')

        manga_title = soup.select_one('div.post-title h1').get_text(strip=True)
        post_content_item = soup.find_all('div', class_='post-content_item')

        json_list = {}
        for item in post_content_item:
            title = item.find('div', class_='summary-heading').get_text(strip=True)
            content = item.find('div', class_='summary-content').get_text(strip=True)

            if title.lower() == 'rating':
                content = item.find(id='averagerate').get_text(strip=True)

            if title.lower() == 'genre(s)':
                genre_element_list = item.find_all('a')
                content = [genre.get_text(strip=True) for genre in genre_element_list]

            data = {
                title: content
            }

            json_list.update(data)
        
        rating = json_list.get('Rating', '')
        alternative_name = json_list.get('Alternative', '')
        genre = json_list.get('Genre(s)', '')
        type = json_list.get('Type', '')
        release_year = json_list.get('Release', '')
        status = json_list.get('Status', '')

        manga_data = {
            'title': manga_title,
            'alternative_name': alternative_name,
            'rating': rating,
            'genre': genre,
            'type': type,
            'release_year': release_year,
            'status': status
        }
        return manga_data
    
    def get_chapter_details(self, url: str):

        chapter_list = {}

        # URL for the AJAX call
        ajax_call_url = f'{url}ajax/chapters/'

        # Set up headers similar to the original request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Referer": url,
            "X-Requested-With": "XMLHttpRequest",
        }

        # Send the POST request
        ajax_call_response = requests.post(ajax_call_url, headers=headers)

        # Check if the request was successful
        if ajax_call_response.status_code == 200:
            # Parse the HTML content
            ajax_soup = BeautifulSoup(ajax_call_response.content, 'html.parser')
            
            # Render the desired divs (you can modify the selector based on your needs)
            li_elements = ajax_soup.find_all('li', class_='wp-manga-chapter')  # Adjust this selector to target specific divs
            for element in li_elements:
                chapter_link = element.find('a').get('href')
                chapter_name = element.find('a').text.strip()

                release_date_element = element.find('a', class_='c-new-tag')
                if release_date_element:
                    release_date_info = release_date_element.get('title')

                    duration_num = int(release_date_info.split()[0])
                    duration_text = release_date_info.split()[1]
                    if duration_text.lower() in ['day', 'days']:
                        if duration_num > 0:
                            now = datetime.now()
                            correct_date = now - timedelta(days=duration_num)
                            release_date = correct_date.strftime("%B %d, %Y")
                    elif duration_text.lower() in ['hour', 'hours', 'mins', 'secs']:
                        if duration_num > 0:
                            now = datetime.now()
                            release_date = now.strftime("%B %d, %Y")
                else:
                    release_date = element.find('span', class_='chapter-release-date').text.strip()

                chapter_data = {
                    chapter_name:{
                        'chapter_link': chapter_link,
                        'release_date': release_date
                    }
                }
                chapter_list.update(chapter_data)
            
            return chapter_list
        else:
            print(f"Request failed with status code: {ajax_call_response.status_code}")
            return chapter_list
        
    def is_valid_filename(self, filename: str):
        # Check if the filename is empty
        if not filename:
            return False
        
        # Define a regex pattern for invalid characters
        invalid_chars = r'[<>:"/\\|?*]'
        
        # Check for invalid characters
        if re.search(invalid_chars, filename):
            return False
        
        # Check for reserved names on Windows
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        if os.name == 'nt' and filename.upper() in reserved_names:
            return False
        
        return True
    
    def get_valid_filename(self, base_name: str, extension: str):
        # Remove invalid characters from the base name
        cleaned_name = re.sub(r'[<>:"/\\|?*]', '', base_name)
        
        # Check if the cleaned name is valid
        if self.is_valid_filename(cleaned_name):
            return cleaned_name + extension
        else:
            # If the cleaned name is still invalid, add a timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"{cleaned_name}_{timestamp}{extension}"
    


if __name__ == '__main__':

    df = pd.read_csv('manga_urls.csv')

    start_index = 6106
    manga_urls_list = df['url'].to_list()

    if start_index:
        manga_urls = manga_urls_list[6106:]
    else:
        manga_urls = manga_urls_list
    print(f"Starting to process {len(manga_urls)} data...")

    scraper = MangaScraper()

    for url in tqdm(manga_urls):
        print(url)
        manga_data = scraper.get_post_content_details(url=url)
        chapter_data = {
            'chapters': scraper.get_chapter_details(url=url)
        }
        manga_data.update(chapter_data)

        filename = manga_data['title']
        extension = ".pkl"

        valid_filename = scraper.get_valid_filename(filename, extension)

        with open(f'pkl_dump\\{valid_filename}', 'wb') as file:
            pickle.dump(manga_data, file)
    
