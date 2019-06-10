import poplib
import pexpect
import time
import sys
import json
import re
from email.parser import Parser

with open('config.json') as config_file:
    config = json.load(config_file)

server = config.get('server')
vpnuser = config.get('vpnuser')
vpnpassword = config.get('vpnpassword')
email = config.get('email')
emailpassword = config.get('emailpassword')
popserver = config.get('popserver')
port = config.get('port')
route = config.get('route')

def login_to_vpn(forticlient):
    forticlient.expect('Password for VPN:')
    forticlient.sendline(vpnpassword)
    forticlient.expect('Would you like to connect to this server')
    forticlient.sendline('Y')
    forticlient.expect('An email message containing a Token Code')
    print 'Login successful. Waiting for auth code email...\n'

def wait_for_auth_code_email():
    time.sleep(10)

def connect_to_pop_server():
    connection = poplib.POP3_SSL(popserver)
    connection.user(email)
    connection.pass_(emailpassword)
    return connection

def get_auth_code_email(pop_connection):
    _, messages, __ = pop_connection.list()
    _, lines, __ = pop_connection.retr(len(messages))

    msg_content = b'\r\n'.join(lines).decode('utf-8')
    return Parser().parsestr(msg_content)

def extract_auth_code(msg):
    subject = msg.get('Subject')
    match = re.search('AuthCode: (\d{6})', subject)

    return match.group(1)

def enter_auth_code(forticlient, code):
    forticlient.sendline(code)
    forticlient.expect('STATUS::Login succeed')
    forticlient.logfile = sys.stdout
    forticlient.expect('STATUS::Tunnel running')

def setup_static_route(route):
    print "Adding static route...:"
    print route
    pexpect.run(route)


forticlient = pexpect.spawn('./forticlientsslvpn_cli --server {} --vpnuser {}'.format(server, vpnuser))

login_to_vpn(forticlient)

wait_for_auth_code_email()
auth_code_email = get_auth_code_email(connect_to_pop_server())

code = extract_auth_code(auth_code_email)
enter_auth_code(forticlient, code)

setup_static_route(route)

forticlient.interact()
