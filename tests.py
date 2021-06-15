from unittest import TestCase

from app import app
from models import db, User, Trail

# Use test database and don't clutter tests with SQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///urbanmaps_test_db'
app.config['SQLALCHEMY_ECHO'] = False

# Make Flask errors be real errors, rather than HTML pages with error info
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

db.drop_all()
db.create_all()

NEW_USER2 = {
    "username": "testuser2",
    "password": "password",
    "email": "testuser2@test.com",
    "address": "A test street address 95952"
}


class UrbanTrailsViewsTest(TestCase):
    '''Tests for views of APIs'''

    def setUp(self):
        """Make demo data."""

        User.query.delete()
        Trail.query.delete()

        user1 = User(
            username="testuser",
            password="password",
            email="testuser@test.com",
            address="A test street address 95951"
        )
        db.session.add(user1)
        db.session.commit()

        trail1 = Trail(
            name="testtrail",
            distance=3.5,
            duration=35.4,
            coordinates=[[-121, 36.5], [-122, 37]],
            user_id=user1.id
        )
        db.session.add(trail1)
        db.session.commit()

        print(f'**** user: {user1.id}')
        self.user1 = user1
        self.trail1 = trail1

    def tearDown(self):
        """Clean up fouled transactions."""

        db.session.rollback()

    
    def testDefaultRoute(self):
        with app.test_client() as client:
            resp = client.get("/")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="col-md-5">', html)
    
    def testRegisterRoute(self):
        with app.test_client() as client:
            resp = client.post("/users/register", data=NEW_USER2)
            html = resp.get_data(as_text=True)
                        
            self.assertEqual(User.query.count(), 2)
            self.assertEqual(resp.location, "http://localhost/")
            self.assertEqual(resp.status_code, 302)

            # test login for newly loggedin user
            resp = client.post("/users/login", data=
            {"username":"testuser2", "password": "password"},
            follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Hello, testuser2!', html)

            # test logout
            resp = client.get("users/logout", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('You have been logged out, Thanks for visiting!', html)

    def testGetUserPage(self):
        with app.test_client() as client:
            resp = client.get(f"/users/{self.user1.id}")
            html = resp.get_data(as_text=True)
    
            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'Welcome {self.user1.username}', html)

    def testUpdateUserProfile(self):
        with app.test_client() as client:
            # Register a new user and login
            resp = client.post("/users/register", data=NEW_USER2)
            resp = client.post("/users/login", data=
            {"username":"testuser2", "password": "password"},
            follow_redirects=True)
                        
            # Now call /users/profile route
            resp = client.post(f"/users/profile",data=
            {"username":"testuser2", "password": "password", "email": "newmail@mail.com", "address": "New Address"},
            follow_redirects=True)
            html = resp.get_data(as_text=True)
            user = User.query.filter_by(username='testuser2').first()
                
            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'Welcome {user.username}', html)
            self.assertEqual('newmail@mail.com',user.email)

    def testDeleteUser(self):
        with app.test_client() as client:
            # Register a new user and login
            resp = client.post("/users/register", data=NEW_USER2)
            resp = client.post("/users/login", data=
            {"username":"testuser2", "password": "password"},
            follow_redirects=True)
    
            self.assertEqual(User.query.count(), 2)
            # Get logged in user id 
            user2 = User.query.filter_by(username='testuser2').first()      
            # Now call /users/profile route
            resp = client.delete(f"/users/{user2.id}", follow_redirects=True)

            self.assertEqual(User.query.count(), 1)
            self.assertEqual(resp.status_code, 200)

    def testAddDeleteTrail(self):
        with app.test_client() as client:
            # Register a new user and login
            resp = client.post("/users/register", data=NEW_USER2)
            resp = client.post("/users/login", data=
            {"username":"testuser2", "password": "password"},
            follow_redirects=True)
            user2 = User.query.filter_by(username='testuser2').first()
            
            # Test Add trail
            resp = client.post(f'/users/{user2.id}/trails', json = {
                "name": "testtrail2",
                "distance": 4.5,
                "duration": 35.4,
                "coordinates": [[-121, 36.5], [-122, 37]],
                "user_id": user2.id
            })  

            self.assertEqual(resp.status_code, 201)
            self.assertEqual(Trail.query.count(), 2)
            
            # Test Delete Trail
            trail2 = Trail.query.filter_by(name='testtrail2').first()
            resp = client.post(f'/users/{user2.id}/trails/{trail2.id}/delete')

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(Trail.query.count(), 1)
            

