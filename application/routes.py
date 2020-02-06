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
    tags = [tags_mapping(i) for i in query.getlist('query[tags][]')]

    sub = 'query[properties]'
    properties = [i.split(sub)[1][1:-1] for i in query.keys() if sub in i]
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
    query_template = f"SELECT {object_name}.id AS {object_name}_id\
                      FROM {object_name}, tags, address\
                      WHERE ST_DWithin(ST_SetSRID(ST_Point(address.lat, address.lon), 4326),'SRID=4326;POINT({lat} {lon})', {range})"
    return text(query_template)

# routing

def get_entity(entity):
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

    all_ratings = []
    all_tags = []
    all_properties = []

    service_collection = organization.services
    deduplicate = lambda x: list(set(x))

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

    print(f'ALL PROPS: {all_properties} \n ALL TAGS: {all_tags}')

    organization_extension.update(get_entity(organization.entity))
    return dict(organization.serialize, **organization_extension)

def get_propertites(property_collection):
    properties = dict()
    # Update returns null not the dictionary
    [properties.update(p.serialize) for p in property_collection]
    return properties

def get_service(service, description):
    service_extended = {
        'description' : description,
        'access_instructions' : [s.serialize for s in service.access],
        'resource_type' : 'opportunities',
        'organization' : service.organization.serialize
    }

    service_extended.update(get_entity(service.entity))

    return dict(service.serialize, **service_extended)

def get_schedule(schedules):
    weekly_schedule = dict()

    for schedule in schedules:
        weekday = schedule.day_times.day.day.lower()
        timeblock = schedule.day_times.timeblock

        weekly_schedule[f'{weekday}_start'] = f'{timeblock.start_time}'
        weekly_schedule[f'{weekday}_end'] = f'{timeblock.end_time}'

    return weekly_schedule

def get_tags(tag_collection):
    tags = []
    for tag in tag_collection:
        tags.append(Tags.query.filter_by(id = tag.parent_tag).one().name)

    return tags

def filter_query(object, query, range = 500):

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

    if raw_query:
        query = parse_query(raw_query)
        limit = query['per_page']
        filtered_object = filter_query(object, query)

    else:
        limit = 10
        filtered_object = object.query

    return filtered_object, limit


@simpleApp.route('/asylum_connect/api/v1.0/users', methods = ['GET'])
def userFunction():
    users = AsylumSeeker.query.outerjoin(Users).all()

    result = []
    for u in users:
        dict1 = u.serialize
        dict1.update(u.user.serialize)
        result.append(dict1)

    return jsonify(users = result)

@simpleApp.route('/asylum_connect/api/v1.0/user=<user_id>')
def query_get_user(user_id):
    users = AsylumSeeker.query.filter_by(user_id = user_id).one()
    print(f'======================== {user_id} ==========================')
    return jsonify(users = users.serialize)


@simpleApp.route('/asylum_connect/api/v1.0/organizations')
def query_get_organizations():
    iso3_language = 'ENG' # Eventually property by user
    filtered_organization, limit = filter_object(Organization, request.args)

    organization_collection = filtered_organization.outerjoin(EntityLanguage, Organization.entity_id == EntityLanguage.entity_id)\
        .add_columns(EntityLanguage.description)\
        .filter(EntityLanguage.iso3_language == iso3_language).limit(limit).all()
    result = []

    for organization, description in organization_collection:
        result.append(get_organization(organization, description))

    return jsonify(organization = result)

@simpleApp.route('/asylum_connect/api/v1.0/services')
def query_get_services():
    iso3_language = 'ENG'
    filtered_service, limit = filter_object(Services, request.args)

    service_collection = filtered_service.outerjoin(EntityLanguage, Services.entity_id == EntityLanguage.entity_id)\
        .add_columns(EntityLanguage.description)\
        .filter(EntityLanguage.iso3_language == iso3_language).limit(limit).all()

    result = []
    for service, description in service_collection:
        result.append(get_service(service, description))

    return jsonify(opportunities=result)

@simpleApp.route('/asylum_connect/api/v1.0/service/{id}/{column_name}')
def query_get_service():
    pass

@simpleApp.route('/asylum_connect/api/v1.0/organization/{id}/{column_name}')
def query_get_organization():
    pass

@simpleApp.route('/asylum_connect/api/v1.0/locations')
def query_get_locations():
    location = Address.query.all()
    return jsonify(location = [l.serialize for l in location])

@simpleApp.route('/asylum_connect/api/v1.0/tags')
def query_get_tags():
    temp = request.args
    for key, val in temp.items():
        print(f'{key} : {val}')

    return jsonify(tags = [t.serialize for t in Tags.query.all()])
