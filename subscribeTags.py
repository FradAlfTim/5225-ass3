import json
import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource('dynamodb')
USER_SUBSCRIPTIONS_TABLE = 'user-tags'

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
        'Access-Control-Allow-Headers': '*'
    }
    
    # 从事件对象中获取用户信息
    # user_email = event['requestContext']['claims']['email']
    body = json.loads(event['body'])
    new_tags = body['subscribed_tags']
    user_email = body['user_email']
    
    # 获取 DynamoDB 表
    table = dynamodb.Table(USER_SUBSCRIPTIONS_TABLE)
    
    # 检查用户是否已有订阅
    response = table.get_item(Key={'id': user_email})
    
    if 'Item' in response:
        # 用户已有订阅，合并新的标签
        existing_tags = set(response['Item']['subscribed_tags'])
        print(existing_tags)
        updated_tags = list(existing_tags.union(new_tags))  # 合并集合，并转换回列表以供DynamoDB使用
        # 更新 DynamoDB 表中的订阅信息
        table.update_item(
            Key={'id': user_email},
            UpdateExpression='SET subscribed_tags = :updated_tags', # SET 表示更新，将属性subscribed_tags设置为参数:updated_tags的值
            ExpressionAttributeValues={':updated_tags': updated_tags} # 更新表达式中使用的参数值为updated
        )
    else: 
        # 用户没有订阅，创建新订阅
        table.put_item(
            Item={
                'id': user_email,
                'subscribed_tags': list(new_tags)  # 存储为列表，DynamoDB 自动处理为'SS'
            }
        )
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({'message': 'Subscription updated successfully'})
    }
