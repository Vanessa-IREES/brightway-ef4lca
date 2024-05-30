import json
import os
import requests

def load_config(config_path):    
    # Load the JSON configuration file
    with open( os.path.join(config_path,'config.json'), 'r') as f:
        config = json.load(f)

    ics = config['impact_cats'];

    config['ic_names'] = list(ics.keys())
    config['obd_units'] = [item['unit'] for item in ics.values()]
    config['obd_cats'] = [item['category'] for item in ics.values()]

    config['ic_biosphere_map'] = {key: value['bs_ref'] for key, value in ics.items()}

    return config

def download_csv_file(config):
    # Send a GET request to the URL
    csv_file_url = config['csv_file_url']
    print(f'Download csv from: {csv_file_url}...')
    response = requests.get(csv_file_url)
    
    # Check if request was successful (status code 200)
    if response.status_code == 200:
        # Open a file in binary write mode and write the contents of the response
        file_name = config['csv_file_name']
        with open(file_name, 'wb') as f:
            f.write(response.content)
        print('File downloaded successfully as', file_name)
    else:
        print('Failed to download the file. Status code:', response.status_code)
