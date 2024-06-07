import json
import boto3

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
table = dynamodb.Table('database')

THUMBNAIL_BUCKET = '5225-a3-thumbnails'
IMAGE_BUCKET = '5225-a3-image'

def lambda_handler(event, context):
    # Extract links from the body
    body = json.loads(event.get('body', '{}'))
    links = body.get('image_url')
    
    if not links:
        return {
            'statusCode': 400,
            'body': json.dumps('No links provided'),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Headers': '*'
            },
        }
    
    errors = []
    
    # Handle CORS preflight request
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Headers': '*'
            },
            'body': json.dumps('CORS preflight response')
        }
    
    for thumbnail_url in links:
        try:
            # Query DynamoDB to find the item with the provided thumbnail URL
            response = table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('thumbnail_url').eq(thumbnail_url)
            )
            if 'Items' not in response or len(response['Items']) == 0:
                errors.append(f'Image not found for thumbnail URL: {thumbnail_url}')
                continue
            
            item = response['Items'][0]
            image_id = item['id']
            s3_url = item.get('s3_url')
            
            # Delete the item from DynamoDB
            table.delete_item(Key={'id': image_id})
            
            # Extract S3 keys from URLs
            thumbnail_key = thumbnail_url.split('/')[-1]
            s3.delete_object(Bucket=THUMBNAIL_BUCKET, Key=thumbnail_key)
            
            if s3_url:
                image_key = s3_url.split('/')[-1].replace('thumb-', '')
                s3.delete_object(Bucket=IMAGE_BUCKET, Key=image_key)
        
        except Exception as e:
            errors.append(f'Error deleting image for thumbnail URL {thumbnail_url}: {str(e)}')
    
    if errors:
        return {
            'statusCode': 207,
            'body': json.dumps({'errors': errors}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Headers': '*'
            },
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps('All image records and files deleted successfully'),
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*',
            'Access-Control-Allow-Headers': '*'
        },
    }