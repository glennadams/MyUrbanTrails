from models import db, connect_db, User, Trail, Note
from app import app

db.drop_all()
db.create_all()

user1 = User(username='demoname', password='password', address = '29 Wellbeing circle, Carmel Valley, CA')
db.session.add(user1)
db.session.commit()

map1 = Trail(name='Demo Map', distance=3.5,
                                duration=35.4,
                                coordinates=[[-121.603451,36.704384],
                                            [-121.604256,36.704232],
                                            [-121.605525,36.703853]],
                                user_id=1)


db.session.add(map1)
db.session.commit()

note1 = Note(comment='Really awesome route', trail_id=1)

db.session.add(note1)
db.session.commit()