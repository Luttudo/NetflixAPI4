from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    synopsis = db.Column(db.String(500), nullable=False)
    cast = db.Column(db.String(200), nullable=False)
    director = db.Column(db.String(100), nullable=False)
    average_rating = db.Column(db.Float, nullable=False)

#Playlists

class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tracks = db.relationship('PlaylistTrack', backref='playlist', lazy=True)

class PlaylistTrack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id'), nullable=False)
    content_id = db.Column(db.Integer, db.ForeignKey('content.id'), nullable=False)
    position = db.Column(db.Integer, nullable=False)


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'message': 'Invalid JSON data'}), 400

    hashed_password = generate_password_hash(data['password'], method='sha256')
    new_user = User(username=data['username'], email=data['email'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Registered successfully'}), 201



@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'message': 'Invalid JSON data'}), 400

    user = User.query.filter_by(username=data['username']).first_or_404()
    if not check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Login Unsuccessful'}), 401

    return jsonify({'message': 'Login Successful'}), 200

@app.route('/content', methods=['GET'])
def get_content():
    content = Content.query.all()
    return jsonify([{'title': c.title, 'synopsis': c.synopsis, 'cast': c.cast, 'director': c.director, 'average_rating': c.average_rating} for c in content]), 200


# Visualização de detalhes -=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=-
@app.route('/content/<id>', methods=['GET'])
def get_content_details(id):
    content = Content.query.get_or_404(id)
    return jsonify({'title': content.title, 'synopsis': content.synopsis, 'cast': content.cast, 'director': content.director, 'average_rating': content.average_rating}), 200

#Tabela armazena o hsitorico de views  -=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=-
class ViewingHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content_id = db.Column(db.Integer, db.ForeignKey('content.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


#Reproduzir os videos e registrar que foi reproduzido -=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=-
@app.route('/content/<id>/play', methods=['POST'])
def play_content(id):
    content = Content.query.get_or_404(id)
    # Aqui você pode adicionar código para registrar que o usuário assistiu este conteúdo
    history = ViewingHistory(user_id=current_user.id, content_id=content.id)
    db.session.add(history)
    db.session.commit()

    return jsonify({'message': 'Playing ' + content.title}), 200

#Busca de conteúdo e filtros -=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=-
@app.route('/search', methods=['GET'])
def search_content():
    query = request.args.get('query')
    genre = request.args.get('genre')
    year = request.args.get('year')
    rating = request.args.get('rating')

    content_query = Content.query

    if query:
        content_query = content_query.filter(Content.title.contains(query))
    if genre:
        content_query = content_query.filter(Content.genre == genre)
    if year:
        content_query = content_query.filter(Content.year == year)
    if rating:
        content_query = content_query.filter(Content.average_rating >= rating)

    content = content_query.all()

    return jsonify([{'title': c.title, 'synopsis': c.synopsis, 'cast': c.cast, 'director': c.director, 'average_rating': c.average_rating} for c in content]), 200

#Criar e editar listas de reprodução -=--=--=--=--=--=--=
@app.route('/playlists', methods=['GET'])
def get_playlists():
    playlists = Playlist.query.filter_by(user_id=current_user.id).all()
    return jsonify([{'id': p.id, 'name': p.name, 'created_at': p.created_at} for p in playlists]), 200

@app.route('/playlists', methods=['POST'])
def create_playlist():
    data = request.get_json()
    playlist = Playlist(name=data['name'], user_id=current_user.id)
    db.session.add(playlist)
    db.session.commit()
    return jsonify({'message': 'Playlist created successfully', 'id': playlist.id}), 201

@app.route('/playlists/<playlist_id>/tracks', methods=['POST'])
def add_track_to_playlist(playlist_id):
    data = request.get_json()
    playlist = Playlist.query.get(playlist_id)
    if not playlist:
        return jsonify({'message': 'Playlist not found'}), 404

    content_id = data['content_id']
    position = data['position']

    playlist_track = PlaylistTrack(playlist_id=playlist.id, content_id=content_id, position=position)
    db.session.add(playlist_track)
    db.session.commit()

    return jsonify({'message': 'Track added to playlist successfully'}), 200

@app.route('/playlists/<playlist_id>/tracks/<track_id>', methods=['DELETE'])
def remove_track_from_playlist(playlist_id, track_id):
    playlist = Playlist.query.get(playlist_id)
    if not playlist:
        return jsonify({'message': 'Playlist not found'}), 404

    playlist_track = PlaylistTrack.query.filter_by(playlist_id=playlist.id, content_id=track_id).first()
    if not playlist_track:
        return jsonify({'message': 'Track not found in playlist'}), 404

    db.session.delete(playlist_track)
    db.session.commit()

    return jsonify({'message': 'Track removed from playlist successfully'}), 200


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
