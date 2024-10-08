import os
import uuid
import json
import jwt
import base64
from datetime import datetime, timedelta, timezone
from flask import Flask , session
from flask import request
from flask import url_for
from flask import make_response,redirect
from flask import render_template
from flask import jsonify
from functools import wraps
from PIL import Image

from flask_sqlalchemy import SQLAlchemy
from io import BytesIO

from authlib.integrations.flask_client import OAuth


from flask import g
import secrets

current_dir=os.path.abspath(os.path.dirname(__file__))
app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///"+os.path.join(current_dir,"music.db")
db = SQLAlchemy()
db.init_app(app)


with open('C:\ONE DRIVE ROHITH\OneDrive\Documents\music_streaming\code\paths.json') as config_file3:
    paths = json.load(config_file3)


with open(paths['secret']) as config_file2:
     secrets_ = json.load(config_file2)
app.config['SECRET_KEY'] = secrets_['jwtwebtoken_secret']   #For JWT Token and Flask session signing



# app.app_context().push()




#OAuth
with open(paths["OAuth"]) as config_file:
    config = json.load(config_file)

oauth = OAuth(app)
google = oauth.register(
    'google',
    client_id=config['web']['client_id'],
    client_secret=config['web']['client_secret'],
    access_token_url=config['web']['token_uri'],
    authorize_url=config['web']['auth_uri'],
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'email profile'},
)



# print(dir(oauth))




def gen_uuid():
    return str(uuid.uuid4())


               
def decodeutf8(value):
    decoded_value = value.decode('utf-8')
    return decoded_value
app.jinja_env.filters['decodeutf8'] = decodeutf8




def generate_csrf_token():
    session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']

@app.context_processor
def inject_csrf_token():
    return {'csrf_token': generate_csrf_token()}




class Albums(db.Model): #One (One : Album , Many : Songs)
    __tablename__="albums"    
    album_id = db.Column(db.String, primary_key=True)
    album_name = db.Column(db.String(50), nullable=False,unique=True)
    album_owner_id = db.Column(db.String,db.ForeignKey('users.user_id'), nullable=False)
    album_image=db.Column(db.BLOB)
    songs_in = db.relationship('Songs',backref='album',lazy=True)



class Playlists(db.Model): #Many (Many :Playlists , Many : Somgs)
    __tablename__="playlists"
    playlist_id = db.Column(db.String, primary_key=True)
    playlist_name = db.Column(db.String(50), nullable=False,unique=True)
    playlist_image=db.Column(db.BLOB)
    playlist_owner_id = db.Column(db.String,db.ForeignKey('users.user_id'), nullable=False)
    songs_in = db.relationship("Songs",secondary="playlist_songs",backref="song_playlists")


class Playlist_songs(db.Model):  #Secondary Table  (To biuld Many to Many Relationship between Playlists and Songs)
    __tablename__="playlist_songs"
    song_id=db.Column(db.String,db.ForeignKey("songs.song_id"),primary_key=True,nullable=False)
    playlist_id=db.Column(db.String,db.ForeignKey("playlists.playlist_id"),primary_key=True,nullable=False)


    
class Songs(db.Model):  #Many
    __tablename__="songs"
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
    __tablename__="users"
    user_id = db.Column(db.String,primary_key = True)
    user_name = db.Column(db.String(50),nullable=False,unique=True)
    first_name = db.Column(db.String(50),nullable=False)
    last_name = db.Column(db.String(50))
    age = db.Column(db.Integer)
    user_image_url = db.Column(db.String)
    role= db.Column(db.String(50),nullable=False)
    password = db.Column(db.String)


class User_likes_ratings(db.Model):
    __tablename__="user_likes_ratings"
    user_id=db.Column(db.String,db.ForeignKey('users.user_id'),primary_key = True,nullable=False)
    song_id=db.Column(db.String,db.ForeignKey('songs.song_id'),primary_key=True,nullable=False)
    song_liked=db.Column(db.Integer,server_default=db.text('0'))
    song_rating=db.Column(db.Float,server_default=db.text('0'))





with open(paths['admin']) as config_file1:
    admin_dict = json.load(config_file1)




