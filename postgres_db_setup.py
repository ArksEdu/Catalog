from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from collections import OrderedDict

Base = declarative_base()


class person(Base):
    __tablename__ = 'person'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)


class category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    person_id = Column(Integer, ForeignKey('person.id'))
    person = relationship(person)

    @property
    def serialized(self):
        orderedDict = OrderedDict()
        orderedDict['id'] = self.id
        orderedDict['name'] = self.name
        orderedDict['item'] = [i.serialized for i in self.items]
        return orderedDict


class item(Base):
    __tablename__ = 'item'

    cat_id = Column(Integer, ForeignKey('category.id'))
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    title = Column(String(80), nullable=False)
    created_date = Column(DateTime, default=func.now())
    category = relationship(category, backref='items')
    person_id = Column(Integer, ForeignKey('person.id'))
    person = relationship(person)

    @property
    def serialized(self):
        orderedDict = OrderedDict()
        orderedDict['cat_id'] = self.cat_id
        orderedDict['description'] = self.description
        orderedDict['id'] = self.id
        orderedDict['title'] = self.title
        return orderedDict


engine = create_engine('postgresql+psycopg2://student:86jgs12NBA@localhost:5432/catalog')

Base.metadata.create_all(engine)
