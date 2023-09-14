"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()
        self.message = Message(text="Hello", user_id = self.testuser.id)
        db.session.add(self.message)
        db.session.commit()
        
    
    def tearDown(self):
        db.session.rollback()
        Message.query.delete()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            html = resp.get_data(as_text=True)
            # Make sure it redirects
            #no login, resp should be redirected to homepage
            #and has flashed message
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.request.path, "/")
            self.assertIn("Access unauthorized.", html)
            
            #login
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Helloo"})
            get_resp = c.get("/messages/new")
            

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(get_resp.status_code, 200)
            
            msg = Message.query.all()[-1]
            self.assertEqual(msg.text, "Helloo")
    
    def test_message_detail(self):
        """Should get certain message and show it's details"""
        with self.client as c:
            
            #logged in or not logged in should bring same result
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
        
            resp = c.get(f"/messages/{self.message.id}")
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Hello', html)
            
    def test_message_delete(self):
        """Delete Message if logged user is owner of the message"""
        with self.client as client:
            #no login
            resp = client.post(f'/messages/{self.message.id}/delete')
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, '/', resp.location)#location checks url after redirect
            
            redirected_resp = client.post(f'/messages/{self.message.id}/delete', follow_redirects=True)
            html = redirected_resp.get_data(as_text=True)
            self.assertEqual(redirected_resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)
            #logged in
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser.id
                
            message = Message.query.get(self.message.id)
                
            log_resp = client.post(f'/messages/{message.id}/delete', follow_redirects=True)
            log_html = log_resp.get_data(as_text=True)
            self.assertEqual(log_resp.status_code, 200, self.message.id)
            self.assertEqual(log_resp.request.path, f"/users/{self.testuser.id}")
            self.assertNotIn(self.message.text, log_html, self.message.text)
            
    
            
            
            
            
                
            
