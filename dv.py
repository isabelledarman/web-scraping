from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import json

'''
def save_to_mongodb(stations_data, departures_data):
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['nj_transit_db']
        
        stations_collection = db['stations']
        departures_collection = db['departures']
        
        stations_to_insert = []
        for station in stations_data:
            stations_to_insert.append({
                'name': station.name,
                'is_accessible': station.is_accessible,
                'updated_at': datetime.now()
            })
        
        if stations_to_insert:
            stations_collection.insert_many(stations_to_insert)
            print(f"Saved {len(stations_to_insert)} stations to MongoDB")
        
        if not departures_data.empty:
            departures_collection.insert_many(
                departures_data.to_dict('records')
            )
            print(f"Saved {len(departures_data)} departures to MongoDB")
            
        return True
        
    except Exception as e:
        print(f"Error saving to MongoDB: {e}")
        return False
'''

def save_to_csv(stations_data, departures_data):
    try:
        stations_df = pd.DataFrame([
            {'name': s.name, 'is_accessible': s.is_accessible} 
            for s in stations_data
        ])
        stations_df.to_csv('nj_transit_stations.csv', index=False)
        print(f"Saved {len(stations_df)} stations to CSV")
        
        if not departures_data.empty:
            departures_data.to_csv('nj_transit_departures.csv', index=False)
            print(f"Saved {len(departures_data)} departures to CSV")
            
        return True
        
    except Exception as e:
        print(f"Error saving to CSV: {e}")
        return False

class Station:
    def __init__(self, name, is_accessible=False):
        self.name = name
        self.is_accessible = is_accessible
    def __str__(self):
        return self.name

def get_all_stations():
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-notifications')  # Disable popups
        driver = webdriver.Chrome(options=options)

        print("Fetching NJ Transit stations...")
        driver.get('https://www.njtransit.com/dv-to')

        wait = WebDriverWait(driver, 10)
        station_input = wait.until(
            EC.presence_of_element_located((By.ID, 'dv-to-station'))
        )

        driver.execute_script("arguments[0].click();", station_input)
        time.sleep(2)

        station_input.click()
        time.sleep(2)

        station_items = driver.find_elements(By.CSS_SELECTOR, 'li[data-cy="autocomplete-item"]')

        stations = []

        for item in station_items:
            try:
                name = item.find_element(By.TAG_NAME, 'a').text.strip()
                is_accessible = len(item.find_elements(By.CSS_SELECTOR, 'svg[aria-labelledby="accessibility-title"]')) > 0
                stations.append(Station(name, is_accessible))
                print(f"Found station: {name}, Accessible: {is_accessible}")
            except Exception as e:
                print(f"Error processing station item: {e}")
                continue
        
        driver.quit()

        if not stations:
            print("\nNo stations found. Using default stations.")
            return [
                Station("Newark Penn Station", True),
                Station("New York Penn Station", True),
                Station("Hoboken Terminal", True)
            ]
        
        print(f"\nSuccessfully found {len(stations)} stations")
        return stations
    
    except Exception as e:
        print(f"Error fetching stations: {e}")
        print(f"Full error details: {str(e)}")
        return []

STATIONS = [
    {"name": "Newark Penn Station", "accessible": True},
    {"name": "New York Penn Station", "accessible": True},
    {"name": "Hoboken Terminal", "accessible": True},
    {"name": "Secaucus Junction", "accessible": True},
    {"name": "Newark Broad St", "accessible": True},
    {"name": "Princeton Junction", "accessible": True},
    {"name": "Metropark", "accessible": True},
    {"name": "Trenton Transit Center", "accessible": True},
    {"name": "Aberdeen-Matawan", "accessible": True},
    {"name": "Summit", "accessible": True}
]

class Station:
    def __init__(self, name, is_accessible=False):
        self.name = name
        self.is_accessible = is_accessible
    
    def __str__(self):
        return self.name

def get_all_stations():
    return [Station(s["name"], s["accessible"]) for s in STATIONS]

    
def get_station_departures(station):

    trains = []
    try:
        encoded_station = requests.utils.quote(station.name)
        url = f'https://www.njtransit.com/dv-to/{encoded_station}'
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
                
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'lxml')
        departures = soup.find_all('div', class_='media no-gutters p-3')

        print(f"\n{station.name} Train Departures:")
        print("-" * 50)

        if not departures:
            print("No departures found.")
            return pd.DataFrame()

        for departure in departures:
            train_line_elem = departure.find('p', class_='mb-0')
            time_info_elem = departure.find('div', class_='d-flex flex-column ml-3 text-right')
            track_elem = departure.find('p', class_='align-self-end mt-1 mb-0')

            # Extract text only if elements exist
            train_line = train_line_elem.text.strip() if train_line_elem else "Unknown Train"
            time_info = time_info_elem.text.strip() if time_info_elem else "Time Not Available"
            track = track_elem.text.strip() if track_elem else "Track Not Available"

            print(f"Train: {train_line}")
            print(f"Time: {time_info}")
            print(f"Track: {track}")
            print("-" * 50)

            trains.append({"Train": train_line, "Time": time_info, "Track": track, "Station": station.name, "Accessible": station.is_accessible})
        
        df = pd.DataFrame(trains)
        return df
    
    except requests.RequestException as e:
        print(f"Error fetching data for {station.name}: {e}")
    except AttributeError as e:
        print(f"Error parsing data for {station.name}: {e}")

if __name__ == "__main__":
    print("Fetching all NJ Transit stations...")
    stations = get_all_stations()
    print(f"\nFound {len(stations)} stations")
    
    all_departures = []
    for station in stations:
        df = get_station_departures(station)
        if isinstance(df, pd.DataFrame) and not df.empty:
            all_departures.append(df)
        time.sleep(2)  # Be respectful to the server
    
    # Combine all departures into one DataFrame
    if all_departures:
        combined_departures = pd.concat(all_departures, ignore_index=True)
        
        # Save data to MongoDB
        #save_to_mongodb(stations, combined_departures)
        
        # Backup to CSV
        save_to_csv(stations, combined_departures)
    else:
        print("No departure data to save")