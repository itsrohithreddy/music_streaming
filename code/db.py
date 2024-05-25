from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

current_dir=os.path.abspath(os.path.dirname(__file__))
app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///"+os.path.join(current_dir,"music.db")
db = SQLAlchemy()
db.init_app(app)
app.app_context().push()


class Albums(db.Model): #One (One : Album , Many : Songs)  
    album_id = db.Column(db.String, primary_key=True)
    album_name = db.Column(db.String(50), nullable=False,unique=True)
    album_owner_id = db.Column(db.String,db.ForeignKey('users.user_id'), nullable=False)
    album_image=db.Column(db.BLOB)
    songs_in = db.relationship('Songs',backref='album',lazy=True)



class Playlists(db.Model): #Many (Many :Playlists , Many : Songs)
    playlist_id = db.Column(db.String, primary_key=True)
    playlist_name = db.Column(db.String(50), nullable=False,unique=True)
    playlist_image=db.Column(db.BLOB)
    playlist_owner_id = db.Column(db.String,db.ForeignKey('users.user_id'), nullable=False)
    songs_in = db.relationship("Songs",secondary="playlist_songs",backref="song_playlists")


class Playlist_songs(db.Model):  #Secondary Table  (To biuld Many to Many Relationship between Playlists and Songs)
    song_id=db.Column(db.String,db.ForeignKey("songs.song_id"),primary_key=True,nullable=False)
    playlist_id=db.Column(db.String,db.ForeignKey("playlists.playlist_id"),primary_key=True,nullable=False)


    
class Songs(db.Model):  #Many
    song_id = db.Column(db.String, primary_key=True)
    song_name = db.Column(db.String(50), nullable=False,unique=True)
    song_file = db.Column(db.BLOB,nullable=False)
    song_lyrics=db.Column(db.String,nullable=False)
    album_id = db.Column(db.String, db.ForeignKey('albums.album_id'),nullable=False)
    duration=db.Column(db.Integer,server_default=db.text('0'))
    song_views=db.Column(db.Integer,nullable=False,server_default=db.text('0'))
    genre=db.Column(db.String(50))
    liked=db.Column(db.Integer,nullable=False,server_default=db.text('0'))

class Users(db.Model):
    user_id = db.Column(db.String,primary_key = True)
    user_name = db.Column(db.String(50),nullable=False,unique=True)
    first_name= db.Column(db.String(50),nullable=False)
    last_name = db.Column(db.String(50))
    age = db.Column(db.Integer)
    role = db.Column(db.String(50),nullable=False)
    user_image_url = db.Column(db.String)
    password = db.Column(db.String)


class User_likes_ratings(db.Model):
    user_id=db.Column(db.String,db.ForeignKey('users.user_id'),primary_key = True,nullable=False)
    song_id=db.Column(db.String,db.ForeignKey('songs.song_id'),primary_key=True,nullable=False)
    song_liked=db.Column(db.Integer,server_default=db.text('0'))
    song_rating=db.Column(db.Float,server_default=db.text('0'))

db.create_all()