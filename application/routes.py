import random, uuid
import numpy as np
import sys

from datetime import datetime
from application import simpleApp, db
from flask import render_template, request
from flask import Flask, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, text

from .models import *

WEEKDAYS = {
    'Sunday' : 1,
    'Monday': 2,
    'Tuesday' : 3,
    'Wednesday' : 4,
    'Thursday' : 5,
    'Friday' : 6,
    'Saturday' :7
}

TABLENAME = {
    'entity' : Entity,
    'address' : Address,
    'access' : Access,
    'email' : Email,
    'phone' : Phone,
    'entity_language' : EntityLanguage,
    'service' : Service,
    'schedule' : Schedule,
    'organization' : Organization
}

def tags_mapping(name):
    """
        Returns a mapping of tag names with their parent tag name
    """
    tag = {
        'General health' : 1,
        'Vision' : 1,
        'Medical emergency' : 1,
        'Transportation for healthcare' : 1,
        'Transgender health' : 1,
        'Legal' : 2,
    }

    if name in tag.keys():
        return tag[name]
    else:
        return 0

def parse_query(query):
    """
        Turns a raw query from catalog into a dictionary useful for the server
        based on query language of 1Degree.

        TODO: eventually want to clean this up once we connect it to the front
        end
    """
    # query for tags in one degree is query[tags][]=tag_name
    tags = [tags_mapping(i) for i in query.getlist('query[tags][]')]

    sub = 'query[properties]'
    properties = [i.split(sub)[1][1:-1] for i in query.keys() if sub in i]

    # 1D you had to filter by lgbt and asylum seeker but all resources on server
    # will be for lgbt & asylum seekers
    properties = [x for x in properties if x not in ['community-lgbt','community-asylum-seeker']]

    return {
        'lat' : query.get('query[lat]'),
        'lon' : query.get('query[long]'),
        'tags' : tags,
        'property' : properties,
        'order' : query.get('query[order]'),
        'page' : query.get('page'),
        'per_page' : query.get('per_page')
    }

def within_location_query(object_name,lat,lon, range):
    """
        Returns query string to search database based on proximity to lat lon

        TODO: verify what the proximity range should be? We can make it variable
    """
    query_template = f"SELECT {object_name}.id AS {object_name}_id\
                      FROM {object_name}, category, address\
                      WHERE ST_DWithin(ST_SetSRID(\
                      ST_Point(address.lat, address.lon), 4326),\
                      'SRID=4326;POINT({lat} {lon})', {range})"

    return text(query_template)

def get_basic_config(tablename):
    """
      PURPOSE : Maps basic configuration with table type
       PARAMS :  tablename: str
      RETURNS :  basic_config : dict
    """

    id = uuid.uuid4().hex
    date_created = datetime.now()

    basic_config = {
        "entity" : {
            'id' : id,
            'date_created' : date_created,
            'is_verified' : False
        },

        "users" : {
            'id' : id,
            'date_created' : date_created,
            'active' : True
        },

        "access" : {
            'id' : id,
            'date_created' : date_created
        },
    }

    # if there aren't additional it adds just an id
    return basic_config.get(tablename, {'id' : id})

def get_description(filtered_object, object_type, iso3_language = 'ENG'):
    """
        Returns an object joined with the description column based on filter
        language
    """
    return filtered_object.outerjoin(EntityLanguage, object_type.entity_id == EntityLanguage.entity_id)\
                .add_columns(EntityLanguage.description)\
                .filter(EntityLanguage.iso3_language == iso3_language)

def get_entity(entity):
    """
        Returns a dictionary of entity table columns used in catalog
    """
    weekly_schedule = get_schedule(entity.schedules)
    properties = get_propertites(entity.properties)
    tags = get_tags(entity.category)

    entity_extension =  {
        'comments' : [c.serialize for c in entity.comment],
        'comment_count' : len(entity.comment),
        'emails' : [e.serialize for e in entity.emails],
        'phones' : [p.serialize for p in entity.phones],
        'properties' : properties,

        'schedule' : weekly_schedule,
        'tags' : tags
    }

    if (entity.address):
        address = entity.address.serialize
        entity_extension['location'] = address
        entity_extension['lat'] = address['lat']
        entity_extension['lon'] = address['lon']
        entity_extension['region'] = f"{address['city']}, {address['state']}"

    return dict(entity.serialize, **entity_extension)

