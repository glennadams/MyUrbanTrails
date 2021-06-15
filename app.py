from flask import Flask, request, render_template, redirect, flash, jsonify, session, g
from sqlalchemy.exc import IntegrityError
from models import db, connect_db, Trail, User, Note
from forms import UserAddForm, UserEditProfile, LoginForm, TrailAddForm, NoteAddForm

app = Flask(__name__)

app.config['SECRET_KEY'] = 'A very very secret key'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///urbanmaps_test_db'
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

#############################################################
#             Setup Flask global user variable              #
#############################################################

@app.before_request
def add_user_to_g():
    """If user is logged in, add current user to Flask global."""
    print(f'****** add_user_to_g() running')
    print(f'SESSION: {session.get(CURR_USER_KEY)}')
    if CURR_USER_KEY in session:
        
        g.user = User.query.get(session[CURR_USER_KEY])
        print(f'***** g.user at loggin: ', g.user)
    else:
        g.user = None

def do_login(user):
    """Log in user, by adding user tosession."""
    session[CURR_USER_KEY] = user.id
    print(f'**** LOGGING IN ****  session[CURR_USER_KEY]: ', session.get(CURR_USER_KEY), '-- user.id: ', user.id)


def do_logout():
    """Logout user, by deleting user from session."""
    print(f'**** LOGGING OUT ***** session[CURR_USER_KEY]: ', session.get(CURR_USER_KEY))
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

##############################################################
#              routes for users                              #
##############################################################

####     User Registration    ######
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


####     User Login            ######
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
            return redirect(f'/users/{user.id}')

        flash("Invalid Password.", 'danger')

    return render_template('login.html', form=form)


####     User Logout           ######
@app.route('/users/logout')
def logout():
    """Handle logout of user."""

    do_logout()
    flash("You have been logged out, Thanks for visiting!", "success")

    return redirect('/users/login')


###     User page              ######
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    '''Gets user page with trails'''

    # Add list of trails for user
    # name of trail, distance, duration
    print(f'***** g.user at /users/{user_id}: ', g.user)
    user = User.query.get_or_404(user_id)

    trails = Trail.query.filter(Trail.user_id == user_id).all()
    trailList = [{"id": trail.id, 
                "name": trail.name,
                "duration": trail.duration,
                "distance": trail.distance} for trail in trails]
    print('**** Trails: ', trailList)
    
    return render_template('userpage.html', user=user, trails=trailList)


####    User Profile UPDATE     ######
@app.route('/users/profile', methods=['GET','POST'])
def get_user_profile():
    '''Update profile for current user'''
    print(f'***** g.user at /users/profile: ', g.user)
    print(f'#### /users/profile #### session[CURR_USER_KEY]: {session.get(CURR_USER_KEY)}')
    user = User.query.get_or_404(session.get(CURR_USER_KEY))
    
    form = UserEditProfile(obj=user)
    
    if form.validate_on_submit():
        user_check = User.authenticate(form.username.data,
                                       form.password.data)

        if user_check:
            user.username = form.username.data
            user.email = form.email.data
            user.address = form.address.data
            db.session.commit()
            flash(f'User {user.username} updated', "success")
            return redirect(f'/users/{g.user.id}')
        else:
            flash(f'Incorrect Password. User {user.username} not updated', "warning")
            return redirect('/')

    return render_template('profile.html', form=form, user_id=g.user.id)


####     User DELETE             ######
@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    '''Delete user'''
    
    if CURR_USER_KEY not in session:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/")

##############################################################
#              routes for trails                             #
##############################################################

####     Trail Details            ######
@app.route('/users/<int:user_id>/trails/<int:trail_id>/', methods=['GET'])
def get_maproute(user_id, trail_id):
    '''Get a map route and return details'''
    user = User.query.get_or_404(user_id)
    print('##### trail_id: ', trail_id)
    trail = Trail.query.get_or_404(trail_id).to_coords_array()
    
    return (jsonify(maproute=trail))


####     Add Trail for User       ######
@app.route('/users/<int:user_id>/trails', methods=['POST'])
def add_maproute(user_id):
    '''Store a user map route'''
    sessionid = session.get(CURR_USER_KEY);
    print(f'***** sessionid: {sessionid}')
    
    name = request.json["name"]
    coords = request.json["coordinates"]
    distance = request.json["distance"]
    duration = request.json["duration"]
    
    
    
    newTrail = Trail(name=name,
                    distance=distance,
                    duration=duration,
                    coordinates=coords,
                    user_id=user_id)
    db.session.add(newTrail)
    db.session.commit()
    response = jsonify(maproute=newTrail.to_coords_array())

    return (response, 201)

    
####     Delete Trail              ######
@app.route('/users/<int:user_id>/trails/<int:trail_id>/delete', methods=['POST'])
def delete_maproute(user_id, trail_id):
    '''Delete a maproute'''
    trail = Trail.query.get_or_404(trail_id)
    db.session.delete(trail)
    db.session.commit()
    flash(f'{trail.name} is deleted', "warning")

    return redirect(f'/users/{user_id}')


# MAKE NOTES A LATER OPTION

##############################################################
#              routes for notes                              #
##############################################################

####     All Trail Notes            ######
@app.route('/users/<int:user_id>/trails/<int:trail_id>/notes', methods=['GET'])
def get_trail_notes(trail_id):
    '''Get all notes for a trail'''

    notes = Note.query.filter(Note.trail_id==trail_id).all()
    noteList = [{"id": note.id, 
                "comment": note.comment,
                "timestamp": note.timestamp,
                "trail_id": trail_id} for note in notes]
        
    return jsonify(noteList)
    

####     Add Note to Trail           ######
@app.route('/users/<int:user_id>/trails/<int:trail_id>/notes', methods=['POST'])
def add_trail_note(trail_id):
    '''Add a note to a trail'''
    comment = request.json['comment']
    note = Note(comment=comment, trail_id=trail_id)
    db.session.add(note)
    db.session.commit()
    response = jsonify(note={"id": note.id, "comment": note.comment,
                "timestamp": note.timestamp, "trail_id": note.trail_id})
    
    return (response, 201);


####     Delete Trail Note         ######
@app.route('/users/<int:user_id>/trails/<int:trail_id>/notes/<int:note_id>', methods=['DELETE'])
def delete_note(trail_id, note_id):
    '''Delete a note'''
    note = Note.query.filter(Note.id==note_id, Note.trail_id==trail_id).one_or_none()
    db.session.delete(note)
    db.session.commit()

    return jsonify(message="deleted")




    
