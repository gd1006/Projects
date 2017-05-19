# This part creates a web server that will "receive" the requests by Slack
# in the `redirect_uri`

# In this cell, we just configure the server. We will start it, 
# using the command webserver.run(host='0.0.0.0') in the next cell

# Flask is a webserver
from flask import Flask, request

# We will use that part to issue a request to Slack
import requests
import json

# Get these after registering an app with Slack
# These are to communicate to Jawbone that the requests come
# from a legitimate, registered app
CLIENT_ID = '3417815998.64093686112'
CLIENT_SECRET = 'ddc9272e1e9d103b11b004b9505567d6'

# This is the location where we will store the authentication data from Slack
OAUTH_FILE = 'slack_secret.json'

# Initialize the Flask web server
webserver = Flask("SlackOAuth", static_folder='plots')


# This is the place where the webserver will receive the call from Slack
# The call from Slack will have a parameter "code"
@webserver.route("/slack")
def oauth_helper():
    code = request.args.get('code')
    
    # Now that we got the code 
    # we request the access token from Slask. Notice that we 
    # use the client_secret to prove that the app is the real one
    # that was registered with the Slack API
    url = "https://slack.com/api/oauth.access"
    params = {"grant_type": "authorization_code", 
              "client_id": CLIENT_ID, 
              "client_secret": CLIENT_SECRET, 
              "code": code,
              "redirect_uri": "http://ipython-panos.ipeirotis.com:5000/slack"}
    resp = requests.get(url, params=params)
    data = json.loads(resp.text)
    
    # We store the code in a file as the webserver does not interact with the 
    # rest of the Python code, and we also want to reuse the code in the future
    # (Typically, we would store the access_token in a database.)
    f = open(OAUTH_FILE, 'w') # Store the code as a file
    f.write(resp.text)
    f.close()
    
    # If we start the server just to get the code, it is safe (and convenient) 
    # to shut down the web server after this request. For Slack, we will 
    # use the web server to send plots.
    # stop_server()
    
    # What we return here has no real impact on the functionality of the code
    return '<html><body>Code: <b>'+code+'</b><p>Response:<b>'+resp.text+'</b></body></html>'

@webserver.route('/plots/<path:path>')
def static_proxy(path):
  # send_static_file will guess the correct MIME type
  return webserver.send_static_file(path)


def start_server():
    webserver.run(host='0.0.0.0', port=5000)
    return
    
def stop_server():
    shutdown_after_request = request.environ.get('werkzeug.server.shutdown')
    shutdown_after_request()
    return
    
# And now start the webserver so that we can receive the answer from Slack API
start_server()
