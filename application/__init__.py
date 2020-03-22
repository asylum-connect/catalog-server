from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint

simpleApp = Flask(__name__)

# simpleApp.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/sample-flask-app-with-postgresql'
simpleApp.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://asylum_connect:qvrzT5HgFe3Ng7ZB1kHj@ac-development.cimgucyve7tg.us-east-1.rds.amazonaws.com:5432/postgres'
db = SQLAlchemy(simpleApp)
CORS(simpleApp)

SWAGGER_URL = '/docs'
API_URL = '/static/swagger.json'
SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Catalog Server"
    }
)
simpleApp.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)

from application import routes
