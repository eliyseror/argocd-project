import json
import urllib3
import boto3
from botocore.exceptions import ClientError

# Initialize HTTP client and DynamoDB client
http = urllib3.PoolManager()
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('eli_db')


def lambda_handler(event, context):
    # Define the location and the URL to fetch data from
    location = event.get('location', 'paris')  # Default to 'paris' if not provided
    url = f"http://mytrueapp-env.eba-uqgxk3pa.us-east-1.elasticbeanstalk.com/result?location={location}&type=json"

    try:
        # Make the HTTP request
        response = http.request('GET', url)

        if response.status == 200:
            # Parse JSON data
            data = json.loads(response.data.decode('utf-8'))

            # Store data in DynamoDB
            store_in_dynamodb(location, data)

            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Data stored successfully!'})
            }
        else:
            return {
                'statusCode': response.status,
                'body': json.dumps({'message': 'Failed to retrieve data'})
            }
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def store_in_dynamodb(location, data):
    """ Store weather data in DynamoDB """
    try:
        table.put_item(
            Item={
                'id': location,
                'weather_data': json.dumps(data)
            }
        )
    except ClientError as e:
        print(f"Failed to store data in DynamoDB: {e}")
        raise
