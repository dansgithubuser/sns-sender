#!/usr/bin/env python3

#===== imports =====#
#----- 3rd party -----#
import boto3

#----- standard -----#
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import time

#===== consts =====#
exchanges_path = Path(__file__).resolve().parent / 'exchanges'

try:
    aws_access_key_id = os.environ['SNS_SENDER_AWS_ACCESS_KEY_ID']
    aws_secret_access_key = os.environ['SNS_SENDER_AWS_SECRET_ACCESS_KEY']
    client = boto3.client(
        'sns',
        region_name='us-west-2',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )
    print(f'Created SNS client, AWS access key ID is:\n{aws_access_key_id}')
except Exception as e:
    print(f'Error when making SNS client: {e}')
    client = None

#===== helpers =====#
def now():
    return datetime.now(timezone.utc)

#===== main =====#
while True:
    for request_path in exchanges_path.glob('*-req.json'):
        with request_path.open() as f:
            try:
                request = json.load(f)
            except:
                continue
        request_path.unlink()
        topic_arn = request['topic_arn']
        subject = request['subject']
        message = request['message']
        if client:
            client.publish(
                TopicArn=topic_arn,
                Subject=subject,
                Message=message,
            )
        else:
            print(f"SNS credentials not set up, but if they were I'd send this message to {topic_arn}:\n\n{subject}\n\n{message}\n\n\n")
        response_path = Path(re.sub('(.*)-req.json$', r'\1-rsp.json', str(request_path)))
        with response_path.open('w') as f:
            json.dump(
                {
                    **request,
                    'sent_at': now().isoformat(' ', 'seconds'),
                },
                f,
            )
    for response_path in exchanges_path.glob('*-rsp.json'):
        with response_path.open() as f:
            response = json.load(f)
        if now() - datetime.fromisoformat(response['sent_at']) > timedelta(hours=1):
            response_path.unlink()
    time.sleep(5)