#Custom decorator
def check_loggedIn_jwt_expiration(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('token')

        if not token:
            # If no token is found, redirect or return an error response
            return jsonify({"message": "Token is missing!"}), 403

        try:
            # Simply trying to Decode the token is enough here
            # If the token expires then bolow line throws exception `jwt.ExpiredSignatureError` 
            decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            return f(*args, **kwargs)
            # elif decoded_token.get("loggedIn") == 0:
            #     # If not logged in return a message useful in case of api calls
            #     return jsonify({"message": "Unauthorized user!!!!"}), 401
                

        except jwt.ExpiredSignatureError:
            # If token has expired (based on 'exp' claim)
            # print("Expired and changed...................")
            inject_csrf_token()
            # print("CSRF Token : ",session.get('csrf_token'))
            session.pop('google_token', None)
            response = make_response(redirect("/"))
            response.set_cookie('token', '',expires=0)  # Clear the token cookie
            return response
            # return jsonify({"message": "Token has expired!"}), 401

        except jwt.InvalidTokenError:
            # If the token is invalid
            return jsonify({"message": "Invalid token!"}), 403

    return decorated_function



# Custom CSRF protection decorator
def csrf_protect(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        csrf_token = request.headers.get('X-CSRF-Token')
        
        if not csrf_token or csrf_token != session.get('csrf_token'):
            abort(403, description="Invalid or missing CSRF token")
        # print("CSRF Token : ",session.get('csrf_token'))
        # print("checked")
        return f(*args, **kwargs)
    
    return decorated_function




@app.route('/',methods=['GET'])
@app.route('/index',methods=['GET'])
def home():
    # print(request.cookies)
    if request.cookies.get('token')  is None:
        token_payload = {
            'username':"",
            'name': "",
            'role': "",
            'loggedIn':"0",
            'pic_url':"",
            'admin' : "0",
            'admin_u' : "",
        }
        token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')
        response = make_response(redirect("/"))
        response.set_cookie("token",token)
        return response
    top_rated_song_ids = db.session.query(User_likes_ratings.song_id,db.func.avg(User_likes_ratings.song_rating).label('average_rating')).group_by(User_likes_ratings.song_id).order_by(db.desc('average_rating')).limit(5).all()
    top_rated_songs=[]
    for top_rated_song_id in top_rated_song_ids:
        top_rated_songs.append(Songs.query.filter(Songs.song_id == top_rated_song_id.song_id).first())
    albums=Albums.query.all()
    # print(albums)
    playlist_url=url_for("playlist_songs",playlist_name="")
    album_url=url_for("album_songs",album_name="")
    # print("Token : ",request.cookies.get('token'))
    decoded_token = jwt.decode(request.cookies.get('token'), app.config['SECRET_KEY'], algorithms=['HS256'])
    if decoded_token.get("loggedIn")=="1":
        user_id=Users.query.filter(Users.user_name == decoded_token.get("username")).first().user_id
        playlists=Playlists.query.filter(Playlists.playlist_owner_id == user_id).all()
        return render_template('index.html',top_rated_songs=top_rated_songs,playlists=playlists,nav_username=decoded_token.get("name"),loggedIn_status=decoded_token.get("loggedIn"),profilePic_url=decoded_token.get('pic_url'),playlist_url=playlist_url,album_url=album_url,albums=albums)
    return render_template('index.html',top_rated_songs=top_rated_songs,nav_username=decoded_token.get("name"),loggedIn_status=decoded_token.get("loggedIn"),profilePic_url=decoded_token.get('pic_url'),playlist_url=playlist_url,album_url=album_url,albums=albums)







@app.route('/signin')
def login():
    # print(dir(google) )
    redirect_uri = url_for('authorized', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/logout')
@check_loggedIn_jwt_expiration
def logout():
    inject_csrf_token()
    session.pop('google_token', None)
    decoded_token = jwt.decode(request.cookies.get('token'), app.config['SECRET_KEY'], algorithms=['HS256'])
    decoded_token["loggedIn"] = "0"
    decoded_token["username"] = ""
    decoded_token["name"] = ""
    decoded_token["pic_url"] = ""
    decoded_token['role']= ""
    decoded_token['admin']= "0"
    decoded_token['admin_u'] = ""
    decoded_token.pop('exp')
    new_token = jwt.encode(decoded_token, app.config['SECRET_KEY'], algorithm='HS256')
    response = make_response(redirect("/"))
    response.set_cookie("token",new_token)
    return response

@app.route('/signin/callback')
def authorized():
    resp = google.authorize_access_token()
    # print("Response : ",resp)
    if resp is None or resp.get('access_token') is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    session['google_token'] = (resp['access_token'],'')
    # print(session['google_token'])
    # print("Session : ",session)
    # print("Token Getter : ",google.tokengetter)
    user_info = google.get('userinfo')
    # print("User Info : ",user_info)
    user_data = user_info.json()  # Use .json() to get the data as a dictionary
    # print('Logged in with id :  ' , user_data.get('email')," Name : ",user_data.get('name') , " Given name : ",user_data.get('given_name'), " Family Name : ",user_data.get('family_name'), " Picture : ",user_data.get('picture'))
    username_mailid = user_data.get('email')
    first_name = user_data.get('given_name')
    last_name = user_data.get('family_name')
    name = user_data.get('name')
    picture = user_data.get('picture')
    user_check=Users.query.filter(Users.user_name == username_mailid).first()
    inject_csrf_token()
    if user_check:
        try:
            user_check.user_name = username_mailid
            user_check.first_name = first_name
            user_check.last_name = last_name
            user_check.user_image_url = picture
        
            db.session.commit()
        except:
            print("Rolling Back")
            db.session.rollback()
        decoded_token = jwt.decode(request.cookies.get('token'), app.config['SECRET_KEY'], algorithms=['HS256'])
        decoded_token["loggedIn"] = "1"
        decoded_token["username"] = username_mailid
        decoded_token["name"] = name
        decoded_token["pic_url"] = picture
        if user_check.role == "creator":
            decoded_token["role"] = "creator"
        else:
            decoded_token["role"] = "user"
        decoded_token["exp"] = datetime.now(timezone.utc) + timedelta(hours=1)
        new_token = jwt.encode(decoded_token, app.config['SECRET_KEY'], algorithm='HS256')
        response = make_response(redirect("/"))
        response.set_cookie("token",new_token)
        return response
    else:
        with app.app_context():
            try:
                new_user=Users(user_id=gen_uuid(),user_name=username_mailid,role="user",first_name=first_name,last_name=last_name,user_image_url=picture)
                db.session.add(new_user)
                db.session.commit()
            except:
                print("Rolling back")
                db.session.rollback()
        decoded_token = jwt.decode(request.cookies.get('token'), app.config['SECRET_KEY'], algorithms=['HS256'])
        decoded_token["loggedIn"] = "1"
        decoded_token["username"] = username_mailid
        decoded_token["name"] = name
        decoded_token["role"] = "user"
        decoded_token["pic_url"] = picture
        decoded_token["exp"] = datetime.now(timezone.utc) + timedelta(hours=1)
        new_token = jwt.encode(decoded_token, app.config['SECRET_KEY'], algorithm='HS256')
        response = make_response(redirect("/"))
        response.set_cookie("token",new_token)
        return response




# @app.route("/register", methods=['POST'])
# def register():
#     if request.method == "POST":
        
#         username_mailid=request.form['email']
#         password=request.form['enterPassword']
        
#         with app.app_context():
#             try:
#                 new_user=Users(user_id=gen_uuid(),user_name=username_mailid,role="user",password=generate_password_hash(password,method='pbkdf2:sha256'))
#                 db.session.add(new_user)
#                 db.session.commit()
#             except:
#                 db.session.rollback()
#         return f"""<html>
#                     <head>
#                         <meta http-equiv="refresh" content="3;url=/signin" />
#                     </head>
#                     <body>
#                         <h3> Registered {username_mailid} hopefully.... </h3>
#                         <h1>Redirecting you to login page in 3 seconds . Please login now . </h1>
#                     </body>
#                     </html>"""





# @app.route("/signin", methods=['POST', 'GET'])
# def signin():
#     if request.method == "GET":
#         if request.cookies.get("loggedIn") == "1":
#             return redirect("/")
#         return render_template("signin.html")
#     if request.method == "POST":
#         # print("Hi")
#         username = request.form['username']
#         password = request.form['password']
#         user_exists=Users.query.filter(Users.user_name == username).first()
#         if user_exists:
#             user_password=user_exists.password
#             user_role=user_exists.role
#             if check_password_hash(user_password,password):
#                 response = make_response(redirect("/"))
#                 response.set_cookie("loggedIn", "1")
#                 response.set_cookie("username", username)
#                 if user_role == "creator":
#                     response.set_cookie("role", "creator")
#                 else:
#                     response.set_cookie("role", "user")

#                 return response
#             else:
#                 return f"""<html>
#                         <head>
#                             <meta http-equiv="refresh" content="3;url=/signin" />
#                         </head>
#                         <body>
#                             <h2> <span style="color:crimson;text-align:center;">Password Incorect !! </span></h2>
#                             <h4><span style="color:crimson;text-align:center;"> Redirecting you to same login page in 3 seconds . Please Retry . </span></h4>
#                         </body>
#                         </html>"""
#         else:
#             return f"""<html>
#                         <head>
#                             <meta http-equiv="refresh" content="3;url=/signin" />
#                         </head>
#                         <body>
#                             <h2> <span style="color:crimson;text-align:center;">No user found !! Please Register first . </span></h2>
#                             <h4><span style="color:crimson;text-align:center;"> Redirecting you to login page in 3 seconds . Please click on <strong>Register here</strong></span></h4>
#                         </body>
#                         </html>"""
        




# @app.route("/logout", methods=['GET'])
# def logout():
#     response = make_response(redirect("/"))
#     response.set_cookie("loggedIn", "0")
#     response.set_cookie("role", "none")
#     response.set_cookie("username", "None")
#     return response




@app.route('/create',methods=['GET','POST'])
@check_loggedIn_jwt_expiration
def create(user_song_count=0):
    decoded_token = jwt.decode(request.cookies.get('token'), app.config['SECRET_KEY'], algorithms=['HS256'])
    if decoded_token.get("loggedIn") == "1" and decoded_token.get("role") == "creator":
        
        user_id=Users.query.filter(Users.user_name == decoded_token.get("username")).first().user_id
        user_albums=Albums.query.filter(Albums.album_owner_id == user_id).all()
        user_album_count=len(user_albums)

        for user_album in user_albums:
            user_song_count+=Songs.query.filter_by(album_id=user_album.album_id).count()
        
        return render_template('create.html',nav_username=decoded_token.get("name"),username=decoded_token.get("username"),profilePic_url=decoded_token.get('pic_url'),albums=user_albums,user_album_count=user_album_count,user_song_count=user_song_count)
    elif decoded_token.get("loggedIn") == "1" and decoded_token.get("role") == "user":
        if request.method == 'GET':
            return render_template('before_create.html',nav_username=decoded_token.get("name"),profilePic_url=decoded_token.get('pic_url'))
        elif request.method == 'POST':
            # print("YES")
            username=decoded_token.get("username")
            # user_exists=Users.query.filter(Users.user_name == username).first()
            # print(user_exists.role)
            with app.app_context():
                try:
                    user_exists=Users.query.filter(Users.user_name == username).first()
                    user_exists.role="creator"
                    # print("Inside TRY")
                    db.session.commit()
                    decoded_token["role"]="creator"
                    new_token = jwt.encode(decoded_token, app.config['SECRET_KEY'], algorithm='HS256')
                    response = make_response(redirect("/create"))
                    response.set_cookie("token",new_token)
                    # print(request.cookies.get("role"),request.cookies.get("username"),request.cookies.get("loggedIn"))
                    return response
                except:
                    db.session.rollback()
                    return render_template('redirect.html' , message="Changes could not be made !! Redirecting you to same page in 3 seconds ." , redirect_url='/create')
                    # return f"""<html>
                    #         <head>
                    #             <meta http-equiv="refresh" content="3;url=/create" />
                    #         </head>
                    #         <body>
                    #             <h2> <span style="color:crimson;text-align:center;"> Changes could not be made !! </span></h2>
                    #             <h4><span style="color:crimson;text-align:center;"> Redirecting you to same page in 3 seconds . </span></h4>
                    #         </body>
                    #         </html>""" 
       







@app.route('/playlist_songs/',methods=['POST'])   # To add songs to a playlist
@app.route('/playlist_songs/<string:playlist_name>',methods=['GET'])   # To display songs in a playlist
@check_loggedIn_jwt_expiration
def playlist_songs(playlist_name=None):
    decoded_token = jwt.decode(request.cookies.get('token'), app.config['SECRET_KEY'], algorithms=['HS256'])
    if request.method=='GET' and playlist_name is not None:
        songs=Songs.query.filter(Songs.song_playlists.any(playlist_name = playlist_name)).all()
        user_id=Users.query.filter(Users.user_name == decoded_token.get("username")).first().user_id
        playlists=Playlists.query.filter(Playlists.playlist_owner_id == user_id)
        return render_template('songs.html',nav_username=decoded_token.get('name'),profilePic_url=decoded_token.get('pic_url'),data=1,songs=songs,playlists=playlists,name=playlist_name)
    elif request.method=='POST' and playlist_name is None:
        playlist_names=request.form.getlist("playlist_name")
        song_name=request.form['song_name-p']
        song_id=Songs.query.filter(Songs.song_name == song_name).first().song_id
        for playlist_name_ in playlist_names: 
            playlist_id=Playlists.query.filter(Playlists.playlist_name == playlist_name_).first().playlist_id
            checks=Playlist_songs.query.filter(Playlist_songs.playlist_id == playlist_id).all()
            flag=False
            for check in checks:
                if check.song_id==song_id:
                    flag=True
                    break
            if flag:
                pass
            else:
                with app.app_context():
                        try:
                            playlist_song = Playlist_songs(song_id=song_id, playlist_id=playlist_id)
                            db.session.add(playlist_song)
                            db.session.commit()
                        except:
                            db.session.rollback()
        return render_template('redirect.html' , message="Added the song to your selected playlist . Redirecting you to the home page in 3 seconds ." , redirect_url='/')
         






@app.route('/playlist_create',methods=["POST"])  # To create a playlist 
@check_loggedIn_jwt_expiration
def createPlaylist():
    decoded_token = jwt.decode(request.cookies.get('token'), app.config['SECRET_KEY'], algorithms=['HS256'])
    if request.method=='POST':
        playlist_name=request.form["playlist_name"]
        song_name=request.form['song_name-a']
        playlist_image=request.files['playlistImage']
        if playlist_image:
            image = Image.open(playlist_image)
            playlist_image = image.resize((224,224))
            buffered=BytesIO()
            playlist_image.save(buffered, format="PNG")
            playlist_image_io= base64.b64encode(buffered.getvalue())
        else:
            return render_template('redirect.html' , message="Provide Cover Image for Playlist . Cannot proceed without it ." , redirect_url='/')
        song_id=Songs.query.filter(Songs.song_name == song_name).first().song_id
        check_playlist=Playlists.query.filter(Playlists.playlist_name == playlist_name).first()
        user_id=Users.query.filter(Users.user_name == decoded_token.get("username")).first().user_id
        if check_playlist is None:
            with app.app_context():
                try:
                    new_playlist=Playlists(playlist_id=gen_uuid(), playlist_name=playlist_name, playlist_image=playlist_image_io,playlist_owner_id=user_id)
                    db.session.add(new_playlist)
                    db.session.commit()
                    playlist_id=Playlists.query.filter(Playlists.playlist_name == playlist_name).first().playlist_id
                    playlist_song = Playlist_songs(song_id=song_id, playlist_id=playlist_id)
                    db.session.add(playlist_song)
                    db.session.commit()
                except:
                    db.session.rollback()
            return render_template('redirect.html' , message="Added the song to your new playlist . Redirecting you to the home page in 3 seconds ." , redirect_url='/')
            
        else:
            return render_template('redirect.html' , message="This Playlist name is already taken . So nothing done . Try creating playlist with a different name . Redirecting you to the home page in 3 seconds ." , redirect_url='/')
            





@app.route('/deleteSong',methods=['POST'])  #To delete song from playlist
@check_loggedIn_jwt_expiration
def delete_Song():
    if request.method=='POST':
        playlist_name=request.form['playlist_name']
        song_name=request.form['song_name-d']
        song_id=Songs.query.filter(Songs.song_name == song_name).first().song_id
        playlist_id=Playlists.query.filter(Playlists.playlist_name == playlist_name).first().playlist_id
        with app.app_context():
            try:
                playlist_song=Playlist_songs.query.filter((Playlist_songs.song_id==song_id) & (Playlist_songs.playlist_id==playlist_id)).first()
        
                db.session.delete(playlist_song)
                db.session.commit()
            except:
                 db.session.rollback()
        return render_template('redirect.html' , message="Song deleted from the playlist . Redirecting you to the playlist page in 3 seconds ." , redirect_url='/playlist_songs/'+playlist_name)
    






@app.route('/album_songs/<string:album_name>',methods=['GET'])    # To dispaly songs in an albumn
@check_loggedIn_jwt_expiration
def album_songs(album_name=None):
    decoded_token = jwt.decode(request.cookies.get('token'), app.config['SECRET_KEY'], algorithms=['HS256'])
    if request.method=='GET'and album_name is not None:
        songs=Songs.query.filter(Songs.album.has(album_name = album_name))
        user_id=Users.query.filter(Users.user_name == decoded_token.get("username")).first().user_id
        user_playlists=Playlists.query.filter(Playlists.playlist_owner_id == user_id).all()
        return render_template('songs.html',nav_username=decoded_token.get('name'),profilePic_url=decoded_token.get('pic_url'),data=0,songs=songs,name=album_name,user_playlists=user_playlists)
        






@app.route('/creator_upload',methods=['POST'])
@check_loggedIn_jwt_expiration
def creator_upload():
    song_name=request.form['songName']
    creator_username=request.form['userName']
    creator_userid=Users.query.filter(Users.user_name == creator_username).first().user_id
    lyrics=request.form['lyrics']
    # print(lyrics)
    album_name=request.form['albumName']
    genre=request.form['genre']
    duration=request.form['duration']
    audio_file = request.files['songFile']
    if audio_file:
        audio_file_io= base64.b64encode(BytesIO(audio_file.read()).getvalue())
    else:
        return render_template('redirect.html' , message="Provide an audio file . Cannot proceed without an audio file ." , redirect_url='/create')
    album_image=request.files['albumImage']
    check_albumName=Albums.query.filter(Albums.album_name == album_name).first()
    if check_albumName is None:
        if album_image:
            image = Image.open(album_image)
            album_image = image.resize((224,224))
            buffered = BytesIO()
            album_image.save(buffered, format="PNG")
            album_image_io= base64.b64encode(buffered.getvalue())
        else:
            return render_template('redirect.html' , message="Provide Cover Image for Album . Cannot proceed without it ." , redirect_url='/create')
    if check_albumName is not None:
        # print(base64.b64encode(image_file_io.getvalue()),"--------------------------------------------------------------------")
        try:
            new_song=Songs(song_id=gen_uuid(), song_name=song_name,song_file=audio_file_io,song_lyrics=lyrics,album=check_albumName, duration=duration, genre=genre)
            db.session.add(new_song)
            db.session.commit()
        except:
            db.session.rollback()
        return render_template('redirect.html' , message="Song added to the album : "+album_name+" which alredy exists . Redirecting you to the create page in 3 seconds ." , redirect_url='/create')
        
    else:
        try:
            new_album=Albums(album_id=gen_uuid(), album_name=album_name,album_image=album_image_io,album_owner_id=creator_userid)
            db.session.add(new_album)
            db.session.commit()
            new_song=Songs(song_id=gen_uuid(),song_file=audio_file_io,song_lyrics=lyrics,song_name=song_name, album=new_album, duration=duration, genre=genre)
            db.session.add(new_song)
            db.session.commit()
        except:
            db.session.rollback()
        return render_template('redirect.html' , message="Creating a new album with the name as "+{album_name}+" and adding the song into it . Redirecting you to the create page in 3 seconds ." , redirect_url='/create')

 



@app.route('/creator_song_delete',methods=['POST'])
@check_loggedIn_jwt_expiration
def creator_song_delete():
    song_name=request.form["songName-d"]
    
    with app.app_context():
        try:
            song_id=Songs.query.filter(Songs.song_name == song_name).first().song_id
            check_playlist_songs=Playlist_songs.query.filter(Playlist_songs.song_id == song_id).all()
            check_user_ratings=User_likes_ratings.query.filter(User_likes_ratings.song_id == song_id).all()
            # print(check_playlist_songs)
            if len(check_playlist_songs)>0:
                # print("YES")
                for playlist_song in check_playlist_songs:
                    db.session.delete(playlist_song)
                db.session.commit()
            if len(check_user_ratings)>0:
                for user_rating in check_user_ratings:
                    db.session.delete(user_rating)
                db.session.commit()
            song=Songs.query.filter(Songs.song_id == song_id).first()
            db.session.delete(song)
            db.session.commit()


        except:
            db.session.rollback()
    return render_template('redirect.html' , message="Song deleted from the album . If any user-playlists contain this song then the song will be deleted from those playlists also . Redirecting you to the create page in 3 seconds ." , redirect_url='/create')
    




@app.route('/creator_song_edit/<string:song_id>',methods=['POST'])
@check_loggedIn_jwt_expiration
def creator_song_edit(song_id):
    song_name=request.form["songName-e"]
    lyrics=request.form["lyrics-e"]
    genre=request.form["genre-e"]
    duration=request.form["duration-e"]
    audio_file = request.files['songFile-e']
    if audio_file:
        audio_file_io= base64.b64encode(BytesIO(audio_file.read()).getvalue())
    
    with app.app_context():
        try:
            song_update=Songs.query.filter(Songs.song_id == song_id).first()
            # print(song_update,song_id,"Hoi")
            song_update.song_name=song_name
            song_update.song_lyrics=lyrics
            song_update.genre=genre
            song_update.duration=duration
            if audio_file:
                song_update.song_file = audio_file_io
            # print("YES")
            db.session.commit()
        except:
            db.session.rollback()
    return render_template('redirect.html' , message="Song details updated . Redirecting you to the create page in 3 seconds ." , redirect_url='/create')
    




# For user to rate a song from the album_songs 
@app.route('/user_rateSong',methods=['POST'])
@check_loggedIn_jwt_expiration
def user_rating():
    decoded_token = jwt.decode(request.cookies.get('token'), app.config['SECRET_KEY'], algorithms=['HS256'])
    if request.method=='POST':
        user_name=decoded_token.get("username")
        user_id=Users.query.filter(Users.user_name == user_name).first().user_id
        song_name=request.form["song_name-r"]
        rating=request.form["ratingValue"]
        album_name=request.form["album_name-r"]
        song_id=Songs.query.filter(Songs.song_name == song_name).first().song_id
        check=User_likes_ratings.query.filter((User_likes_ratings.user_id == user_id) & (User_likes_ratings.song_id == song_id)).first()
        if check is not None:
            try:
                check.song_rating=rating
                db.session.commit()
            except:
                db.session.rollback()
            return  render_template('redirect.html' , message="Rating of the song updated . Redirecting you to the same page in 3 seconds ." , redirect_url='/album_songs/'+album_name)
        else:
            try:
                new=User_likes_ratings(user_id=user_id,song_id=song_id,song_rating=rating)
                db.session.add(new)
                db.session.commit()
            except:
                db.session.rollback()
            return render_template('redirect.html' , message="Thank you for rating the song . Redirecting you to the same page in 3 seconds ." , redirect_url='/album_songs/'+album_name)
            



# Get the liked songs of currently logged in user(JS fetch API )
@app.route("/user_liked_songs/<string:song_id>",methods=["GET"])
@check_loggedIn_jwt_expiration
def check_liked_songs(song_id):
    decoded_token = jwt.decode(request.cookies.get('token'), app.config['SECRET_KEY'], algorithms=['HS256'])
    user_id=Users.query.filter(Users.user_name == decoded_token.get("username")).first().user_id
    user_check=User_likes_ratings.query.filter((User_likes_ratings.user_id == user_id) & (User_likes_ratings.song_id == song_id)).first()
    data={}
    # print(user_check)
    if user_check:
        if user_check.song_liked==1:
            data["check"]=1
        else:
             data["check"]=0
        return jsonify(data),200
    data["check"]=0
    return jsonify(data),200



# For user to add a song to liked list(JS fetch API )
@app.route("/song_like/<string:song_id>/<string:check>",methods=['GET'])
@check_loggedIn_jwt_expiration
def like_song(song_id,check):
    decoded_token = jwt.decode(request.cookies.get('token'), app.config['SECRET_KEY'], algorithms=['HS256'])
    user_id=Users.query.filter(Users.user_name == decoded_token.get("username")).first().user_id
    user_check=User_likes_ratings.query.filter((User_likes_ratings.user_id == user_id) & (User_likes_ratings.song_id == song_id)).first()
    if user_check:
        if check=="1":
            try:
                user_check.song_liked=1
                db.session.commit()
            except:
                db.session.rollback()
            # print("Inside If,If")
            return "OK",200
        
        else:
            try:
                user_check.song_liked=0
                db.session.commit()
            except:
                db.session.rollback()
            # print("Inside If,Else")
            return "",204
        
        
    else:
        if check=="1":
            with app.app_context():
                try:
                    new=User_likes_ratings(user_id=user_id,song_id=song_id,song_liked=1)
                    db.session.add(new)
                    db.session.commit()
                except:
                    db.session.rollback()
            # print("Inside Else-If")
        return "OK" ,200
        
    




# To attach a song to music playing bar on clicking the play-button of the song card(XMLHttpRequest API) 
@app.route("/add_song_queue/<string:song_name>")
# @csrf_protect
@check_loggedIn_jwt_expiration
def add_song_queue(song_name):
    song = Songs.query.filter(Songs.song_name == song_name).first()
    song.song_views+=1
    song_to_send =  dict()
    song_to_send['song_name'] = song_name
    song_to_send['lyrics'] = song.song_lyrics
    album_owner_id=song.album.album_owner_id
    album_owner_name=Users.query.filter(Users.user_id == album_owner_id).first().first_name
    song_to_send['creator_username'] = album_owner_name
    # print(album_owner_name)
    # "data:image/png;base64,{{ song.album.album_image|decodeutf8 }}"
    song_to_send['image']="data:image/png;base64,"+decodeutf8(song.album.album_image) 
    song_to_send['duration'] = song.duration
    song_to_send['song_file'] = str(song.song_file.decode('utf-8', 'ignore'))
    db.session.commit()
    return json.dumps(song_to_send)



# Count the likes of a song in create page(JS fetch API )
@app.route("/song_likes_count/<string:song_id>",methods=['GET'])
@csrf_protect
@check_loggedIn_jwt_expiration
def song_likes_count(song_id):
    data={}
    # print(User_likes_ratings.query.filter_by(song_id = song_id))
    data["count"]=User_likes_ratings.query.filter_by(song_id = song_id,song_liked = 1).count()
    return jsonify(data),200



# Average rating of a song in create page(JS fetch API )
@app.route("/song_avg_rating/<string:song_id>",methods=['GET'])
@csrf_protect
@check_loggedIn_jwt_expiration
def song_avg_rating(song_id):
    data={}
    song_ratings=User_likes_ratings.query.filter(User_likes_ratings.song_id == song_id).all()
    # print(song_ratings)
    sum=0
    if len(song_ratings)>0:
        for rating in song_ratings:
            sum+=rating.song_rating
        data["rating"]=sum/len(song_ratings)
    else:
        data["rating"]=0
    return jsonify(data),200


# For search in index page (JS AJAX API) 
@app.route("/search_albums_playlists",methods=['GET'])
# @csrf_protect
@check_loggedIn_jwt_expiration
def search():
    data={}
    data["playlist_names_lst"]=[]
    data["album_names_lst"]=[]
    data["song_album_names_lst"]=[]
    playlists=Playlists.query.all()
    albums=Albums.query.all()
    songs=Songs.query.all()
    if len(songs)>0:
        for song in songs:
            song_album_id=song.album_id
            album_name=Albums.query.filter(Albums.album_id == song_album_id).first().album_name
            data["song_album_names_lst"].append([song.song_name,album_name])
    # print(data["song_album_names_lst"])
    if len(playlists)>0:
        for playlist in playlists:
            data["playlist_names_lst"].append(playlist.playlist_name)
    if len(albums)>0:
        for album in albums:
            data["album_names_lst"].append(album.album_name)
    return jsonify(data)






@app.route("/admin_signin",methods=['GET','POST'])
def admin_signin():
    decoded_token = jwt.decode(request.cookies.get('token'), app.config['SECRET_KEY'], algorithms=['HS256'])
    if request.method == "GET":
        if decoded_token.get("admin") == "1":
            return redirect("/admin_index")
        return render_template("admin_signin.html")
    if request.method == "POST":
        # print("Hi")
        username = request.form['username']
        password = request.form['password']
        if username in admin_dict.keys():
            user_password=admin_dict[username]
            if password == user_password:
                decoded_token['admin']="1"
                decoded_token['admin_u']=username
                new_token = jwt.encode(decoded_token, app.config['SECRET_KEY'], algorithm='HS256')
                response = make_response(redirect("/admin_index"))
                response.set_cookie("token",new_token)
                return response
            else:
                return render_template('redirect.html' , message="Admin Password Incorect !! Redirecting you to same admin signin page in 3 seconds . Please Retry ." , redirect_url='/admin_signin')
                # return f"""<html>
                #         <head>
                #             <meta http-equiv="refresh" content="3;url=/admin_signin" />
                #         </head>
                #         <body>
                #             <h2> <span style="color:crimson;text-align:center;">Admin Password Incorect !! </span></h2>
                #             <h4><span style="color:crimson;text-align:center;"> Redirecting you to same admin signin page in 3 seconds . Please Retry . </span></h4>
                #         </body>
                        # </html>"""
        else:
            return render_template('redirect.html' , message="No admin with the given username found  !! Redirecting you to home page in 3 seconds ." , redirect_url='/')
            # return f"""<html>
            #             <head>
            #                 <meta http-equiv="refresh" content="3;url=/" />
            #             </head>
            #             <body>
            #                 <h2> <span style="color:crimson;text-align:center;">No admin with the given username found  !! </span></h2>
            #                 <h4><span style="color:crimson;text-align:center;"> Redirecting you to home page in 3 seconds . </h4>
            #             </body>
            #             </html>"""




@app.route("/admin_logout")
def admin_logout():
    decoded_token = jwt.decode(request.cookies.get('token'), app.config['SECRET_KEY'], algorithms=['HS256'])
    decoded_token['admin']="0"
    decoded_token['admin_u']=""
    new_token = jwt.encode(decoded_token, app.config['SECRET_KEY'], algorithm='HS256')
    response = make_response(redirect("/"))
    response.set_cookie("token",new_token)
    return response



@app.route("/admin_index")
def admin_index_page():
    # nav_username=request.cookies.get("username")
    decoded_token = jwt.decode(request.cookies.get('token'), app.config['SECRET_KEY'], algorithms=['HS256'])
    total_users = len(Users.query.all())
    total_creators = len(Users.query.filter(Users.role == "creator").all())
    total_songs = len(Songs.query.all())
    total_albums = len(Albums.query.all())
    return render_template('admin_index.html', nav_username=decoded_token.get("admin_u"), total_users = total_users, total_creators = total_creators, total_songs= total_songs, total_albums = total_albums)


@app.route('/admin/all/<string:ele>', methods = ['GET', 'POST'])
def show(ele):
    decoded_token = jwt.decode(request.cookies.get('token'), app.config['SECRET_KEY'], algorithms=['HS256'])
    all_data = []
    if ele == 'user':
        data=Users.query.all()
        for row in data:
            temp = []
            id = row.user_id
            temp.append(id)
            name = row.first_name
            if row.last_name is not None:
                name+=" "
                name+= row.last_name
            temp.append(name)
            username = row.user_name
            temp.append(username)
            role=row.role
            temp.append(role)
            all_data.append(temp)
        return render_template('details_admin.html', data=all_data, check = "user",nav_username=decoded_token.get("admin_u"))
    elif ele == 'creator':
        data=Users.query.filter(Users.role == "creator").all()
        for row in data:
            temp = []
            id = row.user_id
            temp.append(id)
            name = row.first_name
            if row.last_name is not None:
                name+=" "
                name+= row.last_name
            temp.append(name)
            username=name = row.user_name
            temp.append(username)
            all_data.append(temp)
        return render_template('details_admin.html', data=all_data, check = "creator",nav_username=decoded_token.get("admin_u"))
    elif ele == 'songs':
        data=Songs.query.all()
        for row in data:
            temp = []
            id = row.song_id
            temp.append(id)
            name = row.song_name
            temp.append(name)
            genre=row.genre
            temp.append(genre)
            album_name=row.album.album_name
            temp.append(album_name)
            album_owner=Users.query.filter(Users.user_id == row.album.album_owner_id).first().first_name
            temp.append(album_owner)
            song_average_rating = db.session.query(db.func.avg(User_likes_ratings.song_rating)).filter(User_likes_ratings.song_id == id).scalar()
            temp.append(song_average_rating)
            song_likes_count = User_likes_ratings.query.filter_by(song_id = row.song_id,song_liked = 1).count()
            temp.append(song_likes_count)
            song_views_count = Songs.query.filter(Songs.song_id == row.song_id).first().song_views
            temp.append(song_views_count)
            all_data.append(temp)
        return render_template('details_admin.html', data=all_data, check = "songs",nav_username=decoded_token.get("admin_u"))
    elif ele=='albums':
        data=Albums.query.all()
        for row in data:
            temp=[]
            id=row.album_id
            temp.append(id)
            album_name=row.album_name
            temp.append(album_name)
            album_owner = Users.query.filter(Users.user_id == row.album_owner_id).first().first_name
            temp.append(album_owner)

            #Song Count in an album
            songs_count=Songs.query.filter(Songs.album.has(album_name = album_name)).count()
            temp.append(songs_count)
            all_data.append(temp)
        return render_template('details_admin.html', data=all_data, check = "albums",nav_username=decoded_token.get("admin_u"))




@app.route("/admin_song_delete",methods=['POST'])
def admin_song_delete():
    song_name=request.form["songName-d"]
    
    with app.app_context():
        try:
            song_id=Songs.query.filter(Songs.song_name == song_name).first().song_id
            check_playlist_songs=Playlist_songs.query.filter(Playlist_songs.song_id == song_id).all()
            check_user_ratings=User_likes_ratings.query.filter(User_likes_ratings.song_id == song_id).all()
            # print(check_playlist_songs)
            if len(check_playlist_songs)>0:
                # print("YES")
                for playlist_song in check_playlist_songs:
                    db.session.delete(playlist_song)
                db.session.commit()
            if len(check_user_ratings)>0:
                for user_rating in check_user_ratings:
                    db.session.delete(user_rating)
                db.session.commit()
            # print("YES")
            song=Songs.query.filter(Songs.song_id == song_id).first()
            db.session.delete(song)
            db.session.commit()
        except:
            db.session.rollback()
    return render_template('redirect.html' , message="Song deleted . If any user-playlists contain this song then the song will be deleted from those playlists also . Redirecting you to the Admin Home page in 3 seconds ." , redirect_url='/admin_index')
    # return f"""<html>
    #                         <head>
                                
    #                             <meta http-equiv="refresh" content="5;url=/admin_index" />
    #                         </head>
    #                         <body>
    #                             <h2> <span style="color:crimson;text-align:center;"> Song deleted . If any user-playlists contain this song then the song will be deleted from those playlists also .  </span></h2>
    #                             <h4><span style="color:crimson;text-align:center;"> Redirecting you to the Admin Home page in 5 seconds . </span></h4>
    #                         </body>
    #                         </html>"""



@app.route("/admin_album_delete",methods=['POST'])
def admin_album_delete():
    album_name=request.form["albumName-d"]
    with app.app_context():
        album=Albums.query.filter(Albums.album_name == album_name).first()
        check_songs=Songs.query.filter(Songs.album.has(album_name = album_name)).all()
        if len(check_songs)>0:
            for check_song in check_songs:
                playlist_check=Playlist_songs.query.filter(Playlist_songs.song_id == check_song.song_id).all()
                check_user_ratings=User_likes_ratings.query.filter(User_likes_ratings.song_id == check_song.song_id).all()

                for check in playlist_check:
                    db.session.delete(check)
                db.session.commit()


                for user_rating in check_user_ratings:
                    db.session.delete(user_rating)
                db.session.commit()

                db.session.delete(check_song)
                db.session.commit()
        db.session.delete(album)
        db.session.commit()
    return render_template('redirect.html' , message="Album deleted . Songs of the album also deleted . If any user-playlists contain these song then the songs will be deleted from those playlists also . Redirecting you to the Admin Home page in 3 seconds ." , redirect_url='/admin_index')

      

if __name__ == '__main__':
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )