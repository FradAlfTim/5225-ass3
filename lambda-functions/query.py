import json
import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource('dynamodb')
table_name = 'database' 
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    print('event')
    
    # print('remaining time =', context.getRemainingTimeInMillis())
    # print('functionName =', context.functionName)
    # print('AWSrequestID =', context.awsRequestId)

    status_code = 200
    response_body = {}
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': '*',
        'Access-Control-Allow-Headers': '*'
    }

    try:
        if 'httpMethod' not in event:
            raise ValueError('httpMethod is missing from the event')
        # Handle CORS preflight request
        if event['httpMethod'] == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': '*',
                    'Access-Control-Allow-Headers': '*'
                },
                'body': json.dumps('CORS preflight response')
            }
        if event['httpMethod'] == 'POST':
            body = json.loads(event['body']) if 'body' in event else {}
            if 'tags' in body:
                tags = body['tags']
                if not isinstance(tags, list):
                    tags = [tags]

                if tags:
                    filter_expression = None

                    for tag in tags:
                        if filter_expression is None:
                            filter_expression = Attr('tags').contains(tag)
                        else:
                            filter_expression = filter_expression & Attr('tags').contains(tag)

                    response = table.scan(
                        FilterExpression=filter_expression
                    )
                    response_body = [item['thumbnail_url'] for item in response['Items']]
                else:
                    raise ValueError('Tags are required')
            else:
                raise ValueError('Tags are missing')

    except Exception as e:
        status_code = 400
        response_body = {'error': str(e)}

    return {
        'statusCode': status_code,
        'body': json.dumps(response_body),
        'headers': headers,
    }