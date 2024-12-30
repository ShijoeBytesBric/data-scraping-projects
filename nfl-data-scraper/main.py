import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time


start_year = 2012
end_year = 2024

min_count = 1
max_count = 17

extra_path = ['post1', 'post2', 'post3', 'post4', 'pro1']


def get_page_contents(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        print(f'Successfully retrieved the page_content \nurl: {url}\n')
        return response.content
    print(f'No content was retrieved \nurl: {url}\n')
    return None


link_path_list = []
for year in range(start_year, end_year + 1):
    path_list = []
    
    for num in range(min_count, max_count + 1):
        link_path = f'/injuries/league/{year}/reg{num}'
        path_list.append(link_path)
    
    for path in extra_path:
        link_path = f'/injuries/league/{year}/{path}'
        path_list.append(link_path)
    
    path_data = {
        'year': year,
        'path_list': path_list
    }
    link_path_list.append(path_data)


for link in link_path_list:
    combined_list = []
    for path in link['path_list']:

        sub_url = f'https://www.nfl.com{path}'
        sub_html_content = get_page_contents(sub_url)

        if sub_html_content:
            page_soup = BeautifulSoup(sub_html_content, 'html.parser')
            injury_report_wrap = page_soup.find(class_='nfl-o-injury-report__wrap')

            if injury_report_wrap is not None:

                date_data = injury_report_wrap.find(class_='d3-o-section-title').text
                print(date_data)

                report_wraps_list = injury_report_wrap.find_all(class_='nfl-o-injury-report__unit')
                print(len(report_wraps_list))

                json_list = []

                for report_wrap in report_wraps_list:
                    time_data = report_wrap.find(class_='nfl-c-matchup-strip__date-time').text
                    print(time_data)

                    team_names_list = report_wrap.find_all(class_='d3-o-section-sub-title')
                    team_names = [name.text.strip() for name in team_names_list]
                    print(team_names)

                    team_list = report_wrap.find_all('table')
                    print(len(team_list))

                    if len(team_list) > 0:

                        for team_data, team_name in zip(team_list, team_names):

                            headers = [th.text.strip() for th in team_data.find_all("th")]

                            rows = []
                            for row in team_data.find_all("tr")[1:]:
                                cells = [td.text.strip() for td in row.find_all("td")]
                                if cells:
                                    rows.append(cells)
                            
                            df = pd.DataFrame(rows, columns=headers)
                            new_columns = {
                                'Day': date_data,
                                'Time': time_data,
                                'Team': team_name,
                                'url': sub_url
                            }
                            df = df.assign(**new_columns)
                            json_data = df.to_json(orient="records")
                            json_list.append(json_data)
                            print(json_data)
                    else:
                        for team_name in team_names:
                            json_data ="[{" + f'"Player": "", "Position": "", "Injuries": "", "Practice Status": "", "Game Status": "", "Day": "{date_data}", "Time": "{time_data}", "Team": "{team_name}", "url": "{sub_url}"' + "}]"
                            json_list.append(json_data)
                            print(json_data)
                

                
                for json_data in json_list:
                    parsed_list = json.loads(json_data)
                    print(json_data)

                    combined_list.extend(parsed_list)
            
    final_df = pd.DataFrame(combined_list)
    print(f'Creating nfl_{link['year']}.xlsx...')
    final_df.to_excel(f'nfl_{link['year']}.xlsx', index=False)
    
    time.sleep(2)


