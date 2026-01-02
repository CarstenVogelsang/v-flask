"""
v-flask - Flask Core Extension Package

Wiederverwendbares Basis-Paket mit User, Config, Logging, Auth für Flask-Anwendungen.

Verwendung:
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    from v_flask import VFlask

    app = Flask(__name__)
    db = SQLAlchemy(app)
    v = VFlask(app, db)

    # Models importieren
    from v_flask.models import User, Rolle, Config, LookupWert
"""

__version__ = "0.1.0"

# TODO: VFlask Extension-Klasse implementieren
# class VFlask:
#     def __init__(self, app=None, db=None):
#         ...
#     def init_app(self, app, db):
#         ...
