import os
from flask import Flask, render_template, request, redirect, url_for, flash, abort, send_file, jsonify
from dotenv import load_dotenv
import boto3
from prometheus_client import generate_latest, Counter
from prometheus_client.exposition import CONTENT_TYPE_LATEST
import json
import urllib
import logging
from logging.handlers import RotatingFileHandler
from weather_api import Weather  # the weather back-end class we created
weather = Weather()

# Directory where the log file will be stored
log_dir = 'logs'

# Ensure the directory exists
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create handlers
console_handler = logging.StreamHandler()
file_handler = RotatingFileHandler(os.path.join(log_dir, 'app.log'), maxBytes=10000, backupCount=1)

# Set level for handlers
console_handler.setLevel(logging.INFO)
file_handler.setLevel(logging.DEBUG)

# Create formatters and add them to handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')

# Initialize Prometheus metrics
location_request_counter = Counter(
    'weather_app_location_requests_total',
    'Total number of requests for each location',
    ['location']
)

# Retrieve AWS credentials and region from environment variables
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_region = os.getenv('AWS_REGION')

# Create DynamoDB client using environment variables
dynamodb = boto3.resource(
    'dynamodb',
    region_name=aws_region,
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)

# Reference a DynamoDB table
table = dynamodb.Table('eli_db')

@app.route('/', methods=['GET', 'POST'])
def home():
    """ Home page to post the user request and the location he wants to check """
    if request.method == 'POST':
        location = request.form.get('location')
        logger.info(f'Received location from form: {location}')
        return redirect(url_for('result', location=location))
    return render_template('home.html')

@app.route('/result', methods=['GET'])
def result():
    """ Result page to display weather data and provide an option to save it """
    location = request.args.get('location')
    response_type = request.args.get('type', 'html')

    if not location:
        logger.warning('Location parameter is missing')
        abort(400, description="Location is required")

    location_request_counter.labels(location=location).inc()
    weather_data = weather.get_current_weather(location)
    if not weather_data:
        logger.error(f'Weather data not found for location: {location}')
        abort(404, description="Weather data not found")

    if response_type == 'json':
        logger.info(f'Returning JSON response for location: {location}')
        return jsonify(weather_data), 200
    else:
        logger.info(f'Rendering HTML template for location: {location}')
        return render_template('result.html', location=location, weather_data=weather_data)

@app.route('/save_weather_data', methods=['POST'])
def save_weather_data():
    """ Save weather data for a given location to DynamoDB """
    location = request.form.get('location')
    if not location:
        logger.warning('Location parameter is missing for saving weather data')
        abort(400, description="Location is required")

    weather_data = weather.get_current_weather(location)
    if weather_data:
        weather_data_str = json.dumps(weather_data)
        try:
            table.put_item(
                Item={
                    'location': location,
                    'weather_data': weather_data_str
                }
            )
            flash('Data saved successfully!', 'success')
            logger.info(f'Successfully saved weather data for location: {location}')
        except boto3.exceptions.Boto3Error as e:
            logger.error(f"Error inserting item into DynamoDB: {e}")
            abort(500, description="Error saving weather data")

    return redirect(url_for('result', location=location))

@app.route('/downloadskies', methods=['GET'])
def downloadskies():
    """ Download picture of the sky from S3 bucket """
    image_path = "sky.jpg"
    try:
        urllib.request.urlretrieve("https://d2stss09utuhb5.cloudfront.net/architecture_design.png", image_path)
        logger.info('Sky image downloaded successfully')
    except Exception as e:
        logger.error(f"Error downloading sky image: {e}")
        abort(500, description="Error downloading image")

    return send_file(
        image_path,
        as_attachment=True,
    )

@app.route('/weather_data/<location>', methods=['GET'])
def get_weather_data(location):
    """ Retrieve weather data for a given location from DynamoDB """
    try:
        response = table.get_item(
            Key={
                'location': location
            }
        )
        item = response.get('Item')
        if item:
            logger.info(f'Weather data retrieved for location: {location}')
            return jsonify(item), 200
        else:
            logger.info(f'No weather data found for location: {location}')
            return jsonify({'message': 'No data found'}), 404
    except Exception as e:
        logger.error(f"Error retrieving weather data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/metrics')
def metrics():
    """ Endpoint for Prometheus to scrape default metrics """
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
