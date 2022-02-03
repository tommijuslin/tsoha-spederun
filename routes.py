from app import app
from flask import render_template, request, redirect, session, url_for
import users
import games
import runs
import platforms
import games_platforms

NEGATIVE = -1

@app.route("/")
def index():
    return render_template("index.html", games=games.get_all_games())

@app.route("/add_game", methods=["get", "post"])
def add_game():
    if request.method == "POST":
        title = request.form["title"]
        if len(title) > 100 or len(title) < 1:
            return render_template("error.html", message="Game title must be 1-100 characters long.")

        games.add_game(title)

        return redirect("/")
    
    return render_template("add_game.html")

@app.route("/game/<int:id>/submit_run", methods=["get", "post"])
def submit_run(id):
    if request.method == "POST":
        time = {
            "hours": validate_time(request.form["hours"]),
            "minutes": validate_time(request.form["minutes"]),
            "seconds": validate_time(request.form["seconds"]),
            "ms": validate_time(request.form["ms"])
        }
        
        if NEGATIVE in time:
            return render_template("error.html", message="Time must be positive.")
        
        if all(value == 0 for value in time.values()):
            return render_template("error.html", message="Time must be non-zero.")

        formatted_time = convert_to_ms(time["hours"], time["minutes"], time["seconds"], time["ms"])

        user_id = request.form["user_id"]
        platform_id = request.form["selected_platform"]
        runs.add_run(id, formatted_time, platform_id, user_id)

        if not games_platforms.get_platform(platform_id):
            games_platforms.add_platform(id, platform_id)

        return redirect(url_for("game", id=id))
    
    return render_template("submit_run.html", game=games.get_game(id),
                                              platforms=platforms.get_all_platforms())

@app.route("/game/<int:id>")
def game(id):
    game = games.get_game(id)
    if game:
        return render_template("game.html", game=game,
                                            runs=runs.get_runs(id),
                                            platforms=games_platforms.get_all_platforms(id),
                                            format_time=format_time)
    
    return render_template("error.html", message=f"No game with id { id } could be found.")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if users.login(username, password):
            return redirect("/")
        else:
            return render_template("error.html", message="Wrong username or password")
    
    return render_template("login.html")

@app.route("/register", methods=["get", "post"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        if len(username) < 1 or len(username) > 20:
            return render_template("error.html", message="Username must be 1-20 characters long.")
        if users.get_username(username):
            return render_template("error.html", message="User with that name already exists.")

        password1 = request.form["password1"]
        password2 = request.form["password2"]
        if password1 != password2:
            return render_template("error.html", message="Passwords don't match")
        if users.register(username, password1):
            return redirect("/")
        else:
            return render_template("error.html", message="Registration failed")
    
    return render_template("register.html")
    
@app.route("/logout")
def logout():
    del session["user_id"]
    del session["username"]
    return redirect("/")

def convert_to_ms(hours, minutes, seconds, ms):
    s = 1000 * seconds
    m = 60000 * minutes
    h = 3600000 * hours

    return h + m + s + ms

def format_time(ms):
    second_ms = divmod(ms, 1000)
    min_second = divmod(second_ms[0], 60)
    hour_min = divmod(min_second[0], 60)

    s = int(min_second[1])
    m = int(hour_min[1])
    h = int(hour_min[0])

    return f"{h}h {m}m {s}s"

def validate_time(time):
    if time == "":
        return 0
    elif int(time) < 0:
        return NEGATIVE

    return int(time)
