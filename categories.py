from flask import Flask, render_template, session as login_session
from flask import make_response, flash, request, redirect, url_for
from postgres_db_setup import Base, category, item, person
from sqlalchemy import asc, desc
from sqlalchemy.orm import sessionmaker, joinedload


def home(session):
    categories = session.query(category).order_by(asc(category.name)).all()
    items = session.query(item)
    latest_items = items.order_by(desc(item.created_date)).limit(10).all()
    return render_template('catalog.html', categories=categories,
                           latest_items=latest_items)


def showItemsForCategory(session, cat_id):
    categories = session.query(category).order_by(asc(category.name)).all()
    mainCategory = session.query(category).filter_by(id=cat_id).one()
    filteredItems = session.query(item).filter_by(cat_id=cat_id)
    items = filteredItems.order_by(asc(item.title)).all()
    isLoggedIn = ('email' in login_session)
    canEdit = (isLoggedIn and mainCategory.person_id == login_session['user_id'])
    return render_template('categoryItems.html', categories=categories,
                           category=mainCategory, items=items,
                           allowedit=canEdit)


def newCategory(session):
    if 'email' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        allCategories = session.query(category)
        cat_name = request.form["name"]
        existingCat = allCategories.filter_by(name=cat_name).one_or_none()
        if existingCat is not None:
            flash('A category with name %s already exists' % cat_name)
            return redirect(url_for('showLatestItems'))

        newCategory = category(name=request.form['name'],
                               person_id=login_session['user_id'])
        session.add(newCategory)
        flash('New category %s Successfully Created' % newCategory.name)
        session.commit()
        return redirect(url_for('showLatestItems'))
    else:
        return render_template('createCategory.html')


def editCategory(session, cat_id):
    if 'email' not in login_session:
        return redirect('/login')
    editedCategory = session.query(category).filter_by(id=cat_id).one()
    if editedCategory.person_id != login_session['user_id']:
        flash('You are not authorized to edit this category. \
            Please create your own category in order to edit.')
        return redirect(url_for('showLatestItems'))

    if request.method == 'POST':
        new_name = request.form['name']
        catsByName = session.query(category).filter_by(name=new_name)
        if new_name != editedCategory.name and catsByName.count() > 0:
            flash('A category with name %s already exists' % new_name)
            return redirect(url_for('showItemsForCategory', cat_id=cat_id))

        editedCategory.name = new_name
        flash('category Successfully Edited %s' % editedCategory.name)
        session.commit()
        return redirect(url_for('showItemsForCategory', cat_id=cat_id))
    else:
        return render_template('editCategory.html', category=editedCategory)


def deleteCategory(session, cat_id):
    if 'email' not in login_session:
        return redirect('/login')
    catToDelete = session.query(category).filter_by(id=cat_id).one()
    if catToDelete.person_id != login_session['user_id']:
        flash('You are not authorized to delete this category. \
            Please create your own category in order to delete.')
        return redirect(url_for('showLatestItems'))

    if request.method == 'POST':
        itemsToDelete = session.query(item).filter_by(cat_id=cat_id).all()
        for itemToDelete in itemsToDelete:
            session.delete(itemToDelete)

        session.delete(catToDelete)
        flash('%s Successfully Deleted' % catToDelete.name)
        session.commit()
        return redirect(url_for('showLatestItems'))
    else:
        return render_template('deleteCategory.html', category=catToDelete)