def get_object_description(objects, object_type, get_function, iso3_language = 'ENG', limit = 20, offset = 0):
    """
        Returns list of dictionaries of selected object with their languages
        specific descriptions
    """
    temp = get_description(objects, object_type, iso3_language)
    object_collection = temp.limit(limit).offset(offset).all()

    result_object = []
    for object, description in object_collection:
        result_object.append(get_function(object, description))

    return result_object

def get_organization(organization, description):
    """
        Returns dictionary of organization table with the inherited ones
        e.g: entity
    """
    deduplicate = lambda x: list(set(x))

    all_ratings = []
    all_tags = []
    all_properties = []

    service_collection = organization.service
    for service in service_collection:
        entity = service.entity

        all_tags = all_tags + get_tags(entity.category)
        all_properties = all_properties + [*get_propertites(entity.properties)]

        if entity.rating is not None:
            all_ratings.append(entity.rating)

    organization_extension = {
        'description' : description,
        'opportunity_count' : len(service_collection),
        'opportunity_communitiy_properties' : deduplicate(all_properties),
        'resource_type' : 'organization',
        'opportunity_tags' : deduplicate(all_tags)
    }

    if(len(all_ratings)):
        organization_extension['opportunity_aggregate_ratings'] = round(np.mean(all_ratings),1)

    organization_extension.update(get_entity(organization.entity))
    return dict(organization.serialize, **organization_extension)

def get_propertites(property_collection):
    """
        Returns dictionary of serialize objects
    """
    properties = dict()
    # Update returns null not the dictionary
    [properties.update(p.serialize) for p in property_collection]
    return properties

def get_service(service, description):
    """
        Returns dictionary of service with inherited values from entity
    """
    service_extended = {
        'description' : description,
        'access_instructions' : [s.serialize for s in service.access],
        'resource_type' : 'opportunities',
        'organization' : service.organization.serialize
    }

    service_extended.update(get_entity(service.entity))

    return dict(service.serialize, **service_extended)

def get_schedule(schedules):
    """
        Returns dictionary of time in 1D format


        TODO: once fully integrated we want to allow for time blocks instead of
              just start and end
    """
    weekly_schedule = dict()

    for schedule in schedules:
        weekday = schedule.day_times.day.day.lower()
        timeblock = schedule.day_times.timeblock

        weekly_schedule[f'{weekday}_start'] = f'{timeblock.start_time}'
        weekly_schedule[f'{weekday}_end'] = f'{timeblock.end_time}'

    return weekly_schedule

def get_tags(tag_collection):
    """
        Returns a list of tag parent name (overarching tag name) based on given
        tags. Includes duplicates
    """
    tags = []
    for tag in tag_collection:
        tags.append(Category.query.filter_by(id = tag.parent_id).one().name)

    return tags

def filter_query(object, query, range = 5):
    """
        Returns an query object of the same type as the object given with
        the filter applied

        TODO: add limit. Will take too long if you query the entire database
              each time. Right now adding limit before the rest of the query
              produces an error
    """

    query_object = object.query
    if query['lat'] and query['lon']:
        location_query = within_location_query(object.__tablename__,query['lat'], query['lon'], range)
        object_in_range = object.query.from_statement(location_query).all()
        object_id = [o.id for o in object_in_range]
        query_object = query_object.filter(object.id.in_(object_id))

    if query['tags']:
        query_object = query_object.filter(Category.id.in_(query['tags']))

    if query['property']:
        query_object = query_object.filter(Property.name.in_(query['property']))

    return query_object

def filter_object(object, raw_query, range = 5):
    """
        Return a list of object filtered by the query as well as a limit per
        page based on query
    """
    if raw_query:
        query = parse_query(raw_query)
        limit = query['per_page']
        offset = query['page']
        filtered_object = filter_query(object, query)

    else:
        limit = 20
        offset = 0
        filtered_object = object.query

    return filtered_object, limit, offset

def upload_time_block(schedule):
    """
     *  PURPOSE : Given a schedule upload the time blocks
     *   PARAMS : schedule: dict -
     *            E.g:    "schedule" : {
     *                         "Sunday" : [],
     *                         "Monday" : ["9AM-5PM"],
     *                         "Tuesday" : ["9AM-12PM","3PM-6PM"]
     *                   }
     *  RETURNS : sched: list - list day_time ids for given schedule
     *  NOTES : most time the onus is in the client to check before inserting
    """
    sched = []
    for day, times in schedule.items():
        for time in times:
            start_time, end_time = time.split('-')
            filter_time = {
                'start_time' : convert_str_time(start_time),
                'end_time' : convert_str_time(end_time)
            }

            time_id = conditional_update(TimeBlock, filter_time)

            filter_daytime = {
                'time_id' : time_id,
                'day_id' : WEEKDAYS[day]
            }

            daytime_id = conditional_update(DayTime, filter_daytime)
            sched.append(daytime_id)

    db.session.commit()
    return sched

