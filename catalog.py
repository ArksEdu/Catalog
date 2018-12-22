from flask import Flask, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
from postgres_db_setup import Base, category, item, person
import security
import categories
import items

app = Flask(__name__)

dbtype = 'postgresql+psycopg2'
dbconnectstr = 'catalog:catalogDB1@localhost:5432'
engine = create_engine('%s://%s/catalog' % (dbtype, dbconnectstr))
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

APPLICATION_NAME = "Catalog Application"


@app.route('/catalog.json')
def catalogJSON():
    categoryTable = session.query(category)
    categories = categoryTable.options(joinedload(category.items)).all()
    return jsonify(dict(category=[dict(c.serialized) for c in categories]))


@app.route('/category<int:cat_id>.json')
def categoryJSON(cat_id):
    categories = session.query(category).options(joinedload(category.items))
    mainCategory = categories.filter_by(id=cat_id).one()
    return jsonify(dict(category=[dict(mainCategory.serialized,
                        item=[i.serialized for i in mainCategory.items])]))


@app.route('/item<int:item_id>.json')
def itemSON(item_id):
    cat_item = session.query(item).filter_by(id=item_id).one()
    return jsonify(dict(item=cat_item.serialized))


@app.route("/login")
def showLogin():
    return security.showLogin()


@app.route('/gconnect', methods=['POST'])
def gconnect():
    return security.connectViaGoogle(session)


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    return security.disconnect(session)


# Show latest items
@app.route('/')
@app.route('/catalog')
def showLatestItems():
    return categories.home(session)


# Show items for a category
@app.route('/<int:cat_id>')
def showItemsForCategory(cat_id):
    return categories.showItemsForCategory(session, cat_id)


# Create a new category
@app.route('/catalog/newcategory/', methods=['GET', 'POST'])
def newCategory():
    return categories.newCategory(session)


# Edit a category
@app.route('/catalog/edit/<int:cat_id>/',
           methods=['GET', 'POST'])
def editCategory(cat_id):
    return categories.editCategory(session, cat_id)


# Delete a category
@app.route('/catalog/delete/<int:cat_id>/',
           methods=['GET', 'POST'])
def deleteCategory(cat_id):
    return categories.deleteCategory(session, cat_id)


# Create a new category item
@app.route('/catalog/newitem/', methods=['GET', 'POST'])
def newItem():
    return items.newItem(session)


# Create a new category item
@app.route('/catalog/<int:cat_id>/newitem', methods=['GET', 'POST'])
def newItemForCat(cat_id):
    return items.newItemForCat(session, cat_id)



# Edit an item
@app.route('/catalog/edititem/<int:item_id>',
           methods=['GET', 'POST'])
def editItem(item_id):
    return items.editItem(session, item_id)


# View an item
@app.route('/catalog/viewitem/<int:item_id>', methods=['GET'])
def viewItem(item_id):
    return items.viewItem(session, item_id)


# Delete an item
@app.route('/catalog/deleteitem/<int:item_id>',
           methods=['GET', 'POST'])
def deleteItem(item_id):
    return items.deleteItem(session, item_id)


if __name__ == "__main__":
    app.secret_key = 'super_secret_key'
    # app.debug = True
    # app.run(host="0.0.0.0", port=5000)
    app.run()
