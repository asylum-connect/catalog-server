import random, uuid
import numpy as np
from application import simpleApp, db
from flask import render_template, request
from flask import Flask, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, text

from .models import *
from .core import db

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
                      FROM {object_name}, tags, address\
                      WHERE ST_DWithin(ST_SetSRID(\
                      ST_Point(address.lat, address.lon), 4326),\
                      'SRID=4326;POINT({lat} {lon})', {range})"

    return text(query_template)

def get_description(filtered_object, type_object, iso3_language = 'ENG'):
    """
        Returns an object joined with the description column based on filter
        language
    """
    return filtered_object.outerjoin(EntityLanguage, type_object.entity_id == EntityLanguage.entity_id)\
                .add_columns(EntityLanguage.description)\
                .filter(EntityLanguage.iso3_language == iso3_language)

def get_entity(entity):
    """
        Returns a dictionary of entity table columns used in catalog
    """
    address = entity.address.serialize
    weekly_schedule = get_schedule(entity.schedules)
    properties = get_propertites(entity.properties)
    tags = get_tags(entity.tags)

    entity_extension =  {
        'comments' : [c.serialize for c in entity.comments],
        'comment_count' : len(entity.comments),
        'emails' : [e.serialize for e in entity.emails],
        'lat' : address['lat'],
        'lon' : address['lon'],
        'location' : address,
        'phones' : [p.serialize for p in entity.phones],
        'properties' : properties,
        'region' :f"{address['city']}, {address['state']}",
        'schedule' : weekly_schedule,
        'tags' : tags
    }

    return dict(entity.serialize, **entity_extension)

def get_organization(organization, description):
    """
        Returns dictionary of organization table with the inherited ones
        e.g: entity
    """
    # import sys
    # print(f'==============\n\nORG: {organization}', file=sys.stderr)
    deduplicate = lambda x: list(set(x))

    all_ratings = []
    all_tags = []
    all_properties = []

    service_collection = organization.services
    for service in service_collection:
        entity = service.entity

        all_tags = all_tags + get_tags(entity.tags)
        all_properties = all_properties + [*get_propertites(entity.properties)]
        all_ratings.append(entity.rating)

    organization_extension = {
        'description' : description,
        'opportunity_count' : len(service_collection),
        'opportunity_communitiy_properties' : deduplicate(all_properties),
        'opportunity_aggregate_ratings' : round(np.mean(all_ratings),1),
        'resource_type' : 'organization',
        'opportunity_tags' : deduplicate(all_tags)
    }

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
        tags.append(Tags.query.filter_by(id = tag.parent_tag).one().name)

    return tags

def filter_query(object, query, range = 500):
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
        query_object = query_object.filter(Tags.id.in_(query['tags']))

    if query['property']:
        query_object = query_object.filter(Property.name.in_(query['property']))

    return query_object

def filter_object(object, raw_query, range = 500):
    """
        Return a list of object filtered by the query as well as a limit per
        page based on query
    """
    if raw_query:
        query = parse_query(raw_query)
        limit = query['per_page']
        filtered_object = filter_query(object, query)

    else:
        limit = 10
        filtered_object = object.query

    return filtered_object, limit

def single_query(object, id, iso3_language = 'ENG',column_name = None):
    result_object = object.query.filter_by(id = id)
    import sys
    return get_description(result_object, object, iso3_language).one_or_none()

@simpleApp.errorhandler(404)
def not_found(error = None):
    """
        Creates a json 404 response
    """
    message = {
        'status' : 404,
        'message' : f'Not Found: {request.url}'
    }

    response = jsonify(message)
    response.status_code = 404

    return response

@simpleApp.route('/asylum_connect/api/v1.0/users', methods = ['GET'])
def userFunction():
    """
        Returns json object of all users
    """
    users = AsylumSeeker.query.outerjoin(Users).all()

    result = []
    for u in users:
        dict1 = u.serialize
        dict1.update(u.user.serialize)
        result.append(dict1)

    return jsonify(users = result)

@simpleApp.route('/asylum_connect/api/v1.0/user=<user_id>')
def query_get_user(user_id):
    """
        Returns json object of one user given user_id
    """
    users = AsylumSeeker.query.filter_by(user_id = user_id).one()
    return jsonify(users = users.serialize)


@simpleApp.route('/asylum_connect/api/v1.0/organizations')
def query_get_organizations():
    """
        Returns json object of all organization
    """
    iso3_language = 'ENG' # Eventually property of user
    filtered_organization, limit = filter_object(Organization, request.args)

    organization_collection = get_description(filtered_organization, Organization, iso3_language)\
                                .limit(limit).all()
    result = []

    for organization, description in organization_collection:
        result.append(get_organization(organization, description))

    return jsonify(organization = result)

@simpleApp.route('/asylum_connect/api/v1.0/services')
def query_get_services():
    iso3_language = 'ENG'
    filtered_service, limit = filter_object(Services, request.args)

    service_collection = get_description(filtered_service, Services, iso3_language).limit(limit).all()

    result = []
    for service, description in service_collection:
        result.append(get_service(service, description))

    return jsonify(opportunities=result)

@simpleApp.route('/asylum_connect/api/v1.0/service/<id>')
def query_get_service(id):
    """
        Returns single service. If column name is specified will return
        single property
    """
    query_result = single_query(Services, id)
    if query_result is None:
        return not_found()
    else:
        return jsonify(opportunity= get_service(*query_result))

@simpleApp.route('/asylum_connect/api/v1.0/service/<id>/<column_name>')
def query_get_service_column(id, column_name):
    """
        Returns single service. If column name is specified will return
        single property
    """
    query_result = single_query(Services, id)

    if query_result is None:
        return not_found()

    service = get_service(*query_result)

    if column_name in service.keys():
        return jsonify({column_name : service[column_name]})
    else:
        return not_found()

@simpleApp.route('/asylum_connect/api/v1.0/organization/<id>')
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

@simpleApp.route('/asylum_connect/api/v1.0/organization/<id>/<column_name>')
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

    return jsonify(tags = [t.serialize for t in Tags.query.all()])
