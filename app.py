from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)
DB_PATH = "movies.db"


# ─────────────────────────────────────────────
#  Helper: open a database connection
# ─────────────────────────────────────────────
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # lets you access columns by name, e.g. row["title"]
    return conn


# ─────────────────────────────────────────────
#  Helper: fetch distinct values for dropdowns
# ─────────────────────────────────────────────
def get_filter_options():
    conn = get_db_connection()

    # Fetch distinct genres sorted alphabetically
    genres = [row[0] for row in conn.execute("SELECT DISTINCT genre FROM movies ORDER BY genre ASC").fetchall()]

    # Fetch distinct directors sorted alphabetically
    directors = [row[0] for row in conn.execute("SELECT DISTINCT director FROM movies ORDER BY director ASC").fetchall()]

    conn.close()
    return genres, directors


# ─────────────────────────────────────────────
#  Main route
# ─────────────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    # --- Read filter values sent by the HTML form --------------------------------
    search    = request.args.get("search",   "").strip()
    genre     = request.args.get("genre",    "")
    director  = request.args.get("director", "")
    year_min  = request.args.get("year_min",   type=int, default=1970)
    year_max  = request.args.get("year_max",   type=int, default=2024)
    rating_min = request.args.get("rating_min", type=float, default=0.0)
    rating_max = request.args.get("rating_max", type=float, default=10.0)

    # --- Build the SQL query dynamically -----------------------------------------
    query      = "SELECT * FROM movies"
    conditions = []
    params     = []

    # Add condition for search text in title (case-insensitive)
    if search:
        conditions.append("UPPER(title) LIKE ?")
        params.append(f"%{search.upper()}%")

    # Add condition for genre (case-insensitive)
    if genre:
        conditions.append("UPPER(genre) = ?")
        params.append(genre.upper())

    # Add condition for director (case-insensitive)
    if director:
        conditions.append("UPPER(director) = ?")
        params.append(director.upper())

    # Add conditions for year and rating ranges
    conditions.append("year >= ?")
    params.append(year_min)

    conditions.append("year <= ?")
    params.append(year_max)

    conditions.append("rating >= ?")
    params.append(rating_min)

    conditions.append("rating <= ?")
    params.append(rating_max)

    # Assemble the final query
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY rating DESC"

    # Execute the query and fetch results
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    movies = cursor.fetchall()
    conn.close()

    genres, directors = get_filter_options()

    return render_template(
        "index.html",
        movies=movies,
        genres=genres,
        directors=directors,
        # Pass filter values back so the form keeps them selected after submit
        search=search,
        selected_genre=genre,
        selected_director=director,
        year_min=year_min,
        year_max=year_max,
        rating_min=rating_min,
        rating_max=rating_max,
        result_count=len(movies),
    )


if __name__ == "__main__":
    app.run(debug=True)
