from flask import render_template, redirect, url_for, request, session
from db.connection import get_db_connection
from db.queries import (
    ROLE_SELECT_QUERIES,
    ROLE_UPDATE_QUERIES,
    SELECT_EXISTING_USER_QUERY,
    INSERT_USER_QUERY,
    ROLE_NAME_QUERIES,
    LOGIN_USER_QUERY,
)

ROLE_ROUTE_PREFIXES = {
    "/admin": "admin",
    "/instructor": "instructor",
    "/student": "student",
}


# Initialize auth
def init_auth(app):
    @app.before_request
    def verify_role_access():
        for prefix, required_role in ROLE_ROUTE_PREFIXES.items():
            if request.path == prefix or request.path.startswith(prefix + "/"):
                if session.get("role") != required_role:
                    return redirect(url_for("login"))



def signup():
    if request.method == "GET":
        return render_template("signup.html")

    email = request.form.get("email")
    username = request.form.get("username")
    password = request.form.get("password")

    # Remove blank in string
    email, username, password = [
        value.strip() if value else ""
        for value in (email, username, password)
    ]

    # If at is not in email, the email address is invalid
    if "@" not in email:
        return render_template("signup.html", error="Invalid email")

    # Extract user_id from email
    user_id = email.split("@")[0]

    db = get_db_connection()
    try:
        with db.cursor() as cursor:
            matched_role = None
            existing_user_id = None

            for role, query in ROLE_SELECT_QUERIES.items():
                cursor.execute(query, [email])
                record = cursor.fetchone()

                if record:
                    matched_role = role
                    existing_user_id = record["user_id"]
                    break


            if not matched_role:
                return render_template("signup.html",
                                       error="Email not found")

            if existing_user_id is not None:
                return render_template("signup.html",
                                       error="Account already exists")

            cursor.execute(SELECT_EXISTING_USER_QUERY, (user_id, username))
            if cursor.fetchone():
                return render_template("signup.html",
                                       error="Username or ID already exists")

            cursor.execute(INSERT_USER_QUERY, (user_id, username, password, matched_role))
            cursor.execute(ROLE_UPDATE_QUERIES[matched_role], (user_id, email))

        db.commit()
        return redirect(url_for("login"))
    
    except Exception:
        db.rollback()
        raise

    finally:
        db.close()



def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username")
    password = request.form.get("password")

    # Remove blank in string
    username, password = [
        value.strip() if value else ""
        for value in (username, password)
    ]

    db = get_db_connection()
    try:
        with db.cursor() as cursor:
            cursor.execute(LOGIN_USER_QUERY, (username, password))
            user = cursor.fetchone()

            if not user:
                return render_template("login.html",
                                       error="Invalid username or password")

            cursor.execute(ROLE_NAME_QUERIES[user["role"]], (user["user_id"],))
            profile = cursor.fetchone()
    finally:
        db.close()

    full_name = ""
    if profile:
        name_parts = [
            part.strip()
            for part in (
                profile["first_name"],
                profile["middle_name"],
                profile["last_name"],
            )
            if part and part.strip()
        ]
        full_name = " ".join(name_parts)

    session["user_id"] = user["user_id"]
    session["username"] = user["username"]
    session["role"] = user["role"]
    session["name"] = full_name

    return redirect(url_for(user["role"]))




def logout():
    return redirect(url_for("login"))