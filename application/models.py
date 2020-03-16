from application import db
from sqlalchemy import func

# For many-many relationships table are best suited
# https://docs.sqlalchemy.org/en/13/orm/basic_relationships.html#relationships-one-to-one
entity_property = db.Table('entity_property', db.Model.metadata,
    db.Column('entity_id', db.CHAR(32), db.ForeignKey('entity.id')),
    db.Column('property_id', db.Integer, db.ForeignKey('property.id'))
)

entity_category = db.Table('entity_category', db.Model.metadata,
    db.Column('entity_id', db.CHAR(32), db.ForeignKey('entity.id')),
    db.Column('category_id', db.Integer, db.ForeignKey('category.id')))
# create our database models
class Access(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    access_type = db.Column(db.String)
    access_value = db.Column(db.String)
    direct_access = db.Column(db.Boolean)
    date_created = db.Column(db.DateTime)
    date_updated = db.Column(db.DateTime)
    access_description = db.Column(db.Text)
    service_id = db.Column(db.String, db.ForeignKey('service.id'))


    @property
    def serialize(self):
        return {
            'id' : self.id,
            'access_type' : self.access_type,
            'access_value' : self.access_value,
            'instructions' : self.access_description,
            'enabled_direct_acess' : self.direct_access,
        }


class Address(db.Model):
    id = db.Column(db.CHAR(32), primary_key=True)
    street_number = db.Column(db.Integer)
    street_number_suffix = db.Column(db.String)
    street_name = db.Column(db.String)
    street_type = db.Column(db.String)
    street_direction = db.Column(db.String)
    address_type = db.Column(db.String)
    address_type_id = db.Column(db.String)
    minor_municipality = db.Column(db.String)
    major_municipality = db.Column(db.String)
    governing_district = db.Column(db.String)
    postal_area = db.Column(db.String)
    iso3_code = db.Column(db.CHAR(3))
    lat = db.Column(db.REAL)
    lon = db.Column(db.REAL)


    @property
    def serialize(self):
        address = f'{self.street_number} {self.street_name} {self.street_type} {self.street_direction},'

        return {
            'address' : address,
            'city' : self.major_municipality,
            'id' : self.id,
            'state' : self.governing_district,
            'unit' : f'{self.address_type} {self.address_type_id}',
            'zip_code' : self.postal_area,
            'lat' : self.lat,
            'lon' : self.lon
        }

    def __init__(self, id, *args, **kwargs):
        super(Address, self).__init__(*args, **kwargs)
        self.id = id

class AsylumSeeker(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)

    def __init__(self, user_id, first_name, last_name):
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name

    @property
    def serialize(self):
        return {
            'user_id' : self.user_id,
            'first_name' : self.first_name,
            'last_name' : self.last_name,
        }

class Attachement(db.Model):
    id = db.Column(db.CHAR(32), primary_key=True)
    entity_id = db.Column(db.CHAR(32), db.ForeignKey('entity.id'))
    image = db.Column(db.Boolean)
    name = db.Column(db.String)
    date_uploaded = db.Column(db.DateTime)

    entities = db.relationship('Entity', backref='attachement', lazy=True)

class Comment(db.Model):
    id = db.Column(db.CHAR(32), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    entity_id = db.Column(db.CHAR(32), db.ForeignKey('entity.id'))
    date_created = db.Column(db.DateTime)
    date_updated = db.Column(db.DateTime)
    flagged = db.Column(db.Boolean)
    comment = db.Column(db.Text)

    @property
    def serialize(self):
        return {
            'id' : self.id,
            'user_id' : self.user_id,
            'date_updated' : self.date_updated,
            'comment' : self.comment
        }

class DataManager(db.Model):
    id = db.Column(db.String, primary_key = True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'))
    is_admin = db.Column(db.Boolean)

    def __init__(self, id, user_id, is_admin,*args,**kwargs):
        super(DataManager, self).__init__(*args, **kwargs)

        self.id = id
        self.user_id = user_id
        self.is_admin = is_admin

    @property
    def serialize(self):
        return {
            'user_id' : self.user_id,
            'is_admin' : self.is_admin,
            'id' : self.id
        }


class Day(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.VARCHAR(20))

    daytimes = db.relationship('DayTime', backref='day', lazy=True)

class DayTime(db.Model):
    id = db.Column(db.CHAR(32), primary_key=True)
    time_id = db.Column(db.CHAR(32), db.ForeignKey('time_block.id'))
    day_id = db.Column(db.Integer, db.ForeignKey('day.id'))

    def __init__(self, id, time_id, day_id):
        self.id = id
        self.time_id = time_id
        self.day_id = day_id

class Email(db.Model):
    id = db.Column(db.CHAR(32), primary_key=True)
    email = db.Column(db.String(255))
    entity_id = db.Column(db.CHAR(32), db.ForeignKey('entity.id'))
    is_primary = db.Column(db.Boolean)

    def __init__(self, email,*args, **kwargs):
        super(Email, self).__init__(*args, **kwargs)
        self.email = email

    @property
    def serialize(self):
        return {
            'email' : self.email,
            'id' : self.id,
            'is_primary' : self.is_primary,
            'first_name' : 'Jane',
            'last_name' : 'Doe',
            'show_on_organization' : True,
            'title' : 'Jane Doe'
        }

class Entity(db.Model):
    id = db.Column(db.CHAR(32), primary_key=True)
    name = db.Column(db.String)
    is_searchable = db.Column(db.Boolean)
    marked_deleted = db.Column(db.Boolean)
    date_created = db.Column(db.DateTime)
    date_updated_ac = db.Column(db.DateTime, server_default=func.now())
    date_updated_org = db.Column(db.DateTime, server_default=func.now())
    is_verified = db.Column(db.Boolean)
    last_verified = db.Column(db.DateTime)
    rating = db.Column(db.REAL)
    is_closed = db.Column(db.Boolean)
    user_id = db.Column(db.String)
    website = db.Column(db.String)

    address_id = db.Column(db.CHAR(32), db.ForeignKey('address.id'))

    attachements = db.relationship('Attachement',cascade="all,delete", backref='entity', lazy=True)
    comment = db.relationship('Comment',cascade="all,delete", backref='entity', lazy=True)
    emails = db.relationship('Email',cascade="all,delete", backref='entity', lazy=True)
    entity_languages = db.relationship('EntityLanguage', cascade="all,delete",backref='entity', lazy=True)
    phones = db.relationship('Phone', cascade="all,delete", backref='entity', lazy=True)
    service_providers = db.relationship('ServiceProvider', cascade="all,delete", backref='entity', lazy=True)
    user_favorites = db.relationship('UserFavorite', cascade="all,delete", backref='entity', lazy=True)
    address = db.relationship('Address', cascade="all,delete", backref='entity', uselist=False)
    properties = db.relationship('Property', cascade="all,delete", backref='entity', secondary=entity_property)
    category = db.relationship('Category', cascade="all,delete", backref='entity', secondary=entity_category, lazy=False)

    def __init__(self, id, name, *args, **kwargs):
        super(Entity, self).__init__(*args, **kwargs)
        self.id = id
        self.name = name

    @property
    def serialize(self):
        return {
            'name' : self.name,
            'last_verified' : self.last_verified,
            'updated_at' : self.date_updated_ac,
            'website' : self.website,
            'rating' : self.rating,
            'is_closed' : self.is_closed
        }

class EntityLanguage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entity_id = db.Column(db.CHAR(32), db.ForeignKey('entity.id'))
    iso3_language = db.Column(db.CHAR(3))
    description = db.Column(db.Text)
    notes = db.Column(db.Text)

class Organization(db.Model):
    __tablename__ = 'organization'
    id = db.Column(db.CHAR(32), primary_key=True)
    entity_id = db.Column(db.CHAR(32), db.ForeignKey('entity.id'))

    entity = db.relationship('Entity', cascade="all,delete", backref="organization", uselist=False)
    service = db.relationship('Service',cascade="all,delete", backref='organization', lazy=True)

    @property
    def serialize(self):
        return {
            'id' : self.id
        }

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    definition = db.Column(db.Text)

    @property
    def serialize(self):
        return {
            self.name : True
        }

class Phone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    country_code = db.Column(db.VARCHAR(255))
    entity_id = db.Column(db.CHAR(32), db.ForeignKey('entity.id'))
    area_code = db.Column(db.VARCHAR(255))
    digits = db.Column(db.VARCHAR(255))
    is_primary = db.Column(db.Boolean)

    @property
    def serialize(self):
        return {
            'id' : self.id,
            'digits' : f'{self.area_code}{self.digits}',
            'phone_type' : '',
            'is_primary' : self.is_primary
        }

class Schedule(db.Model):
    id = db.Column(db.CHAR(32), primary_key=True)
    entity_id = db.Column(db.CHAR(32), db.ForeignKey('entity.id'))
    day_time_id = db.Column(db.CHAR(32), db.ForeignKey('day_time.id'))

    entities = db.relationship('Entity', backref='schedules', lazy=True)
    day_times = db.relationship('DayTime', backref='schedules', lazy=True)

class ServiceProvider(db.Model):
    id = db.Column(db.CHAR(32), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    verified = db.Column(db.Boolean)
    entity_id = db.Column(db.CHAR(32), db.ForeignKey('entity.id'))

class Service(db.Model):
    id = db.Column(db.CHAR(32), primary_key=True)
    entity_id = db.Column(db.CHAR(32), db.ForeignKey('entity.id'))
    # access_id = db.Column(db.CHAR(32), db.ForeignKey('access.id'))
    parent_organization = db.Column(db.CHAR(32), db.ForeignKey('organization.id'))
    appointment = db.Column(db.Boolean)


    entity = db.relationship('Entity', cascade="all,delete", backref="service", uselist=False)
    access = db.relationship('Access', cascade="all,delete", backref="access", lazy=False)

    @property
    def serialize(self):
        return {
            'id' : self.id,
            'parent_organization' : self.parent_organization,
            'is_appointment' : self.appointment
        }

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    @property
    def serialize(self):
        return {
            'id' : self.id,
            'tag' : self.name,
            'parent_id' : self.parent_id
        }

class TimeBlock(db.Model):
    id = db.Column(db.CHAR(32), primary_key=True)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)

    daytimes = db.relationship('DayTime', backref='timeblock', lazy=True)

    def __init__(self, id, *args, **kwargs):
        super(TimeBlock, self).__init__(*args, **kwargs)
        self.id = id

class Users(db.Model):
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    password = db.Column(db.String)
    date_created = db.Column(db.DateTime)
    active = db.Column(db.Boolean)
    preferred_language = db.Column(db.CHAR(3))

    comment = db.relationship('Comment', cascade="all,delete", backref='users', lazy=True)
    user_favorite = db.relationship('UserFavorite',cascade="all,delete", backref='users', lazy=True)
    asylum_seekers = db.relationship('AsylumSeeker', cascade="all,delete",backref='users', lazy=True)
    data_manager = db.relationship('DataManager',cascade="all,delete", backref='users', lazy=True)
    service_providers = db.relationship('ServiceProvider',cascade="all,delete", backref='users', lazy=True)

    def __init__(self, id, email, password, *args, **kwargs):
        super(Users, self).__init__(*args, **kwargs)
        self.id = id
        self.email = email
        self.password = password


    @property
    def serialize(self):
        return {
            'user_id' : self.id,
            'email' : self.email,
            'first_name' : self.first_name,
            'last_name' : self.last_name,
            'preferred_language' : self.preferred_language
        }

class UserFavorite(db.Model):
    id = db.Column(db.CHAR(32), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    entity_id = db.Column(db.CHAR(32), db.ForeignKey('entity.id'))
