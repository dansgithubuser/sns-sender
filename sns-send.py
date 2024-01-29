#!/usr/bin/env python3

#===== imports =====#
import argparse
import json
from pathlib import Path
import pprint
import sys
import time

#===== args =====#
parser = argparse.ArgumentParser()
parser.add_argument('topic_arn')
parser.add_argument('subject')
parser.add_argument('message', nargs='?')
args = parser.parse_args()

if args.message:
    message = args.message
else:
    message = sys.stdin.read()

#===== consts =====#
exchanges_path = Path(__file__).resolve().parent / 'exchanges'

#===== main =====#
with (exchanges_path / f'{args.subject}-req.json').open('w') as f:
    json.dump(
        {
            'topic_arn': args.topic_arn,
            'subject': args.subject,
            'message': message,
        },
        f,
    )
response_path = exchanges_path / f'{args.subject}-rsp.json'
for i in range(10):
    time.sleep(1)
    if not response_path.exists():
        continue
    with response_path.open() as f:
        pprint.pprint(json.load(f))
        break
else:
    raise Exception('No response from sender.')
