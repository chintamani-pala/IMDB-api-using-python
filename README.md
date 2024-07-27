# IMDb Movie Data API

A Flask-based API that fetches movie data from IMDb. This API allows you to search for movies by name and retrieve detailed information about a movie using its IMDb ID.

## Features

- Search movies by name.
- Retrieve detailed movie data including:
  - Title
  - Thumbnail
  - Release Year
  - Average Rating
  - Rating Vote Count
  - Duration
  - Description
  - Director
  - Writers
  - Stars
  - Playback URL
  - Release Date
  - Country of Origin
  - Languages
  - Production Budget
  - Worldwide Gross
  - Top Casts

## Setup

### Prerequisites

Ensure you have Python 3.7 or higher installed on your system.

### Installation

1. **Clone the repository:**
  ```bash
   git clone https://github.com/yourusername/your-repository.git
   cd your-repository
  ```

2. **Install the dependencies:**
  ```bash
    pip install -r requirements.txt
  ```

3. **Run the Flask application: **
  ```bash
    python app.py
  ```

# EndPoints
## Search Movies by Name:
  Endpoint: /api/search
  Method: GET
  Parameters:  query (required): The name of the movie to search for.
  Example Request:
  ```bash
  curl "http://127.0.0.1:5000/api/search?query=Inception"
  ```

## Get Movie Data by IMDb ID:
  Endpoint: /api/movie
  Method: GET
  Parameters: id (required): The IMDb ID of the movie.
  Example Request:
  ```bash
    curl "http://127.0.0.1:5000/api/movie?id=tt1375666"
  ```
# Error Handling
## The API handles various errors gracefully and returns appropriate HTTP status codes and error messages.
  - 400 Bad Request: Missing required query parameters.
  - 404 Not Found: Script tag or data not found.
  - 500 Internal Server Error: Unexpected server errors.
