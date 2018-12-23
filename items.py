from flask import Flask, render_template, session as login_session
from flask import make_response, flash, request, redirect, url_for
from postgres_db_setup import Base, category, item, person
from sqlalchemy import asc, desc


def newItem(session):
    if 'email' not in login_session:
        return redirect('/login')

    if request.method == 'POST':
        if not request.form.get('cat_id'):
            flash('A parent category must be selected')
            return showCreateItem(session, None)

        if not request.form['title']:
            flash('A title must be provided')
            return showCreateItem(session, None)

        cat_id = request.form.get('cat_id')
        new_title = request.form['title']
        items = session.query(item)
        itemsByName = items.filter_by(title=new_title, cat_id=cat_id)
        if itemsByName.count() > 0:
            messageSuffix = 'already exists for this category'
            flash('An item with title %s %s' % (new_title, messageSuffix))
            return redirect(url_for('showItemsForCategory', cat_id=cat_id))

        mainCategory = session.query(category).filter_by(id=cat_id).one()
        if mainCategory.person_id != login_session['user_id']:
            flash('You are not authorized to add items to this category. \
                Please create your own category in order to add items.')
            return redirect(url_for('showLatestItems'))

        return createItem(session, mainCategory, cat_id)
    else:
        return showCreateItem(session, None)


def newItemForCat(session, cat_id):
    if 'email' not in login_session:
        return redirect('/login')

    mainCategory = session.query(category).filter_by(id=cat_id).one()
    if mainCategory.person_id != login_session['user_id']:
        flash('You are not authorized to add items to this category. \
            Please create your own category in order to add items.')
        return redirect(url_for('showLatestItems'))

    if request.method == 'POST':
        if not request.form['title']:
            flash('A title must be provided')
            return showCreateItem(session, mainCategory)

        new_title = request.form['title']
        items = session.query(item)
        itemsByName = items.filter_by(title=new_title, cat_id=cat_id)
        if itemsByName.count() > 0:
            messageSuffix = 'already exists for this category'
            flash('An item with title %s %s' % (new_title, messageSuffix))
            return redirect(url_for('showItemsForCategory', cat_id=cat_id))

        return createItem(session, mainCategory, cat_id)
    else:
        return showCreateItem(session, mainCategory)


def showCreateItem(session, parentCategory):
    allCategories = session.query(category)
    myCategories = allCategories.filter_by(person_id=login_session["user_id"])
    categories = myCategories.order_by(asc(category.name)).all()
    hasParent = False
    if parentCategory is not None:
        hasParent = True
    return render_template('createItem.html', categories=categories,
                           hasparent=hasParent, parent=parentCategory)


def createItem(session, parentCategory, cat_id):
    newItem = item(description=request.form['description'],
                   title=request.form['title'],
                   person_id=login_session['user_id'],
                   cat_id=cat_id)

    session.add(newItem)
    session.commit()
    cat_name = parentCategory.name
    flash('Successfully Created Item: "%s" for Category: %s' % (newItem.title, cat_name))
    return redirect(url_for('showItemsForCategory', cat_id=newItem.cat_id))

def editItem(session, item_id):
    if 'email' not in login_session:
        return redirect('/login')

    editedItem = session.query(item).filter_by(id=item_id).one()
    if editedItem.category.person_id != login_session['user_id']:
        flash('You are not authorized to edit items in this category. \
            Please create your own category in order to edit items.')
        return redirect(url_for('showLatestItems'))

    if request.method == 'POST':
        if not request.form['title']:
            flash('A title must be provided')
            return render_template('editItem.html', item=editedItem)

        items = session.query(item)
        new_title = request.form['title']
        cat_id = editedItem.category.id
        itemsByName = items.filter_by(title=new_title, cat_id=cat_id)
        if new_title != editedItem.title and itemsByName.count() > 0:
            messageSuffix = 'already exists for this category'
            flash('An item with title %s %s' % (new_title, messageSuffix))
            return redirect(url_for('showItemsForCategory', cat_id=cat_id))

        editedItem.title = request.form['title']
        if request.form['description']:
            editedItem.description = request.form['description']
        session.commit()
        flash('Successfully Edited Item')
        return redirect(url_for('viewItem', item_id=item_id))
    else:
        return render_template('editItem.html', item=editedItem)


def viewItem(session, item_id):
    itemToEdit = session.query(item).filter_by(id=item_id).one()
    isLoggedIn = ('email' in login_session)
    canEdit = (isLoggedIn and itemToEdit.person_id == login_session['user_id'])
    return render_template('viewItem.html', item=itemToEdit, allowedit=canEdit)


def deleteItem(session, item_id):
    if 'email' not in login_session:
        return redirect('/login')
    itemToDelete = session.query(item).filter_by(id=item_id).one()
    if itemToDelete.person_id != login_session['user_id']:
        flash('You are not authorized to delete items in this category. \
            Please create your own category in order to delete items.')
        return redirect(url_for('showLatestItems'))

    if request.method == 'POST':
        cat_id = itemToDelete.cat_id
        session.delete(itemToDelete)
        session.commit()
        flash('Successfully Deleted Item')
        return redirect(url_for('showItemsForCategory', cat_id=cat_id))
    else:
        return render_template('deleteItem.html', item=itemToDelete)
