"""
v-flask Extensions

Central place for Flask extensions used by v-flask.
The db instance is shared with the host application.
"""

from flask_sqlalchemy import SQLAlchemy

# SQLAlchemy instance for v-flask models
# Will be initialized by VFlask.init_app() or can be replaced by host app's db
db: SQLAlchemy = SQLAlchemy()
