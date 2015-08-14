from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
import os
from sqlalchemy.dialects.postgresql import JSON
from rq import Queue
from rq.job import Job
from worker import conn

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
q = Queue(connection=conn)
db = SQLAlchemy(app)
from models import Result

@app.route('/')
def hello():
    return "Hello World!"


@app.route('/<name>')
def hello_name(name):
    return "Hello {}!".format(name)


if __name__ == '__main__':
    app.run()
