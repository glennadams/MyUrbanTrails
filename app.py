from flask import Flask, request, render_template, redirect, flash, jsonify, session, g
from sqlalchemy.exc import IntegrityError
from models import db, connect_db, Trail, User, Note
from forms import UserAddForm, UserEditProfile, LoginForm, TrailAddForm, NoteAddForm

app = Flask(__name__)

app.config['SECRET_KEY'] = 'A very very secret key'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///urbanmaps_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

connect_db(app)
CURR_USER_KEY = "curr_user"

##############################################################
#              Home page route                               #
##############################################################

@app.route('/')
def start_homepage():
    return render_template('home.html')

##############################################################
#              Setup Flask global user variable              #
##############################################################

@app.before_request
def add_user_to_g():
    """If user is logged in, add current user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None

def do_login(user):
    """Log in user, by adding user tosession."""
    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user, by deleting user from session."""
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

##############################################################
#              routes for users                              #
##############################################################

@app.route('/users/register', methods=["GET", "POST"])
def signup():
    """ Run user setup:  
        - Validate unique username or flash error.
        - If form invalid, display new form
        - Add user to db if validation passes
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.register(
                username=form.username.data,
                password=form.password.data,
                email = form.email.data,
                address = form.address.data
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('register.html', form=form)

        do_login(user)
        return redirect("/")

    else:
        return render_template('register.html', form=form)


@app.route('/users/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('login.html', form=form)


@app.route('/users/logout')
def logout():
    """Handle logout of user."""

    do_logout()
    flash("You have been logged out, Thanks for visiting!", "success")
    
    return redirect('/users/login')


##### route to user page #####
@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    '''Gets user page with trails'''

    # Add list of trails for user
    # name of trail, distance, duration
    user = User.query.get_or_404(id)

    trails = (Trail.query
                .filter(Trail.user_id == id)
                .limit(10)
                .all())
    
    return render_template('usertrails.html', user=user, trails=trails)


##### route to UPDATE user #####
@app.route('/users/profile', methods=['GET','POST'])
def get_user_profile():
    '''Update profile for current user'''
    
    user = g.user
    print(f'g.user: {g.user} g.user.id: {g.user.id}')
    form = UserEditProfile(obj=user)
    
    # return render_template('test.html')

    if form.validate_on_submit():
        user_check = User.authenticate(form.username.data,
                                       form.password.data)

        if user_check:
            user.username = form.username.data
            user.email = form.email.data
            user.address = form.address.data
            db.session.commit()
            flash(f'User {user.username} updated', "success")
            # return redirect(f'/users/{g.user.id}')
            return render_template('test.html')
        else:
            flash(f'Incorrect Password. User {user.username} not updated', "warning")
            return redirect('/')

    return render_template('profile.html', form=form, user_id=g.user.id)


##### route to DELETE user #####
@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    '''Delete user'''
    
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/")

##############################################################
#              routes for trails                             #
##############################################################
@app.route('/api/trails', methods=['GET'])
def map_routes():
    '''Get all trails'''

    # format each trail form trail_data 
    trails = [trail.to_coords_array() for trail in Trail.query.all()]
    
    return jsonify(trails=trails)

@app.route('/api/trails/<int:id>', methods=['GET'])
def get_maproute(id):
    '''Get a map route and return details'''
    new_trail = Trail.query.get_or_404(id).to_coords_array()
    
    return jsonify(maproute=new_trail)

@app.route('/api/trails', methods=['POST'])
def add_maproute():
    '''Store a user map route'''
    name = request.json["name"]
    coords = request.json["coordinates"]
    distance = request.json["distance"]
    duration = request.json["duration"]
    user_id = LOGGED_IN_USER;
    
    newTrail = Trail(name=name,
                    distance=distance,
                    duration=duration,
                    coordinates=coords,
                    user_id=user_id)
    db.session.add(newTrail)
    db.session.commit()
    response = jsonify(maproute=newTrail.to_coords_array())

    return (response, 201)

@app.route('/api/trails/<int:id>', methods=['PATCH'])
def update_maproute(id):
    '''Update maproute name'''

    trail = Trail.query.get_or_404(id)
    trail.name = request.json.get('name', trail.name)
    db.session.commit()

    return (jsonify(maproute=trail.to_coords_array()))
    

@app.route('/api/trails/<int:id>', methods=['DELETE'])
def delete_maproute(id):
    '''Delete a maproute'''
    trail = Trail.query.get_or_404(id)
    db.session.delete(trail)
    db.session.commit()

    return jsonify(message="deleted")


##############################################################
#              routes for notes                              #
##############################################################

@app.route('/api/trails/<int:trail_id>/notes', methods=['GET'])
def get_trail_notes(trail_id):
    '''Get all notes for a trail'''

    notes = Note.query.filter(Note.trail_id==trail_id).all()
    noteList = [{"id": note.id, 
                "comment": note.comment,
                "timestamp": note.timestamp,
                "trail_id": trail_id} for note in notes]
        
    return jsonify(noteList)
    

@app.route('/api/trails/<int:trail_id>/notes/<int:note_id>', methods=['GET'])
def get_trail_note(trail_id, note_id):
    '''Get a single note'''
    note = Note.query.filter(Note.id==note_id, Note.trail_id==trail_id).one_or_none()
    noteList = {"id": notes.id, "comment": notes.comment,
                "timestamp": notes.timestamp, "trail_id": trail_id}
                
    return jsonify(noteList);


@app.route('/api/trails/<int:trail_id>/notes', methods=['POST'])
def add_trail_note(trail_id):
    '''Add a note to a trail'''
    comment = request.json['comment']
    note = Note(comment=comment, trail_id=trail_id)
    db.session.add(note)
    db.session.commit()
    response = jsonify(note={"id": note.id, "comment": note.comment,
                "timestamp": note.timestamp, "trail_id": note.trail_id})
    
    return (response, 201);


@app.route('/api/trails/<int:trail_id>/notes/<int:note_id>', methods=['PATCH'])
def update_note(trail_id, note_id):
    '''Update a note'''
    note = Note.query.filter(Note.id==note_id, Note.trail_id==trail_id).one_or_none()
    note.comment = request.json['comment']
    db.session.commit()
    response = jsonify(note={"id": note.id, "comment": note.comment,
                "timestamp": note.timestamp, "trail_id": note.trail_id})

    return (response, 200);


@app.route('/api/trails/<int:trail_id>/notes/<int:note_id>', methods=['DELETE'])
def delete_note(trail_id, note_id):
    '''Delete a note'''
    note = Note.query.filter(Note.id==note_id, Note.trail_id==trail_id).one_or_none()
    db.session.delete(note)
    db.session.commit()

    return jsonify(message="deleted")




    
