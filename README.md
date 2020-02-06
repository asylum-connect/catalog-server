# catalog-server
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

## Other information
* the base URL is http://localhost:5000/asylum_connect/api/v1.0/
