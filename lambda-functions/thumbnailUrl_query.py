import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('database')

def lambda_handler(event, context):
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': '*'
            },
            'body': json.dumps('CORS preflight response')
        }
    
    if event['httpMethod'] != 'POST':
        return {
            'statusCode': 405,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': '*'
            },
            'body': json.dumps('Method Not Allowed')
        }
    
    body = json.loads(event['body'])
    thumbnail_url = body.get('thumbnail_url')
    
    if not thumbnail_url:
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': '*'
            },
            'body': json.dumps('No thumbnail URL provided')
        }
    
    # Query using the GSI on thumbnail_url
    response = table.query(
        IndexName='thumbnail_url-index',  # Replace with the actual GSI index name
        KeyConditionExpression=Key('thumbnail_url').eq(thumbnail_url)
    )
    
    if 'Items' not in response or len(response['Items']) == 0:
        return {
            'statusCode': 404,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': '*'
            },
            'body': json.dumps('Image not found')
        }
    
    item = response['Items'][0]
    full_image_url = item['s3_url']
    
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Methods': '*'
        },
        'body': json.dumps({'full_image_url': full_image_url})
    }