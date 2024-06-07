import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('database')

def lambda_handler(event, context):
    # Extract body from event and parse it as JSON
    body = json.loads(event.get('body', '{}'))
    urls = body.get('url', [])
    tags = body.get('tags', [])
    action_type = body.get('type')  # 1 for add, 0 for remove

    if not urls or not tags or action_type not in [0, 1]:
        return {
            'statusCode': 400,
            'body': json.dumps('Invalid input'),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Headers': '*'
            },
        }

    for url in urls:
        # Query using the GSI on thumbnail_url to get the item
        response = table.query(
            IndexName='thumbnail_url-index',  # Replace with the actual GSI index name
            KeyConditionExpression=Key('thumbnail_url').eq(url)
        )

        if 'Items' not in response or len(response['Items']) == 0:
            continue

        item = response['Items'][0]
        item_id = item['id']
        c_tags = item['tags']
        current_tags = json.loads(c_tags)['tags']

        # Ensure current_tags is a list
        if not isinstance(current_tags, list):
            current_tags = []

        # Update the current_tags based on the action type
        if action_type == 1:
            # Add tags
            current_tags.extend(tags)
        elif action_type == 0:
            # Remove tags
            for tag in tags:
                if tag in current_tags:
                    current_tags.remove(tag)

        # Convert updated tags to JSON string
        new_tags = {"tags": current_tags}
        updated_tags = json.dumps(new_tags)

        # Update the item in DynamoDB
        table.update_item(
            Key={'id': item_id},
            UpdateExpression='SET tags = :val1',
            ExpressionAttributeValues={
                ':val1': updated_tags
            }
        )

    return {
        'statusCode': 200,
        'body': json.dumps('Tags updated successfully'),
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*',
            'Access-Control-Allow-Headers': '*'
        },
    }