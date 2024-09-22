# Music Streaming Web Application

Welcome to the Music Streaming Web Application! This application allows users to stream music, manage their playlists, and interact with their favorite songs and albums.

## Features

### User Management
- **Authorization:** Implemented Google's OAuth for secure logins.
- **Role-based Access Control:** Different roles such as admin , user and creator are available, each with its own set of permissions.

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

## Setup

Follow the steps below to set up and run the Music Streaming Web Application on your local machine:


1. Clone the repository:
   ```bash
   git clone https://github.com/itsrohithreddy/music_streaming
   ```


2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the db.py file by navigating to `code` directory . This initializes the database with the tables required:
   ```bash
   python db.py
   ```

4. Run the application(present within the `code` directory):
   ```bash
   python app.py
   ```

5. Access the application in your web browser at [http://localhost:5000](http://localhost:5000).



