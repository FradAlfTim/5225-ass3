import boto3
import json
import cv2
import numpy as np
from botocore.exceptions import ClientError
from io import BytesIO
from urllib.parse import unquote_plus

s3_client = boto3.client('s3')
# Define SNS client and the topic ARN
sns_client = boto3.client('sns')
TOPIC_ARN = 'arn:aws:sns:us-east-1:534701713148:ForLambdaTopic'

def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])

        try:
            response = s3_client.get_object(Bucket=bucket, Key=key)
            img_data = response['Body'].read()
            
            # Convert image to numpy array and read with OpenCV
            np_array = np.fromstring(img_data, np.uint8)
            image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
            
            # Generate thumbnail
            thumbnail = cv2.resize(image, (128, 128), interpolation=cv2.INTER_AREA)
            
            # Convert thumbnail to bytes using imencode (already done in your code)
            _, buffer = cv2.imencode('.jpg', thumbnail)
            thumbnail_bytes = BytesIO(buffer)

            # Upload the thumbnail_bytes (which is already image data) to S3 using put_object
            thumbnail_bucket = 'tianfu-thumbnail-bucket'
            thumbnail_key = "thumb-" + key  # You can keep the same key name here
            s3_client.put_object(Bucket=thumbnail_bucket, Key=thumbnail_key, Body=thumbnail_bytes.getvalue())
            
            # Publish message to SNS
            message = json.dumps({'object_key': key})
            sns_client.publish(TopicArn=TOPIC_ARN, Message=message)
        
        except ClientError as e:
            print(e)
            return {
                'statusCode': 400,
                'body': json.dumps('Error processing image')
            }
        
    return {
            'statusCode': 200,
            'body': json.dumps('Thumbnail generated successfully')
        }
