# PyMySQL puro-Python como driver MySQLdb: evita compilar mysqlclient
# (sin apt, sin build-essential). Mantiene la API flask_mysqldb intacta.
import pymysql

pymysql.install_as_MySQLdb()

from flask import Flask
from config import Config
from Routes import load_routes
from flask_mysqldb import MySQL

app = Flask(__name__)

app.config.from_object(Config)

mysql = MySQL(app)
app.mysql = mysql

load_routes(app) 

 
if __name__ == "__main__": 
    app.run(debug=True, port=5000, host='0.0.0.0')