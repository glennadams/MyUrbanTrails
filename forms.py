from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Email, Length

class UserAddForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    address = StringField('Location Address (Optional)')


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])

class UserEditProfile(FlaskForm):
    """Edit profile for user."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    address = StringField('Location Address (Optional)')

class TrailAddForm(FlaskForm):
    """Form for adding a users trail"""
    name = StringField('name', validators=[DataRequired(), Length(max=100)])
   

class NoteAddForm(FlaskForm):
    """Form for adding notes to a trail"""
    title = StringField('title', validators=[DataRequired(), Length(max=140)])
    comment = StringField('comment', validators=[DataRequired()])