def single_query(object, id, iso3_language = 'ENG',column_name = None):
    result_object = object.query.filter_by(id = id)
    return get_description(result_object, object, iso3_language).one_or_none()

def client_error(error, message):
    message = {
        'status' : error,
        'message' : message
    }
    response = jsonify(message)
    response.status_code = error

    return response

def decompose_config(Table, config):
    """
     *  PURPOSE : Separates config file in two, one part that match the column in
     *            specified table
     *   PARAMS : Table: db.Model
     *            config: dict
     *  RETURNS : config_other: dict - config not in the table
     *            config_in_table: dict - config in the table
    """
    # string returned from __table__.columns: entity.id, user.first_name
    table_column = eval(str(Table.__table__.columns))
    table_column = [col.split('.',1)[1] for col in table_column]

    config_in_table = {}
    config_other = {}

    for key, value in config.items():
        if key in table_column:
            config_in_table[key] = value
        else:
            config_other[key] = value

    return config_in_table, config_other

def update_database(Table, config, commit=True, *args):
    """
     *  PURPOSE : Given a table it will upload the entry
     *   PARAMS : Table: db.Model
     *            config: dict
     *            commit: bool
     *            *args - list of tuple (Table: db.Model, tablename: str, table_config: dict)
     *  RETURNS :  config - dict of table configuration or None
     *  NOTES: can be cleaned up especially with args to make more general
    """
    basic_config = get_basic_config(Table.__tablename__)
    config = dict(basic_config, **config)
    try:
        new_entry = Table(**config)

        # TODO: clean this up so that it is more general
        if args:
            for Object, column_name, values in args[0]:
                objects = Object.query.filter(Object.id.in_(values))
                if column_name == 'properties':
                    [new_entry.properties.append(o) for o in objects]
                elif column_name == 'category':
                    [new_entry.category.append(o) for o in objects]

        db.session.add(new_entry)
        if commit:
            db.session.commit()
        return config
    except:
        return None

def convert_str_time(time, time_format=None):
    """
     *  PURPOSE : Converts string time to time
     *   PARAMS : time: str
     *            time_format: str - datetime string format standard
     *  RETURNS : time: datetime.time
     *    NOTES : fails if str does not match
    """
    if time_format is None:
        if ':' in time:
            time_format = '%I:%M%p'
        elif 'h' in time:
            time_format = '%Ih%M%p'
        else:
            time_format = '%I%p'

    return datetime.strptime(time,time_format).time()

def conditional_update(Table, filters):
    """
     *  PURPOSE : Updates if not duplicate entry
     *   PARAMS : Table: db.Model -
     *            filters: dict - all unique values in the entry
     *  RETURNS : id: str - can sometimes be an integer
     *    NOTES : does not commit changes so you have to commit them after
    """
    result = Table.query.filter_by(**filters).one_or_none()

    if result is None:
        config = update_database(Table, filters, commit=False)
        return config['id']
    else:
        return result.id


def set_schedule(schedule_config, entity_id, commit = False):
    """
     * PURPOSE : Upload schedule to database
     *  PARAMS : schedule_config: dict
     *           entity_id: str - has to already be in table
     *           commit: bool
     * RETURNS : schedule_config: dict
     *   NOTES : Does not change the value of the configuration
    """

    schedule_id = upload_time_block(schedule_config)

    for id in schedule_id:
        config = {'day_time_id' : id,
                   'entity_id' : entity_id
                 }

        update_database(Service, config, commit=commit)

    return schedule_config

def set_config_object(tablename, object_config, all_config):
    """
     * PURPOSE : Adds to the configuration based on specific table
     *           needs
     *  PARAMS : tablename: str
     *           object_config: dict
     *           all_config: dict
     * RETURNS : object_config: dict - updated configuration
     *   NOTES : order matters. Address must be created first and then entity &
     *           service needs to be created before access
    """
    # TODO: add configuration for organization
    # most other tables need a entity_relation & address
    if tablename == 'entity':
        object_config['address_id'] = all_config['address']['id']

    if tablename != 'entity' and tablename != 'address':
        object_config['entity_id'] = all_config['entity']['id']

    if tablename == 'access':
        object_config['service_id'] = all_config['service']['id']

    return object_config

