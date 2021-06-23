import slack
import os
import requests
import json
from flask import Flask
from slack import WebClient
from slackeventsapi import SlackEventAdapter

# Establish app and keys
app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'], '/slack/events', app)
client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")['user_id']
dbs_api = 'https://a4tyyal61e.execute-api.us-east-1.amazonaws.com/api/databases'
dbs_key = os.environ.get('DBSERVICES_KEY')
headers = {'x-api-key': dbs_key, 'Content-Type': 'application/json'}

# Set up a response at the root / path. Takes GET method.
@app.route('/', methods=['GET'])
def hello_world():
    return "Hello world"

BOILER = """
Available commands for the Database Service Bot are:

  list                    Lists all database services
  show <1a2b3c>           Shows details for database service with ID 1a2b3c
                          Do not include < > characters.
  new <name> <owner>      Request a new database service with a 'name' for owner 'for'
                          Use single-word names, may include hyphens, such as 'sdscap-mst3k'
                          Do not include < > characters.
  help                    Shows this command reference
"""

def post_message(msg_text,user_id):
    pre = '```' + msg_text + '```'
    if BOT_ID != user_id:
        client.chat_postMessage(channel='#dbs', text=pre)

def new_dbservice(dbuser, created_for):
    slackuser = 'uvarc'
    data_package = {"dbuser":dbuser, "created_by": slackuser, "created_for":created_for}
    request = requests.post(dbs_api, headers=headers, data=json.dumps(data_package))
    return 

def list_dbservices():
    request = requests.get(dbs_api, headers=headers)
    payload = request.json()
    resp_text = ''
    answer = []
    col_headers = ('ID','DBNAME','CREATED FOR','CREATED ON','STATUS')
    answer.append(col_headers)
    for pay in payload:
        created = str(pay['created_on'])
        created_for = str(pay['created_for'])
        dbid = str(pay['dbid'])
        dbuser = str(pay['dbuser'])
        created_on = created[0:10]
        dbstatus = str(pay['dbstatus'])
        pset = dbid, dbuser, created_for, created_on, dbstatus
        answer.append(pset)
    for args in answer:
        resp_text+='{0:<12} {1:<18} {2:<14} {3:<14} {4:<12}'.format(*args) + '\n'
    return resp_text

def detail_dbservice(dbid):
    qurl = dbs_api + '/' + dbid
    request = requests.get(qurl, headers=headers)
    payload = request.json()
    r = ''
    created_for = payload['created_for']
    created_by = payload['created_by']
    dbuser = payload['dbuser']
    dbpass = payload['dbpass']
    dbstatus = payload['dbstatus']
    created = payload['created_on']
    created_on = created[0:10]
    r+="Status:       " + dbstatus + '\nCreated by:   ' + created_by + '\nCreated on:   ' + created_on + '\n\nDB User:      ' + dbuser + '\nDB Pass:      ' + dbpass + '\nDB Host:      dbs.hpc.uvadcos.io' + '\nDB Port:      3306'
    # print(dbstatus)
    return r

@slack_event_adapter.on('message')
def message(payload):
    event = payload.get('event',{'text'})
    # print(event)
    user_id = event.get('user')
    text = event.get('text')
    if len(text.split()) >= 1:
        first = text.split()[0]
    else:
        first = text
    if first == 'list':
        msg_text = list_dbservices()
        post_message(msg_text,user_id)
    elif first == 'show':
        dbid = text.split()[1]
        msg_text = detail_dbservice(dbid)
        post_message(msg_text,user_id)
    elif first == 'Status':
        var = "value"
    elif first == 'new':
        if len(text.split()) == 3:
            dbname = text.split()[1]
            created_for = text.split()[2]
            new_dbservice(dbname, created_for)
            # msg_text = 'This function not yet implemented.'
            msg_text = "Database Service submitted. Please wait for creation."
            post_message(msg_text,user_id)
        else:
            msg_text = "Please enter two additional parameters, <dbname> and <created_for>"
            post_message(msg_text,user_id)
    else:
        msg_text = BOILER
        post_message(msg_text,user_id)


if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
