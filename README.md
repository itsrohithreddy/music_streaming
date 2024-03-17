# Music Streaming Web Application

Welcome to the Music Streaming Web Application! This application allows users to stream music, manage their playlists, and interact with their favorite songs and albums.

## Features

### User Management
- **Authentication:** Users can sign up for an account or log in with their existing credentials.
- **Role-based Access Control:** Different roles such as admin and user are available, each with its own set of permissions.

### Music Management
- **Upload Songs and Albums:** Users can upload their favorite songs and albums to the platform.
- **Create Playlists:** Users can create custom playlists and add songs to them.
- **View Album Details:** Users can explore details about albums, including songs, artists, and cover images.
- **Like/Dislike Songs:** Users can express their preference for songs by liking or disliking them.
- **Rate Songs:** Users can rate songs based on their liking.

### Admin Panel
- **User Management:** Admins have access to a dedicated panel for managing users, including adding/removing users and changing their roles.
- **Content Management:** Admins can manage albums, songs, and playlists, including adding, editing, or deleting them.

## Technologies Used

- **Flask:** Flask is a lightweight web framework for Python, used for building web applications.
- **Flask-SQLAlchemy:** Flask-SQLAlchemy is an extension for Flask that adds support for SQLAlchemy, a powerful SQL toolkit and Object-Relational Mapper (ORM).
- **Werkzeug:** Werkzeug is a WSGI utility library for Python, providing various utilities for building web applications.

## Setup

Follow the steps below to set up and run the Music Streaming Web Application on your local machine:


1. Clone the repository:
   git clone https://github.com/slvarun/Music-streaming-App.git


2. Install dependencies:
   pip install -r requirements.txt

3. Run the db.py file to initialize the database with all the db classes:
   python db.py

4. Run the application:
   python app.py

5. Access the application in your web browser at [http://localhost:5000](http://localhost:5000).

## Contributors

- M.Varun
- G.Rohith reddy
- A.Sai Tharun



