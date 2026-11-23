from flask import Flask, render_template, session
from db.config import configure
from api.auth import init_auth, signup, login, logout


# The compiler cannot find a directory of server/templates/index.html
# without using template_folder="static".
app = Flask(__name__, static_folder="static", template_folder="static")
configure(app)
init_auth(app)

app.add_url_rule("/signup", view_func=signup, methods=["GET", "POST"])
app.add_url_rule("/login", view_func=login, methods=["GET", "POST"])
app.add_url_rule("/logout", view_func=logout)



@app.route("/")
def index():
    return render_template(
        "index.html",
        name=session.get("name"),
        username=session.get("username"),)


@app.route("/admin")
def admin():
    return render_template("admin/admin.html")


@app.route("/instructor")
def instructor():
    return render_template("instructor/instructor.html")


@app.route("/student")
def student():
    return render_template("student/student.html")


if __name__ == "__main__":
    app.run(debug=True)