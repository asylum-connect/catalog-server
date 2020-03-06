from application import db
from sqlalchemy import func

# For many-many relationships table are best suited
# https://docs.sqlalchemy.org/en/13/orm/basic_relationships.html#relationships-one-to-one
entity_property = db.Table('entity_property', db.Model.metadata,
    db.Column('entity_id', db.CHAR(32), db.ForeignKey('entity.id')),
    db.Column('property_id', db.Integer, db.ForeignKey('property.id'))
)

entity_tag = db.Table('entity_tag', db.Model.metadata,
    db.Column('entity_id', db.CHAR(32), db.ForeignKey('entity.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id')))
# create our database models
class Access(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    access_type = db.Column(db.String)
    access_value = db.Column(db.String)
    location = db.Column(db.String)
    direct_access = db.Column(db.Boolean)
    service_id = db.Column(db.String, db.ForeignKey('services.id'))
    date_created = db.Column(db.DateTime)
    date_updated = db.Column(db.DateTime)
    meta_data = db.Column(db.Text)

    @property
    def serialize(self):
        return {
            'id' : self.id,
            'access_type' : self.access_type,
            'access_value' : self.access_value,
            'instructions' : self.meta_data,
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

class Comments(db.Model):
    id = db.Column(db.CHAR(32), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    entity_id = db.Column(db.CHAR(32), db.ForeignKey('entity.id'))
    date_created = db.Column(db.DateTime)
    date_updated = db.Column(db.DateTime)
    flagged = db.Column(db.Boolean)
    comment = db.Column(db.Text)

    def __init__(self, id, user_id, entity_id, date_updated, comment):
        self.id = id
        self.user_id = user_id
        self.entity_id = entity_id
        self.date_updated = date_updated
        self.comment = comment

    @property
    def serialize(self):
        return {
            'id' : self.id,
            'user_id' : self.user_id,
            'entity_id' : self.entity_id,
            'date_updated' : self.date_updated,
            'comment' : self.comment
        }

class Day(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.VARCHAR(20))

    daytimes = db.relationship('DayTime', backref='day', lazy=True)

class DayTime(db.Model):
    id = db.Column(db.CHAR(32), primary_key=True)
    time_id = db.Column(db.CHAR(32), db.ForeignKey('time_block.id'))
    day_id = db.Column(db.Integer, db.ForeignKey('day.id'))

class Email(db.Model):
    id = db.Column(db.CHAR(32), primary_key=True)
    email = db.Column(db.String(32))
    entity_id = db.Column(db.CHAR(32), db.ForeignKey('entity.id'))
    is_primary = db.Column(db.Boolean)

    def __init__(self, email):
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

    attachements = db.relationship('Attachement', backref='entity', lazy=True)
    comments = db.relationship('Comments', backref='entity', lazy=True)
    emails = db.relationship('Email', backref='entity', lazy=True)
    entity_languages = db.relationship('EntityLanguage', backref='entity', lazy=True)
    phones = db.relationship('Phone', backref='entity', lazy=True)
    service_providers = db.relationship('ServiceProvider', backref='entity', lazy=True)
    user_favorites = db.relationship('UserFavorites', backref='entity', lazy=True)
    address = db.relationship('Address', backref='entity', uselist=False)
    properties = db.relationship('Property', backref='entity', secondary=entity_property)
    tags = db.relationship('Tags', backref='entity', secondary=entity_tag, lazy=False)

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

    entity = db.relationship('Entity', backref="organization", uselist=False)
    services = db.relationship('Services', backref='organization', lazy=True)

    def __init__(self, id, entity_id):
        self.id = id,
        self.entity_id = entity_id

    @property
    def serialize(self):
        return {
            'id' : self.id
        }

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    definition = db.Column(db.Text)
    value = db.Column(db.String)

    @property
    def serialize(self):
        return {
            self.name : True
        }

class Phone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    country_code = db.Column(db.VARCHAR(32))
    entity_id = db.Column(db.CHAR(32), db.ForeignKey('entity.id'))
    area_code = db.Column(db.VARCHAR(32))
    digits = db.Column(db.VARCHAR(32))
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
    type = db.Column(db.String)
    description = db.Column(db.String)
    organization_name = db.Column(db.String)
    about = db.Column(db.String)
    phone = db.Column(db.String)
    website = db.Column(db.String)
    cost = db.Column(db.String)
    appointment_needed = db.Column(db.Boolean)
    languages_spoken = db.Column(db.String)
    who_we_serve = db.Column(db.String)
    verified = db.Column(db.Boolean)
    entity_id = db.Column(db.CHAR(32), db.ForeignKey('entity.id'))

class Services(db.Model):
    id = db.Column(db.CHAR(32), primary_key=True)
    entity_id = db.Column(db.CHAR(32), db.ForeignKey('entity.id'))
    parent_organization_id = db.Column(db.CHAR(32), db.ForeignKey('organization.id'))
    appointment = db.Column(db.Boolean)

    entity = db.relationship('Entity', backref="services", uselist=False)
    access = db.relationship('Access', backref="access", lazy=False)

    @property
    def serialize(self):
        return {
            'id' : self.id,
            'parent_organization_id' : self.parent_organization_id,
            'is_appointment' : self.appointment
        }

class Tags(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    parent_tag = db.Column(db.Integer, db.ForeignKey('tags.id'))

    @property
    def serialize(self):
        return {
            'id' : self.id,
            'tag' : self.name,
            'parent_id' : self.parent_tag
        }

class TimeBlock(db.Model):
    id = db.Column(db.CHAR(32), primary_key=True)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)

    daytimes = db.relationship('DayTime', backref='timeblock', lazy=True)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String)
    user_type = db.Column(db.String)
    hashed_password = db.Column(db.String)
    salt = db.Column(db.String)
    created_at = db.Column(db.DateTime)
    iso3_code = db.Column(db.CHAR(3))
    active = db.Column(db.Boolean)
    preferred_language = db.Column(db.CHAR(3))

    comments = db.relationship('Comments', backref='user', lazy=True)
    user_favorites = db.relationship('UserFavorites', backref='user', lazy=True)
    asylum_seekers = db.relationship('AsylumSeeker', backref='user', lazy=True)
    service_providers = db.relationship('ServiceProvider', backref='user', lazy=True)

    def __init__(self, id, email, preferred_language):
        self.id = id
        self.email = email
        self.preferred_language = preferred_language

    @property
    def serialize(self):
        return {
            'user_id' : self.id,
            'email' : self.email,
            'preferred_language' : self.preferred_language
        }

class UserFavorites(db.Model):
    id = db.Column(db.CHAR(32), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    entity_id = db.Column(db.CHAR(32), db.ForeignKey('entity.id'))
