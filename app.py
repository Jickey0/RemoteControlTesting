from flask import Flask, request, jsonify, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
from helpers import WeatherGetRequest
import json
import time

app = Flask(__name__)

UE_PROPS_BASE_URL = 'http://localhost:30010/remote/preset/MyRemote/property/Time of Day'

request_all_weather_data = {"objectPath" : "/Game/Main.Main:PersistentLevel.Ultra_Dynamic_Sky_C_1", "access" : "READ_ACCESS"}


def speed_test_change_time(start=0, increment=100, frequency_hz=1000, max_value=3000):
    current_value = start
    interval = 1.0 / frequency_hz  # seconds per request
    
    print(f"Starting speed test: increment {increment} every {interval*1000:.1f} ms")
    
    while current_value <= max_value:
        payload = WeatherGetRequest("Time of Day", current_value)
        try:
            response = requests.put(UE_PROPS_BASE_URL, json=payload)
            print(f"Set Time of Day to {current_value} - Status: {response.status_code}")
        except Exception as e:
            print(f"Request failed at {current_value}: {e}")
            break
        
        current_value += increment
        time.sleep(interval)


@app.route('/', methods=['GET', 'POST'])
def index():
    # fetches data from UE weather controller via sending a blank JSON
    result = None
    if request.method == 'POST':
        try:
            action = request.form["action"]
            if action == "request_all_weather_data":
                response = requests.put(UE_PROPS_BASE_URL, json=request_all_weather_data)
                print("Status Code:", response.status_code)
                response.raise_for_status()
                result = response.json()
                
                # Save JSON data to a file
                with open("Data/WeatherControllerVals.json", "w", encoding="utf-8") as file:
                    json.dump(result, file, ensure_ascii=False, indent=4)

                print("JSON data has been saved to 'data.json'")

            elif action == "StressTest":
                speed_test_change_time()

        except requests.RequestException as e:
            result = {"error": str(e)}
            
    return render_template('index.html', result=result)

@app.route("/changeWeather", methods=["GET", "POST"])
def changeWeather():
    if request.method == "GET":
        # Render the HTML page (your form and JS)
        return render_template("changeWeather.html")

    if request.method == "POST":
        try:
            number = request.form["number"]
            result = f"Changing Time of Day to: {number}"
            
            # format to JSON request
            change_time_of_day = WeatherGetRequest("Time of Day", number)

            # send request change "Time of Day"
            response = requests.put(UE_PROPS_BASE_URL, json=change_time_of_day)
            print("Status Code:", response.status_code)

        except ValueError:
            result = "Please enter a valid number."

        return render_template("changeWeather.html", result=result)


@app.route('/update-time', methods=['POST', 'GET'])
def update_time():
    return render_template("update-time.html")

# Set up limiter with default key function to use client IP
limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)

last_val = 0
session = requests.Session()

@app.route('/update-value', methods=['POST'])
@limiter.limit("1 per second")  # limit to 1 requests per second per client IP
def update_value():
    global last_val
    global session

    data = request.get_json()
    value = float(data.get('value'))
    print(value)

    if value != last_val:
        print(f"Changing Time of Day to: {value}")
        change_time_of_day = WeatherGetRequest("Time of Day", value)

        response = session.put(UE_PROPS_BASE_URL, json=change_time_of_day)
        print("Status Code:", response.status_code)
        
        return jsonify({"status": "success", "received": value})
    else:
        last_val = value


if __name__ == '__main__':
    app.run(port=5000)
