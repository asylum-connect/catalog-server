from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

simpleApp = Flask(__name__)

# simpleApp.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/sample-flask-app-with-postgresql'
simpleApp.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://asylum_connect:qvrzT5HgFe3Ng7ZB1kHj@ac-development.cimgucyve7tg.us-east-1.rds.amazonaws.com:5432/postgres'
db = SQLAlchemy(simpleApp)
CORS(simpleApp)

from application import routes
