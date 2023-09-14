import os
from datetime import datetime
from unittest import TestCase
from models import db,User,Message

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

app.config['TESTING'] = True

db.drop_all()
db.create_all()

class TestMessageModelTestCase(TestCase):
    """Test message model"""
    
    def setUp(self):
        User.query.delete()
        Message.query.delete()
        
        self.user_test = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        db.session.add(self.user_test)
        db.session.commit()
        self.message = Message(text = 'Hello', user_id = self.user_test.id)
        db.session.add(self.message)
        db.session.commit()
    
    def tearDown(self):
        db.session.rollback()
        
    def test_message_barebone(self):
        """Tests for ids to exist and be of type integer"""
        self.assertIsInstance(self.message.id, int)
        self.assertEqual(self.message.user_id, self.user_test.id)
        self.assertNotEqual(self.message.timestamp, datetime.utcnow())
        
    def test_message_delete(self):
        """tests a message deletion of the db"""
        Message.query.filter(Message.id == self.message.id).delete()
        db.session.commit()
        
        self.assertEqual(Message.query.filter(Message.id == self.message.id).first(), None)
        
        