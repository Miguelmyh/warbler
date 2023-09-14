"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.user_test = User(
            email="test1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD"
        )
        db.session.add(self.user_test)
        db.session.commit()
        
        self.client = app.test_client()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
################################################################
#followings/likes
        
        
    def test_user_followers(self):
        """Adds user to followers list and tests is_followed_by function"""
        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        
        db.session.add(u)
        db.session.commit()
        
        u.followers.append(self.user_test)
        db.session.commit()
        
        follow = Follows.query.filter(Follows.user_being_followed_id == u.id).first()
        
        self.assertIsInstance(u.followers[0], object)
        self.assertEqual(u.is_followed_by(self.user_test), True)
        self.assertEqual(follow.user_following_id, self.user_test.id)
        
    def test_user_following(self):
        """Adds user to following list and tests is_following function"""
        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        
        db.session.add(u)
        db.session.commit()
        
        u.following.append(self.user_test)
        db.session.commit()
    
        follow = Follows.query.filter(Follows.user_following_id == u.id).first()
        
        self.assertIsInstance(u.following[0], object)
        self.assertEqual(u.is_following(self.user_test), True)
        self.assertEqual(follow.user_being_followed_id, self.user_test.id)

    def test_user_likes(self):
        """Test user.likes"""
        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        
        db.session.add(u)
        db.session.commit()
        message = Message(text = "test message", user_id = u.id)
        db.session.add(message)
        db.session.commit()
        
        u.likes.append(message)
        db.session.commit()
        
        like = Likes.query.filter(Likes.message_id == u.likes[0].id).first()
        
        self.assertEqual(len(u.likes), 1)
        self.assertEqual(u.likes[0], message)
        #will check for Likes model being updated
        #if .first() found no value returns None
        self.assertNotEqual(like, None)
        
    def test_repr_(self):
        """Test user repr function"""
        self.assertEqual(str(self.user_test), f"<User #{self.user_test.id}: testuser1, test1@test.com>")
########################################################################\
#signup and authenticate tests        
    def test_user_signup(self):
        """Test for signup functionality(encrypted password)"""
        u = User.signup(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url= User.image_url.default.arg
        )
        db.session.commit()
        
        #check for password change
        self.assertNotEqual(u.password, "HASHED_PASSWORD")
        self.assertEqual(u.password, User.authenticate(u.username, "HASHED_PASSWORD").password)
        
    def test_user_authenticate(self):
        """Test user authentication"""
        u = User.signup(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url= User.image_url.default.arg
        )
        db.session.commit()
        #authenticate must return user if valid else False
        self.assertEqual(User.authenticate(u.username, "HASHED_PASSWORD"), u)
        self.assertNotEqual(User.authenticate(u.username, "HasHeD-test"), u)
        self.assertNotEqual(User.authenticate("tesuser", u.password), u)
        
    