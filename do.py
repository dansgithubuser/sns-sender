#! /usr/bin/env python3

#===== imports =====#
import argparse
import datetime
import getpass
import os
from pathlib import Path
import re
import signal
import subprocess
import sys

#===== args =====#
parser = argparse.ArgumentParser()
parser.add_argument('--install-service', action='store_true')
args = parser.parse_args()

#===== consts =====#
DIR = Path(__file__).resolve().parent

#===== setup =====#
os.chdir(DIR)

#===== helpers =====#
def blue(text):
    return '\x1b[34m' + text + '\x1b[0m'

def timestamp():
    return '{:%Y-%m-%d %H:%M:%S.%f}'.format(datetime.datetime.now())

def invoke(
    *args,
    quiet=False,
    env_add={},
    env_add_secrets=set(),
    handle_sigint=True,
    popen=False,
    check=True,
    put_in=False,
    get_out=False,
    get_err=False,
    **kwargs,
):
    if len(args) == 1 and type(args[0]) == str and not kwargs.get('shell'):
        args = args[0].split()
    if not quiet:
        print(blue('-'*40))
        print(timestamp())
        print(f'{Path.cwd()}$', end=' ')
        if any([re.search(r'\s', i) for i in args]):
            print()
            for i in args: print(f'\t{i} \\')
        else:
            for i, v in enumerate(args):
                if i != len(args)-1:
                    end = ' '
                else:
                    end = ';\n'
                print(v, end=end)
        if env_add:
            print('env_add:', {k: (v if k not in env_add_secrets else '...') for k, v in env_add.items()})
        if kwargs: print(kwargs)
        if popen: print('popen')
        print()
    if env_add:
        env = os.environ.copy()
        env.update(env_add)
        kwargs['env'] = env
    if put_in and 'stdin' not in kwargs: kwargs['stdin'] = subprocess.PIPE
    if get_out: kwargs['stdout'] = subprocess.PIPE
    if get_err: kwargs['stderr'] = subprocess.PIPE
    p = subprocess.Popen(args, **kwargs)
    if handle_sigint:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
    if put_in:
        if type(put_in) == str:
            put_in = put_in.encode()
        p.stdin.write(put_in)
        if popen:
            p.stdin.flush()
        else:
            p.stdin.close()
    if popen:
        return p
    stdout, stderr = p.communicate()
    p.out = stdout
    p.err = stderr
    if handle_sigint:
        signal.signal(signal.SIGINT, signal.SIG_DFL)
    if check and p.returncode:
        raise Exception(f'invocation {repr(args)} returned code {p.returncode}.')
    if get_out:
        stdout = stdout.decode('utf-8')
        if get_out != 'exact': stdout = stdout.strip()
        if not get_err: return stdout
    if get_err:
        stderr = stderr.decode('utf-8')
        if get_err != 'exact': stderr = stderr.strip()
        if not get_out: return stderr
    if get_out and get_err: return stdout, stderr
    return p

#===== main =====#
if len(sys.argv) == 1:
    parser.print_help()
    sys.exit()

if args.install_service:
    print('AWS access key ID: ', end='')
    aws_access_key_id = input()
    aws_secret_access_key = getpass.getpass('AWS secret access key: ')
    python3 = invoke('which python3', get_out=True)
    sender = os.path.join(DIR, 'sns-sender.py')
    with open('sns-sender.service') as f:
        service = f.read().format(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            python3=python3,
            sender=sender,
        )
    invoke('touch /etc/systemd/system/sns-sender.service')
    invoke('chmod 700 /etc/systemd/system/sns-sender.service')
    with open('/etc/systemd/system/sns-sender.service', 'w') as f:
        f.write(service)
    invoke('systemctl daemon-reload')
    invoke('systemctl enable sns-sender')
    invoke('systemctl start sns-sender')
