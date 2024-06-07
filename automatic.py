import boto3
import json

sns = boto3.client('sns')
topic_arn = 'arn:aws:sns:ap-southeast-2:992382579935:ImageTagNotifications'

def lambda_handler(event, context):
    for record in event['Records']:
        if record['eventName'] in ['INSERT', 'MODIFY']:
            new_image = record['dynamodb']['NewImage']
            user_email = new_image['id']['S']  # 假设 'id' 是用户电子邮件的属性名
            raw_data = new_image['subscribed_tags']['L']  # 订阅标签列表
            subscribed_tags = [S_tag.get('S') for S_tag in raw_data]
            print("User Email:", user_email)
            print("Subscribed Tags:", subscribed_tags)

            try:
                # 在 INSERT 事件时订阅用户到SNS主题并发送确认邮件
                if record['eventName'] == 'INSERT':
                    sns.subscribe(
                        TopicArn=topic_arn,
                        Protocol='email',
                        Endpoint=user_email
                    )
                    message = f"Welcome! You've subscribed to tags: {', '.join(subscribed_tags)}."
                    subject = "Subscription Confirmation"
                    sns.publish(
                        TopicArn=topic_arn,
                        Message=message,
                        Subject=subject
                    )
                else:  # MODIFY 事件
                    old_image = record['dynamodb'].get('OldImage', {})
                    old_tags_raw = old_image.get('subscribed_tags', {}).get('L', [])
                    old_tags = [S_tag.get('S') for S_tag in old_tags_raw]

                    # 只有在标签实际变化时才发送更新通知
                    if set(old_tags) != set(subscribed_tags):
                        message = f"Your subscription tags have been updated to: {', '.join(subscribed_tags)}."
                        subject = "Subscription Update"
                        sns.publish(
                            TopicArn=topic_arn,
                            Message=message,
                            Subject=subject
                        )
            except Exception as e:
                print(f"Error in subscribing or notifying {user_email}: {str(e)}")
                # 更多的错误处理可以在这里添加

    return {'status': 'Done'}
