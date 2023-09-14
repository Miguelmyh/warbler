import os

from unittest import TestCase
from models import db, connect_db, Message, User
from forms import UserEditForm

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False

class UserViewsTestCase(TestCase):
    def setUp(self):
        db.session.rollback()
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
        
    def test_list_users(self):
        """Tests that list of all users are returned"""
        new_user = User.signup(username="abbytest",
                                    email="test1@test.com",
                                    password="testuser",
                                    image_url=None)
        db.session.commit()
        
        with self.client as client:
            
            resp = client.get('/users')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(self.testuser.username, html)
            #check for specific q value
            
            q_resp = client.get('/users', query_string={'q': 'a'})
            q_html = q_resp.get_data(as_text=True)
            
            self.assertNotIn(self.testuser.username,q_html)
            self.assertIn(new_user.username,q_html)
            
    def test_users_show(self):
        """Test user details being shown"""
        with self.client as client:
            resp = client.get(f'/users/{self.testuser.id}')
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn(self.message.text, html)
            
    def test_show_following(self):
        """Test show_following route"""
        with self.client as client:
            #not logged in
            resp = client.get(f'/users/{self.testuser.id}/following', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)
            #logged in
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser.id
              
            new_user = User.signup(username="abbytest",
                                email="test1@test.com",
                                password="testuser",
                                image_url=None)
            db.session.commit() 
            self.testuser.following.append(new_user)
                
            log_resp = client.get(f'/users/{self.testuser.id}/following')
            log_html = log_resp.get_data(as_text=True)
            
            self.assertEqual(log_resp.status_code, 200)
            self.assertIn(self.testuser.username, log_html)
            self.assertIn(new_user.username, log_html)
            
    def test_users_followers(self):
        """test users_followers route"""
        with self.client as client:
            resp = client.get(f'/users/{self.testuser.id}/followers', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.request.path, '/')
            self.assertIn('Access unauthorized.', html)
            
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser.id
                
            new_user = User.signup(username="abbytest",
                    email="test1@test.com",
                    password="testuser",
                    image_url=None)
            db.session.commit() 
            
            self.testuser.followers.append(new_user)    
            db.session.commit()
            log_resp = client.get(f'/users/{self.testuser.id}/followers')
            log_html = log_resp.get_data(as_text=True)    
            
            self.assertEqual(log_resp.status_code, 200)
            self.assertEqual(len(self.testuser.followers), 1)
            self.assertIn(new_user.username, log_html)
            
    def test_add_follow(self):
        """test should add a follow when g.user"""
        new_user = User.signup(username="abbytest",
                email="test1@test.com",
                password="testuser",
                image_url=None)
        db.session.commit() 
        
        with self.client as client:
            resp = client.post(f'/users/follow/{new_user.id}', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.request.path, '/')
            with client.session_transaction() as session:
                     session[CURR_USER_KEY] = self.testuser.id
            log_resp = client.post(f'/users/follow/{new_user.id}', follow_redirects=True)
            html = log_resp.get_data(as_text=True) 
            
            self.assertEqual(log_resp.status_code, 200)
            self.assertEqual(log_resp.request.path, f'/users/{self.testuser.id}/following')
            self.assertIn(self.testuser.following[0].username, html)
    
    def test_stop_following(self):
        """Test that logged in user stops following other user."""
        new_user = User.signup(username="abbytest",
                email="test1@test.com",
                password="testuser",
                image_url=None)
        db.session.commit() 
        with self.client as client:
            resp = client.post(f'/users/stop-following/{new_user.id}', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.request.path, '/')
            
            with client.session_transaction() as session:
                session[CURR_USER_KEY] =self.testuser.id
                
            #add user to following list to then check if it was removed
            self.testuser.following.append(new_user)
            db.session.commit()
            
            log_resp = client.post(f'/users/stop-following/{new_user.id}', follow_redirects=True)
            log_html = log_resp.get_data(as_text=True)
            
            self.assertEqual(log_resp.status_code, 200)
            self.assertEqual(log_resp.request.path, f'/users/{self.testuser.id}/following')
            self.assertNotIn(new_user.username, log_html)
            
    def test_user_profile(self):
        """Test for updating and showing user profile"""
        form = UserEditForm(obj = self.testuser)
        with self.client as client:
            resp = client.get('/users/profile', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.request.path, '/')
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser.id
            #logged user should get form page
            log_resp = client.get('/users/profile')
            log_html = log_resp.get_data(as_text=True)
            self.assertIn(self.testuser.username, log_html)
            self.assertIn(form.username.data, log_html)
            #logged user should post and be redirected
            post_resp = client.post('/users/profile', data={'username': self.testuser.username, 
                                                            'email': self.testuser.email,
                                                            'image_url': None,
                                                            'header_image_url':None,
                                                            'bio': 'This is my bio',
                                                            'location': 'Arizona', 
                                                            'password': 'testuser'}, follow_redirects=True)
            post_html = post_resp.get_data(as_text=True)
            self.assertEqual(post_resp.status_code,200)
            self.assertIn(self.testuser.bio, post_html)
            self.assertEqual(post_resp.request.path,f'/users/{self.testuser.id}')
            
    def test_delete_user(self):
        """Test for owner to delete account"""
        with self.client as client:
            resp = client.post('/users/delete', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.request.path, '/')
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser.id
            
            log_resp = client.post('/users/delete', follow_redirects=True)
            # log_html = log_resp.get_data(as_text=True)
            user = User.query.filter(User.id == self.testuser.id).first()
            
            self.assertEqual(log_resp.status_code, 200)
            self.assertEqual(log_resp.request.path, '/signup')
            self.assertEqual(user, None)

            
            
            