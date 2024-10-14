"""the code implement the backend"""
from datetime import date  # using date functions
import requests  #
from deep_translator import GoogleTranslator  #for getting the country in english
import os
import json
import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend suitable for saving images
import matplotlib.pyplot as plt


class Weather:
    """ class have 2 method, it send a quary to visualcrossing API and after it get
    a result using deeper filter tothe result and orgnazie it as list of lists and we
     have 4 atrribute class the api key, base url, quary to the api
     and the new url
    """
    key = "&key=VD22NUNAV3EX79PGNAHZHZD9N&contentType=json"
    base = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"
    quary = "/next7days?unitGroup=metric&elements=datetime%2Ctemp%2Chumidity&include=days%2Chours%2Cfcst%2Cobs"
    url = None

    def __init__(self):
        self.cache = {}
        self.location = None
        self.limit = 0
        self.last_cleared_date = date.today()

    def get_current_weather_json(self, location_n):
        """ Retrieve weather data and return it in JSON format """
        weather_data = self.get_current_weather(location_n)
        if weather_data:
            return json.dumps(weather_data)  # Convert the list of lists to a JSON string
        return json.dumps({'error': 'No data found'})

    def filter_data(self, dicit):
        """ get a joson object and refilter the data and reformat to
         jason to list of lists and call the chart method"""
        new_dicit = {}
        for i in range(7):
            new_dicit[i] = {"datetime": dicit['days'][i]['datetime'],
                            "morning": dicit['days'][i]['hours'][13],
                            "evning": dicit['days'][i]['hours'][23]}
        #creating the lists for the cache
        list_l = new_dicit
        list_date = ["date"]
        list_morning_temp = ["day temp °C"]
        list_evning_temp = ["night temp °C"]
        list_morning_hum = ["day humidity %"]
        list_evning_hum = ["night humidity %"]
        list_location = []
        list_data = [list_location, list_date, list_morning_temp, list_morning_hum,
                     list_evning_temp,
                     list_evning_hum]
        city_or_country = dicit['resolvedAddress']
        translated_result = GoogleTranslator(source='auto', target='en').translate(city_or_country)
        list_location.append(str(dicit['resolvedAddress']))
        list_location.append(translated_result)
        for i in list_l:
            list_date.append(new_dicit[i]['datetime'])
            list_morning_temp.append(new_dicit[i]['morning']['temp'])
            list_evning_temp.append(new_dicit[i]['evning']['temp'])
            list_morning_hum.append(new_dicit[i]['morning']['humidity'])
            list_evning_hum.append(new_dicit[i]['evning']['humidity'])

        #call the chart methode
        self.chart(list_date[1:], list_morning_temp[1:], list_evning_temp[1:])
        return list_data

    def get_current_weather(self, location_n):
        """the founcuon get a location check if it in the cache if it is in call the cart function and return the value
        else it make a conection to visual crossing api with the uary send the resul jason to the filter function and
        than return the formt data"""
        if date.today() != self.last_cleared_date or self.limit > 50:
            self.clear_cache()
            self.last_cleared_date = date.today()  # Update the date after clea
        # get a location and check it in the visoulcrossing API if we
        # get an error we will return an empty jason_data and for displaying the country we are using
        # Google Translator API
        if location_n in self.cache:
            #print('Cache hit')
            #print(self.cache[location_n])
            #print(self.cache[location_n][1][1:], self.cache[location_n][2][1:], self.cache[location_n][4][1:])
            #self.chart(self.cache[location_n][1][1:], self.cache[location_n][2][1:], self.cache[location_n][4][1:])
            return self.cache[location_n]

        self.location = location_n
        url = self.base + self.location + self.quary + self.key

        response = requests.get(url)

        if response.status_code != 200:
            print('Unexpected Status code:', response.status_code)
            return None

        if not os.path.exists('static'):
            os.makedirs('static')
        jason_data = response.json()
        f_weather_data = self.filter_data(jason_data)
        self.cache[location_n] = f_weather_data
        f_weather_data = self.convert_floats_to_strings(f_weather_data)
        return f_weather_data

    def chart(self, categories, values1, values2):
        """create a new chart for temp save it in static directory"""
        # categories = list_date[2:]
        # values1 = list_morning_temp[2:]
        # values2 = list_evning_temp[2:]

        plt.figure(figsize=(10, 6))
        #morning temp line
        plt.plot(categories, values1, marker='o', color='blue',
                 linestyle='-', linewidth=2, label='day °C ')

        #evning temp line
        plt.plot(categories, values2, marker='o', color='red',
                 linestyle='-', linewidth=2, label='night °C ')

        # Add title and labels
        plt.xlabel('Dates')
        plt.ylabel('Temp °C')

        # Delete the file if it already exists
        # if os.path.isfile('static/pic.png'):
        #     os.remove('static/pic.png')
        plt.legend()
        # save the image
        plt.savefig('static/' + self.location + '.png')  #{{ location }}
        plt.savefig('static/pic.png')
        plt.close()
    def clear_cache(self):
        """clear the chace"""
        self.cache.clear()
    directory = 'static'
    # List all files in the directory
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)


    def convert_floats_to_strings(self, obj):
        """ Recursively convert float values to strings """
        if isinstance(obj, float):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: self.convert_floats_to_strings(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_floats_to_strings(x) for x in obj]
        else:
            return obj