def upload_object(table, table_config, other_config):
    """
     * PURPOSE : Upload object with configuration to database
     *  PARAMS : table: db.Model
     *           table_config: dict
     *           other_config: dict
     * RETURNS : config: dict
    """
    tablename = table.__tablename__

    if tablename == 'entity':
        config = update_database(table, table_config, False,
                                [(Property, 'properties', other_config['property_id']),
                                 (Category, 'category', other_config['category_id'])])

    elif tablename == 'schedule':
        config = set_schedule(other_config['schedule'],
                              table_config['entity_id'])
    else:
        config = update_database(table, table_config, commit = False)

    return {tablename : config}

@simpleApp.errorhandler(404)
def not_found():
    """
        Creates a json not found response
    """
    return client_error(404, f'Not Found:  {request.url}')

@simpleApp.errorhandler(400)
def bad_request():
    """
        Creates a json bad request
    """
    return client_error(400, f'Bad request')

@simpleApp.route('/asylum_connect/api/v1.0/managers', methods = ['GET','POST'])
def query_managers():
    if request.method == 'POST':
        user_config = request.json
        is_admin = user_config.pop('is_admin', False)

        user_config = update_database(Users, user_config, commit=False)
        manager_config = update_database(DataManager, {"user_id" : user_config['id'],
                                                       "is_admin" : is_admin})
        if manager_config is None:
            return bad_request()

        return jsonify({'user' : user_config,
                        'data_manager': manager_config,
                        'is_admin' : is_admin})
    else:
        users = DataManager.query.outerjoin(Users).all()

        result = []
        for u in users:
            manager = u.serialize
            manager.update(u.users.serialize)
            result.append(manager)

        return jsonify(data_manager = result)

    pass

@simpleApp.route('/asylum_connect/api/v1.0/users', methods = ['GET','POST'])
def query_users():
    if request.method == 'POST':
        """
            Returns json object of added user
        """
        user_config = update_database(Users, request.json)

        if user_config is None:
            return bad_request()
        else:
            return jsonify(new_user = user_config)

    else:
        """
            Returns json object of all users
        """
        users = Users.query.all()
        result = [u.serialize for u in users]

        return jsonify(users = result)

@simpleApp.route('/asylum_connect/api/v1.0/managers/<user_id>',methods = ['GET','PUT','DELETE'])
def query_manager(user_id):
    manager = DataManager.query.filter_by(id = user_id).outerjoin(Users).one_or_none()

    if manager is None:
        return not_found()

    if request.method == 'PUT':
        before_update = dict(manager.serialize,**manager.users.serialize)
        data = request.json

        for key, value in data.items():
            # you should not be allowed to change user id or id
            if key != 'id' or key != 'user_id':
                setattr(manager, key, value)
                setattr(manager.users, key, value)

        db.session.commit()
        return jsonify({'before_update' : before_update,
                        'now' : dict(manager.serialize,**manager.users.serialize)})

    if request.method == 'DELETE':
        db.session.delete(manager)
        db.session.commit()

        return f"data manager {user_id} deleted"
    else:
        return jsonify(data_manager = dict(manager.serialize,**manager.users.serialize))

@simpleApp.route('/asylum_connect/api/v1.0/users/<user_id>',methods = ['GET','PUT','DELETE'])
def query_user(user_id):
    """
        Returns json object of one user given user_id
    """
    user = Users.query.filter_by(id = user_id).one_or_none()
    if user is None:
        return not_found()

    if request.method == 'PUT':
        before_update = user.serialize
        data = request.json

        for key, value in data.items():
            if key != 'id':         # you should not be allowed to change user id
                setattr(user,key, value)

        db.session.commit()

        return jsonify({'before_update' : before_update,
                        'now' : user.serialize})

    elif request.method == 'DELETE':
        db.session.delete(user)
        db.session.commit()

        return f"user {user_id} deleted"
    else:
        return jsonify(users = user.serialize)

@simpleApp.route('/asylum_connect/api/v1.0/organizations')
def query_get_organizations():
    """
        Returns json object of all organizations based on filters
        specified by client
    """
    iso3_language = 'ENG' # Eventually property of user
    filtered_organization, limit, offset = filter_object(Organization, request.args)
    result = get_object_description(filtered_organization, Organization, get_organization, limit=limit, offset=offset)

    return jsonify(organizations = result)

@simpleApp.route('/asylum_connect/api/v1.0/organizations/<id>')
def query_get_organization(id):
    """
        Returns single organization. If column name is specified will return
        single property
    """
    query_result = single_query(Organization, id)
    if query_result is None:
        return not_found()
    else:
        return jsonify(organization=get_organization(*query_result))

@simpleApp.route('/asylum_connect/api/v1.0/organizations/<id>/<column_name>')
def query_get_organization_column(id, column_name):
    """
        Returns single service. If column name is specified will return
        single property
    """
    query_result = single_query(Organization, id)

    if query_result is None:
        return not_found()

    organization = get_organization(*query_result)

    if column_name in organization.keys():
        return jsonify({column_name : organization[column_name]})
    else:
        return not_found()

@simpleApp.route('/asylum_connect/api/v1.0/services', methods = ['GET', 'POST'])
def query_get_services():
    if request.method == 'POST':
        """
            Adds a service entry to database
        """
        service_config = request.json

        # order matters b/c of foreign key relationship
        tables = [Address, Entity, Email, Phone,
                EntityLanguage, Service,  Access, Schedule]
        all_config = {}

        for table in tables:
            tablename = table.__tablename__

            service_config = set_config_object(tablename, service_config, all_config)
            table_config, service_config = decompose_config(table, service_config)
            update_config = upload_object(table, table_config, service_config)

            all_config = dict(all_config, **update_config)

        try:
            db.session.commit()
            return jsonify(all_config)
        except:
            return bad_request()

    else:
        """
            Returns json objects of all services based on filters specified by client
        """
        filtered_service, limit, offset = filter_object(Service, request.args)
        result = get_object_description(filtered_service, Service, get_service, limit=limit)

        return jsonify(services=result)

@simpleApp.route('/asylum_connect/api/v1.0/services/<id>', methods = ['PUT', 'DELETE', 'GET'])
def query_get_service(id):
    """
        Returns single service. If column name is specified will return
        single property
    """
    # service, description
    query_result = single_query(Service, id)

    if query_result is None:
        return not_found()

    service = query_result[0]
    before_update = service.serialize
    date_now = datetime.now()

    if request.method == 'PUT':
        data = request.json

        for tablename, config in data.items():
            for key, value in config.items():
                if key != 'id' or key != entity_id:
                    if tablename == 'service':
                        table = service
                    elif tablename == 'access':
                        table = service.access
                    elif tablename == 'entity':
                        table = service.entity
                    elif tablname == 'entity_language':
                        table = service.entity.entity_language
                    elif tablename == 'address':
                        table = service.entity.address

                    setattr(table, key, value)
                    setattr(table, 'date_updated', date_now)
            # you should not be allowed to change user id or id
            # if key != 'id' or key != 'user_id':
            #     setattr(manager,key, value)
            #     setattr(manager.users, key, value)

        db.session.commit()
        return jsonify({'before_update' : before_update,
                        'now' : service.serialize})
        pass
    elif request.method == 'DELETE':
        entity = Entity.query.filter_by(id=service.entity_id).one_or_none()

        db.session.delete(service)
        db.session.commit()

        return f"service {id} deleted"
    else:
        return jsonify(service= get_service(*query_result))

@simpleApp.route('/asylum_connect/api/v1.0/services/<id>/<column_name>')
def query_get_service_column(id, column_name):
    """
        Returns single service. If column name is specified will return
        single property
    """
    query_result = single_query(Service, id)

    if query_result is None:
        return not_found()

    service = get_service(*query_result)

    if column_name in service.keys():
        return jsonify({column_name : service[column_name]})
    else:
        return not_found()

@simpleApp.route('/asylum_connect/api/v1.0/locations')
def query_get_locations():
    """
        Returns all locations available
    """
    location = Address.query.all()
    return jsonify(location = [l.serialize for l in location])

@simpleApp.route('/asylum_connect/api/v1.0/tags')
def query_get_tags():
    temp = request.args
    for key, val in temp.items():
        print(f'{key} : {val}')

    return jsonify(tags = [t.serialize for t in Category.query.all()])

@simpleApp.route('/asylum_connect/api/v1.0/<user_id>/favorites')
def query_get_favorite(user_id):
    """
        Returns all opportunities and servicess that are in user favorites
    """
    # Ideally you want to store services and opportunities
    favorites = UserFavorites.query.filter_by(user_id = user_id).all()
    entity_ids = [f.entity_id for f in favorites]

    services = Service.query.filter(Service.entity_id.in_(entity_ids))
    organizations = Organization.query.filter(Organization.entity_id.in_(entity_ids))

    result_services = get_object_description(services, Service, get_service)
    result_organization = get_object_description(organizations, Organization, get_organization)

    return jsonify(favorites = {'organizations':result_organization, 'opportunities' : result_services})
