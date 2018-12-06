from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from collections import OrderedDict

Base = declarative_base()


class User(Base):
    __tablename__ = 'User'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)


class Category(Base):
    __tablename__ = 'Category'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)

    user_id = Column(Integer, ForeignKey('User.id'))
    User = relationship(User)

    @property
    def serialized(self):
        orderedDict = OrderedDict()
        orderedDict['id'] = self.id
        orderedDict['name'] = self.name
        orderedDict['Item'] = [i.serialized for i in self.Items]
        return orderedDict


class Item(Base):
    __tablename__ = 'Item'

    cat_id = Column(Integer, ForeignKey('Category.id'))
    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String(250))
    title = Column(String(80), nullable=False)
    created_date = Column(DateTime, default=func.now())
    Category = relationship(Category, backref='Items')
    user_id = Column(Integer, ForeignKey('User.id'))
    user = relationship(User)

    @property
    def serialized(self):
        orderedDict = OrderedDict()
        orderedDict['cat_id'] = self.cat_id
        orderedDict['description'] = self.description
        orderedDict['id'] = self.id
        orderedDict['title'] = self.title
        return orderedDict


engine = create_engine('sqlite:///catalog.db')

Base.metadata.create_all(engine)
