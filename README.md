# catalog-server

[![Build Status](https://travis-ci.org/asylum-connect/catalog-server.svg?branch=master)](https://travis-ci.org/asylum-connect/catalog-server)

A Flask API

## Dependencies
* [PostgreSQL](https://www.postgresql.org/download/)

## To Run
1. Open Terminal and start a PostgreSQL server by executing `pg_ctl -D /usr/local/var/postgres start` in any directory on the machine where PostgreSQL has been installed.
2. Clone this repo locally.
2. Open Terminal and point to the directory of the local clone.
3. Launch the virtual environment by executing `source virtual-environment/bin/activate`.
4. Run application in the virtual environment by executing `flask run`.
5. Open browser and go to Flask's default port http://localhost:5000/.

## Endpoints:
* the base URL is http://localhost:5000/asylum_connect/api/v1.0/

Currently all the routes are GET methods

> GET /baseURL/user=1746

RESPONSE
```
{
    "users": {
        "first_name": "Cam",
        "last_name": "Mbayo",
        "user_id": 1746
    }
}
```

> GET /baseURL/1746/favorites

RESPONSE
```
{
    "favorites": {
        "opportunities": [],
        "organizations": [
            {
                ...
                "id": "3f2e7b4b-a9fd-4b30-9af2-c02404320f11",
                "is_closed": false,
                "last_verified": "Sat, 01 Feb 2020 00:00:00 GMT",
                ...
                "phones": [
                    {
                        "digits": "2023555155",
                        "id": 1,
                        "is_primary": true,
                        "phone_type": ""
                    }
                ],
                "properties": {
                    "cost-free": true,
                    "not-req-medical-insurance": true,
                    "service-county-maryland-montgomery": true
                },
                "rating": 0.0,
                ...
        ]
    }
}
```

> GET /baseURL/organizations

> GET /baseURL/services

RESPONSE
exhaustive list of organizations and service. Filters can be added

same filters apply for organizations as well
> GET /baseURL/services?query[properties][community-asylum-seeker]=true&query[properties][community-lgbt]=true&query[lat]=38.9656971&query[long]=-77.0622028&page=1&per_page=10

RESPONSE
```
"opportunities": [
        {
            "access_instructions": [
                {
                    "access_type": "location",
                    "access_value": "",
                    "enabled_direct_acess": false,
                    "id": 2,
                    ...
                },
                {
                    "access_type": "link",
                    "access_value": "http://casaruby.org/contact.html",
                    "enabled_direct_acess": false,
                    "id": 1,
                    ...
                }
            ],
            "comment_count": 0,
            "comments": [],
            "description": "Casa Ruby's Drop Inn-Community Center is the only bilingual multicultural LGBT ..."
            ...
    ]
```


> GET /baseURL/organization/3f2e7b4b-a9fd-4b30-9af2-c02404320f11

RESPONSE
```
{
    "organization": {
        "comment_count": 2,
        "comments": [
            {
                "comment": "I think this is super cool",
                "date_updated": "Sun, 02 Feb 2020 22:58:49 GMT",
                "id": "35c9ed84-e2f5-4593-8723-99152a3d4897",
                "user_id": 1746
            },
            {
                "comment": "Again heavilty recommend",
                ...
            }
        ],
        ...
        "schedule": {
            "friday_end": "17:00:00",
            "friday_start": "09:00:00",
            ...
        },
        "tags": [],
        "updated_at": "Sat, 01 Feb 2020 00:00:00 GMT",
        ...
    }
}
```

For more granular information on specific organization or service you the column you want to extract
> GET /baseURL/organization/3f2e7b4b-a9fd-4b30-9af2-c02404320f11/Comments

```
{
    "comments": [
        {
            "comment": "I think this is super cool",
            "date_updated": "Sun, 02 Feb 2020 22:58:49 GMT",
            "id": "35c9ed84-e2f5-4593-8723-99152a3d4897",
            "user_id": 1746
        },
        {
            "comment": "Again heavilty recommend",
            ...
        }
    ]
}
```
