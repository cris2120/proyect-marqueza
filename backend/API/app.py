from flask import Flask
from config import Config
from Routes import load_routes
from flask_mysqldb import MySQL
from orm import configure_orm

app = Flask(__name__)

app.config.from_object(Config)

mysql = MySQL(app)
app.mysql = mysql
configure_orm(app)

load_routes(app)


if __name__ == "__main__":
	app.run(debug=True, port=5000, host="0.0.0.0")