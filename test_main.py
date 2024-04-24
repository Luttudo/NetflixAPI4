import unittest
from flask import Flask
from flask_testing import TestCase
from main import app, db, User, Content, Playlist, PlaylistTrack

class YourAppTestCase(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_register(self):
        response = self.client.post('/register', json={'username': 'testuser', 'email': 'test@example.com', 'password': 'testpass'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['message'], 'Registered successfully')

        user = User.query.filter_by(username='testuser').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'test@example.com')

    def test_login(self):
        user = User(username='testuser', email='test@example.com', password='testpass')
        db.session.add(user)
        db.session.commit()

        response = self.client.post('/login', json={'username': 'testuser', 'password': 'testpass'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'Login Successful')

    # Adicione outros testes para as outras rotas e funcionalidades

if __name__ == '__main__':
    unittest.main()
