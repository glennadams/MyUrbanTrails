from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
# import ast class for literal_eval() method convert stringdata
import ast

db = SQLAlchemy()
bcrypt = Bcrypt()

def connect_db(app):
    db.app = app
    db.init_app(app)



class User(db.Model):
    """Site user."""

    __tablename__ = "users"

    id = db.Column(db.Integer, 
                   primary_key=True, 
                   autoincrement=True)
    username = db.Column(db.Text, 
                         nullable=False, 
                         unique=True)
    password = db.Column(db.Text, 
                         nullable=False)
    address = db.Column(db.Text)
    email = db.Column(db.String(120))
    


    # class method to register user
    @classmethod
    def register(cls, username, password, email, address):
        """Register user w/hashed password & return user."""

        hashed = bcrypt.generate_password_hash(password)
        # turn bytestring into normal (unicode utf8) string
        hashed_utf8 = hashed.decode("utf8")

        user = User(
            username=username,
            password=hashed_utf8,
            email=email,
            address=address
        )

        db.session.add(user)
        # return instance of user w/username and hashed pwd
        return user
        
    

    # class method to authenticate existing user
    @classmethod
    def authenticate(cls, username, pwd):
        """Validate that user exists & password is correct.

        Return user if valid; else return False.
        """

        u = User.query.filter_by(username=username).first()

        if u and bcrypt.check_password_hash(u.password, pwd):
            # return user instance
            return u
        else:
            return False


# Map class to define db schema to store user maps
class Trail(db.Model):
    '''
        Db schema to store user maps
        map coordinate data is stored as a long string of text

        to_coords_array() - converts db record to array format
    '''
    __tablename__ = 'trails'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    coordinates = db.Column(db.Text, nullable=False)
    distance = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id',
                        ondelete='CASCADE'),
                        nullable=False)
    
    user = db.relationship('User', backref="trails")

    def to_coords_array(self):
        ''' Converts mapdata from string to lists
            Sets up data in dictionary format
            Facilitates JSON conversion
        '''
        # convert mapdata text string to list of coordinates
        coords_text = self.coordinates.replace("{{", '[[').replace('},{', '],[').replace('}}', ']]')
        # convert to arrays
        coords_arr = ast.literal_eval(coords_text)
        
        # compose and return dicationary
        return {
            'id'   : self.id,
            'name': self.name,
            'distance': self.distance,
            'duration': self.duration,
            'coordinates' : coords_arr,
            'user_id': self.user_id
        }

    def __repr__(self):
        '''Formats data output for query'''
        return f"<Usermap {self.id} {self.name} >"


# User class to define db schema to store user data
# and provide authentication methods
class Note(db.Model):
    "Notes for each stored trail"

    __tablename__ = "notes"

    id = db.Column(db.Integer, 
                   primary_key=True, 
                   autoincrement=True)
    comment = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow())
    trail_id = db.Column(db.Integer,
                        db.ForeignKey('trails.id',
                        ondelete='CASCADE'),
                        nullable=False)

    trail = db.relationship('Trail', backref="notes")
    