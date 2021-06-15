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
            name="test",
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
            

