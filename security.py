from flask import Flask, render_template, session as login_session
from flask import make_response, flash, request, redirect, url_for
from postgres_db_setup import Base, category, item, person
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import requests
import random
import string
import httplib2
import json


SECRETS_FILE = 'client_secrets.json'
CLIENT_ID = json.loads(open(SECRETS_FILE, 'r').read())['web']['client_id']


def showLogin():
    choiceStr = string.ascii_uppercase + string.digits
    state = ''.join(random.choice(choiceStr) for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


def connectViaGoogle(session):
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    googleUrl = 'https://www.googleapis.com/oauth2/v1/tokeninfo'
    url = ('%s?access_token=%s' % (googleUrl, access_token))
    h = httplib2.Http('cache')
    result = json.loads(h.request(url)[1].decode('utf-8'))
    # h = httplib2.Http()
    # result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        dumps = json.dumps('Current user is already connected.')
        response = make_response(dumps, 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    print(data)

    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"], session)
    if not user_id:
        user_id = createUser(login_session, session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['email']
    output += '!</h1>'
    flash("you are now logged in as %s" % login_session['email'])
    return output


def disconnectFromGoogle(session):
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        dumps = json.dumps('Failed to revoke token for given user.')
        response = make_response(dumps, 400)
        response.headers['Content-Type'] = 'application/json'
        return response


def disconnect(session):
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            disconnectFromGoogle(session)
            del login_session['gplus_id']
            del login_session['access_token']

        del login_session['email']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showLatestItems'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showLatestItems'))

def createUser(login_session, session):
    newUser = person(name=login_session['email'], email=login_session['email'])
    session.add(newUser)
    session.commit()
    user = session.query(person).filter_by(email=login_session['email']).one()
    return user.id


def getUserID(email, session):
    try:
        user = session.query(person).filter_by(email=email).one()
        return user.id
    except Exception:
        return None