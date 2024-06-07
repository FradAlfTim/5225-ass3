import json
import boto3
from base64 import b64decode
from io import BytesIO
from botocore.exceptions import ClientError

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    # Log the incoming event for debugging
    print("Received event: " + json.dumps(event, indent=2))

    # Handle CORS preflight request
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps('CORS preflight response')
        }

    # Get the base64 encoded image and image name from the request body
    try:
        body = json.loads(event['body'])
        encoded_image = body['image']
        image_name = body['image_name']
        user_email = body['user_email']
    except KeyError as e:
        print(f"Missing required key in request body: {e}")
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps('Request body must contain "user_email", "image" and "image_name" keys')
        }

    # Decode the base64 image data
    try:
        decoded_image_data = b64decode(encoded_image)
    except Exception as e:
        print(f"Error decoding base64 image: {e}")
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps('Error decoding base64 image')
        }

    # Upload the decoded image to S3
    try:
        s3_client.put_object(
            Body=BytesIO(decoded_image_data),
            Bucket='5225-a3-image',
            Key=image_name,
            Metadata={"user_email": user_email}
        )
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps(f'Image "{image_name}" uploaded successfully!')
        }
    except ClientError as e:
        print(f"Error uploading image to S3: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps('Error uploading image to S3')
        }
