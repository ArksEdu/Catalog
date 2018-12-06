from flask import Flask, render_template, request, redirect, url_for
from flask import jsonify, flash
from flask import session as login_session
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker, joinedload
from database_setup import Base, Category, Item, User
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

SECRETS_FILE = 'client_secrets.json'
CLIENT_ID = json.loads(open(SECRETS_FILE, 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Application"


@app.route('/catalog.json')
def catalogJSON():
    categoryTable = session.query(Category)
    categories = categoryTable.options(joinedload(Category.Items)).all()
    return jsonify(dict(Category=[dict(c.serialized) for c in categories]))


@app.route('/category<int:cat_id>.json')
def categoryJSON(cat_id):
    categories = session.query(Category).options(joinedload(Category.Items))
    category = categories.filter_by(id=cat_id).one()
    return jsonify(dict(Category=[dict(category.serialized,
                        Item=[i.serialized for i in category.Items])]))


@app.route('/item<int:item_id>.json')
def itemSON(item_id):
    cat_item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(dict(Item=cat_item.serialized))


@app.route("/login")
def showLogin():
    choiceStr = string.ascii_uppercase + string.digits
    state = ''.join(random.choice(choiceStr) for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
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
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
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
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['email']
    output += '!</h1>'
    flash("you are now logged in as %s" % login_session['email'])
    return output


@app.route('/gdisconnect')
def gdisconnect():
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


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
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


def createUser(login_session):
    newUser = User(name=login_session['email'], email=login_session['email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except Exception:
        return None


# Show latest items
@app.route('/')
@app.route('/catalog')
def showLatestItems():
    categories = session.query(Category).order_by(asc(Category.name)).all()
    items = session.query(Item)
    latest_items = items.order_by(desc(Item.created_date)).limit(10).all()
    return render_template('catalog.html', categories=categories,
                           latest_items=latest_items)


# Show items for a category
@app.route('/<int:cat_id>')
def showItemsForCategory(cat_id):
    categories = session.query(Category).order_by(asc(Category.name)).all()
    category = session.query(Category).filter_by(id=cat_id).one()
    filteredItems = session.query(Item).filter_by(cat_id=cat_id)
    items = filteredItems.order_by(asc(Item.title)).all()
    isLoggedIn = ('email' in login_session)
    canEdit = (isLoggedIn and category.user_id == login_session['user_id'])
    return render_template('categoryItems.html', categories=categories,
                           category=category, items=items,
                           allowedit=canEdit)


# Create a new category
@app.route('/catalog/newcategory/', methods=['GET', 'POST'])
def newCategory():
    if 'email' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        allCategories = session.query(Category)
        cat_name = request.form["name"]
        existingCat = allCategories.filter_by(name=cat_name).one_or_none()
        if existingCat is not None:
            flash('A category with name %s already exists' % cat_name)
            return redirect(url_for('showLatestItems'))

        newCategory = Category(name=request.form['name'],
                               user_id=login_session['user_id'])
        session.add(newCategory)
        flash('New Category %s Successfully Created' % newCategory.name)
        session.commit()
        return redirect(url_for('showLatestItems'))
    else:
        return render_template('createCategory.html')


# Edit a category
@app.route('/catalog/edit/<int:cat_id>/',
           methods=['GET', 'POST'])
def editCategory(cat_id):
    if 'email' not in login_session:
        return redirect('/login')
    editedCategory = session.query(Category).filter_by(id=cat_id).one()
    if editedCategory.user_id != login_session['user_id']:
        flash('You are not authorized to edit this category. \
            Please create your own category in order to edit.')
        return redirect(url_for('showLatestItems'))

    if request.method == 'POST':
        new_name = request.form['name']
        catsByName = session.query(Category).filter_by(name=new_name)
        if new_name != editedCategory.name and catsByName.count() > 0:
            flash('A category with name %s already exists' % new_name)
            return redirect(url_for('showItemsForCategory', cat_id=cat_id))

        editedCategory.name = new_name
        flash('Category Successfully Edited %s' % editedCategory.name)
        session.commit()
        return redirect(url_for('showItemsForCategory', cat_id=cat_id))
    else:
        return render_template('editCategory.html', category=editedCategory)


# Delete a restaurant
@app.route('/catalog/delete/<int:cat_id>/',
           methods=['GET', 'POST'])
def deleteCategory(cat_id):
    if 'email' not in login_session:
        return redirect('/login')
    catToDelete = session.query(Category).filter_by(id=cat_id).one()
    if catToDelete.user_id != login_session['user_id']:
        flash('You are not authorized to delete this category. \
            Please create your own category in order to delete.')
        return redirect(url_for('showLatestItems'))

    if request.method == 'POST':
        itemsToDelete = session.query(Item).filter_by(cat_id=cat_id).all()
        for item in itemsToDelete:
            session.delete(item)

        session.delete(catToDelete)
        flash('%s Successfully Deleted' % catToDelete.name)
        session.commit()
        return redirect(url_for('showLatestItems'))
    else:
        return render_template('deleteCategory.html', category=catToDelete)


# Create a new category item
@app.route('/catalog/newitem/', methods=['GET', 'POST'])
def newItem():
    if 'email' not in login_session:
        return redirect('/login')

    if request.method == 'POST':
        if not request.form.get('cat_id'):
            flash('A parent Category must be selected')
            return showCreateItem(category=None)

        if not request.form['title']:
            flash('A title must be provided')
            return showCreateItem(category=None)

        cat_id = request.form.get('cat_id')
        new_title = request.form['title']
        items = session.query(Item)
        itemsByName = items.filter_by(title=new_title, cat_id=cat_id)
        if itemsByName.count() > 0:
            messageSuffix = 'already exists for this category'
            flash('An item with title %s %s' % (new_title, messageSuffix))
            return redirect(url_for('showItemsForCategory', cat_id=cat_id))

        category = session.query(Category).filter_by(id=cat_id).one()
        if category.user_id != login_session['user_id']:
            flash('You are not authorized to add items to this category. \
                Please create your own category in order to add items.')
            return redirect(url_for('showLatestItems'))

        return createItem(category=category, cat_id=cat_id)
    else:
        return showCreateItem(category=None)


# Create a new category item
@app.route('/catalog/<int:cat_id>/newitem', methods=['GET', 'POST'])
def newItemForCat(cat_id):
    if 'email' not in login_session:
        return redirect('/login')

    category = session.query(Category).filter_by(id=cat_id).one()
    if category.user_id != login_session['user_id']:
        flash('You are not authorized to add items to this category. \
            Please create your own category in order to add items.')
        return redirect(url_for('showLatestItems'))

    if request.method == 'POST':
        if not request.form['title']:
            flash('A title must be provided')
            return showCreateItem(category)

        new_title = request.form['title']
        items = session.query(Item)
        itemsByName = items.filter_by(title=new_title, cat_id=cat_id)
        if itemsByName.count() > 0:
            messageSuffix = 'already exists for this category'
            flash('An item with title %s %s' % (new_title, messageSuffix))
            return redirect(url_for('showItemsForCategory', cat_id=cat_id))

        return createItem(category=category, cat_id=cat_id)
    else:
        return showCreateItem(category)


def showCreateItem(category):
    allCategories = session.query(Category)
    myCategories = allCategories.filter_by(user_id=login_session["user_id"])
    categories = myCategories.order_by(asc(Category.name)).all()
    hasParent = False
    if category is not None:
        hasParent = True
    return render_template('createItem.html', categories=categories,
                           hasparent=hasParent, parent=category)


def createItem(category, cat_id):
    newItem = Item(description=request.form['description'],
                   title=request.form['title'],
                   user_id=login_session['user_id'],
                   cat_id=cat_id)

    session.add(newItem)
    session.commit()
    cat_name = category.name
    flash('Item "%s" Successfully Created for %s' % (newItem.title, cat_name))
    return redirect(url_for('showItemsForCategory', cat_id=newItem.cat_id))


# Edit an item
@app.route('/catalog/edititem/<int:item_id>',
           methods=['GET', 'POST'])
def editItem(item_id):
    if 'email' not in login_session:
        return redirect('/login')

    editedItem = session.query(Item).filter_by(id=item_id).one()
    if editedItem.Category.user_id != login_session['user_id']:
        flash('You are not authorized to edit items in this category. \
            Please create your own category in order to edit items.')
        return redirect(url_for('showLatestItems'))

    if request.method == 'POST':
        if not request.form['title']:
            flash('A title must be provided')
            return render_template('editItem.html', item=editedItem)

        items = session.query(Item)
        new_title = request.form['title']
        cat_id = editedItem.Category.id
        itemsByName = items.filter_by(title=new_title, cat_id=cat_id)
        if new_title != editedItem.title and itemsByName.count() > 0:
            messageSuffix = 'already exists for this category'
            flash('An item with title %s %s' % (new_title, messageSuffix))
            return redirect(url_for('showItemsForCategory', cat_id=cat_id))

        editedItem.title = request.form['title']
        if request.form['description']:
            editedItem.description = request.form['description']
        session.commit()
        flash('Item Successfully Edited')
        return redirect(url_for('viewItem', item_id=item_id))
    else:
        return render_template('editItem.html', item=editedItem)


# View an item
@app.route('/catalog/viewitem/<int:item_id>', methods=['GET'])
def viewItem(item_id):
    itemToEdit = session.query(Item).filter_by(id=item_id).one()
    isLoggedIn = ('email' in login_session)
    canEdit = (isLoggedIn and itemToEdit.user_id == login_session['user_id'])
    return render_template('viewItem.html', item=itemToEdit, allowedit=canEdit)


# Delete an item
@app.route('/catalog/deleteitem/<int:item_id>',
           methods=['GET', 'POST'])
def deleteItem(item_id):
    if 'email' not in login_session:
        return redirect('/login')
    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    if itemToDelete.user_id != login_session['user_id']:
        flash('You are not authorized to delete items in this category. \
            Please create your own category in order to delete items.')
        return redirect(url_for('showLatestItems'))

    if request.method == 'POST':
        cat_id = itemToDelete.cat_id
        session.delete(itemToDelete)
        session.commit()
        flash('Item Successfully Deleted')
        return redirect(url_for('showItemsForCategory', cat_id=cat_id))
    else:
        return render_template('deleteItem.html', item=itemToDelete)


if __name__ == "__main__":
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host="0.0.0.0", port=5000)
