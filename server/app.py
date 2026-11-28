from flask import Flask, render_template, session, request
import pymysql
from db.config import configure
from api.auth import init_auth, signup, login, logout
from db.connection import get_db_connection


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

# Instructor
@app.route("/instructor/submitGrades")
def submit_grades():
    return render_template("instructor/submitGrades.html")

@app.route("/instructor/submitGradesRoster")
def submit_grades_roster():
    courseid = request.args.get("courseid")
    sec_num = request.args.get("sec_number")
    semester = request.args.get("semester")
    year = request.args.get("year")

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    roster = []

    try:
        cursor.callproc("instructor_check_section_roster", [courseid, sec_num, semester, year])
        roster = [
            row for row in cursor.fetchall()
            if row["grade"] is None
        ]

    finally:
        cursor.close()
        conn.close()

    return render_template(
        "instructor/submitGrades.html",
        roster=roster,
        courseid=courseid,
        sec_num=sec_num,
        semester=semester,
        year=year,
    )

@app.route("/instructor/submitGradesSubmit", methods=["POST"])
def submit_grades_submit():
    courseid = request.form.get("courseid")
    sec_num = request.form.get("sec_number")
    semester = request.form.get("semester")
    year = request.form.get("year")
    grades = request.form.getlist("grade")
    student_ids = request.form.getlist("student_id")

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        for student_id, grade in zip(student_ids, grades):
            cursor.callproc("instructor_submit_grades", [student_id, courseid, sec_num, semester, year, grade])
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

    return render_template("instructor/submitGrades.html", submitted=True)

@app.route("/instructor/changeGrades")
def change_grades():
    return render_template("instructor/changeGrades.html")

@app.route("/instructor/changeGradesRoster")
def change_grades_roster():
    courseid = request.args.get("courseid")
    sec_num = request.args.get("sec_number")
    semester = request.args.get("semester")
    year = request.args.get("year")

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    roster = []

    try:
        cursor.callproc("instructor_check_section_roster", [courseid, sec_num, semester, year])
        roster = [
            row for row in cursor.fetchall()
            if row["grade"] is not None
        ]

    finally:
        cursor.close()
        conn.close()

    return render_template(
        "instructor/changeGrades.html",
        roster=roster,
        courseid=courseid,
        sec_num=sec_num,
        semester=semester,
        year=year,
    )

@app.route("/instructor/changeGradesSubmit", methods=["POST"])
def change_grades_submit():
    courseid = request.form.get("courseid")
    sec_num = request.form.get("sec_number")
    semester = request.form.get("semester")
    year = request.form.get("year")
    student_ids = request.form.getlist("student_id")
    updates = [
        (student_id, request.form.get(f"new_grade_{student_id}"))
        for student_id in student_ids
        if request.form.get(f"new_grade_{student_id}")
    ]

    if not updates:
        return render_template(
            "instructor/changeGrades.html",
            error="Select a replacement grade for at least one student.",
        ), 400

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        for student_id, grade in updates:
            cursor.callproc(
                "instructor_change_grades",
                [student_id, courseid, sec_num, semester, year, grade],
            )
            cursor.execute(
                """
                SELECT grade
                FROM takes
                WHERE takes_id = %s
                  AND course_id = %s
                  AND sec_number = %s
                  AND semester = %s
                  AND year = %s
                """,
                [student_id, courseid, sec_num, semester, year],
            )
            updated_row = cursor.fetchone()
            if updated_row is None or updated_row["grade"] != grade:
                conn.rollback()
                return render_template(
                    "instructor/changeGrades.html",
                    error=(
                        "A grade was not updated. Check that the selected "
                        "section and stored procedure match this database."
                    ),
                ), 409
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

    return render_template("instructor/changeGrades.html", submitted=True)

@app.route("/instructor/addStudentAsAdvisor")
def add_student_as_advisor():
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("select instructor_id from instructor where user_id = %s", (session["user_id"]))
    instructor = cursor.fetchone()
    instructor_id = instructor["instructor_id"]
    cursor.execute("select s_id from advisor where i_id = %s", (instructor_id))
    all_students = cursor.fetchall()
    return render_template("instructor/addStudentAsAdvisor.html", all_students=all_students)

@app.route("/instructor/addStudentAsAdvisorSubmit", methods=["POST"])
def add_student_as_advisor_submit():
    student_id = request.form.get("student_id")
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("select * from advisor where s_id = %s", (student_id))
    student = cursor.fetchone()
    if student:
        cursor.close()
        conn.close()
        return render_template("instructor/addStudentAsAdvisor.html", error="Student already has an advisor.")

    cursor.execute("select instructor_id from instructor where user_id = %s", (session["user_id"]))
    instructor = cursor.fetchone()
    instructor_id = instructor["instructor_id"]
    try:
        cursor.callproc("instructor_advise_student", [instructor_id, student_id])
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

    return render_template("instructor/addStudentAsAdvisor.html", student = True)

@app.route("/instructor/removeStudentAsAdvisor")
def remove_student_as_advisor():
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("select instructor_id from instructor where user_id = %s", (session["user_id"]))
    instructor = cursor.fetchone()
    instructor_id = instructor["instructor_id"]
    cursor.execute("select s_id from advisor where i_id = %s", (instructor_id))
    all_students = cursor.fetchall()
    return render_template("instructor/removeStudentAsAdvisor.html", all_students=all_students)

@app.route("/instructor/removeStudentAsAdvisorSubmit", methods=["POST"])
def remove_student_as_advisor_submit():
    student_id = request.form.get("student_id")
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("select * from advisor where s_id = %s", (student_id))
    student = cursor.fetchone()
    if student is None:
        cursor.close()
        conn.close()
        return render_template("instructor/removeStudentAsAdvisor.html", error="Student is not assigned to this advisor.")

    cursor.execute("select instructor_id from instructor where user_id = %s", (session["user_id"]))
    instructor = cursor.fetchone()
    instructor_id = instructor["instructor_id"]
    try:
        cursor.callproc("instructor_unadvise_student", [instructor_id, student_id])
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

    return render_template("instructor/removeStudentAsAdvisor.html", student = True)

@app.route("/instructor/modifyCoursePrerequisites")
def modify_course_prerequisites():
    return render_template("instructor/modifyCoursePrerequisites.html")

@app.route("/instructor/modifyCoursePrerequisitesData", methods=["POST"])
def modify_course_prerequisites_data():
    course_id = request.form.get("course")
    prereq_id = request.form.get("old_prerequisite")
    new_prereq_id = request.form.get("new_prerequisite")

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("select * from prereq where course_id = %s and prereq_id = %s", (course_id, prereq_id))
    prereq = cursor.fetchone()
    if prereq is None:
        cursor.close()
        conn.close()
        return render_template("instructor/modifyCoursePrerequisites.html", error="That prerequisite does not exist for that course.")

    try:
        cursor.callproc("instructor_modify_prereq", [course_id, prereq_id, course_id, new_prereq_id])
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

    return render_template("instructor/modifyCoursePrerequisites.html", success=True)

@app.route("/instructor/removeStudentFromSection")
def remove_student_from_section():
    return render_template("instructor/removeStudentFromSection.html")

@app.route("/instructor/removeStudentFromSectionData", methods=["POST"])
def remove_student_from_section_data():
    course_id = request.form.get("courseid")
    sec_num = request.form.get("sec_number")
    semester = request.form.get("semester")
    year = request.form.get("year")
    student_id = request.form.get("student_id")

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute(
        "select * from takes where takes_id = %s and course_id = %s and sec_number = %s and semester = %s and year = %s",
        (student_id, course_id, sec_num, semester, year)
    )
    enrollment = cursor.fetchone()
    if enrollment is None:
        cursor.close()
        conn.close()
        return render_template("instructor/removeStudentFromSection.html", error="Student is not enrolled in that section.")

    try:
        cursor.callproc("instructor_remove_student_from_section", [student_id, course_id, sec_num, semester, year])
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

    return render_template("instructor/removeStudentFromSection.html", student=True)

@app.route("/instructor/checkSectionRoster")
def check_section_roster():
    return render_template("instructor/checkSectionRoster.html")

@app.route("/instructor/checkSectionRosterData", methods=["GET"])
def check_section_roster_data():
    courseid = request.args.get("courseid")
    sec_num = request.args.get("sec_number")
    semester = request.args.get("semester")
    year = request.args.get("year")

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    roster = []

    try:
        cursor.callproc("instructor_check_section_roster", [courseid, sec_num, semester, year])
        roster = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    return render_template("instructor/checkSectionRoster.html", roster=roster)

@app.route("/instructor/checkSectionsTeaching")
def check_sections_teaching(): 
    return render_template("instructor/checkSectionsTeaching.html")

@app.route("/instructor/checkSectionsTeachingData", methods=["GET"])
def check_sections_teaching_data():
    semester = request.args.get("semester")
    year = request.args.get("year")

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("select instructor_id from instructor where user_id = %s", (session["user_id"]))
    instructor = cursor.fetchone()
    teaches_id = instructor["instructor_id"]

    try:
        cursor.callproc("instructor_check_sections_teaching", [teaches_id, semester, year])
        sections = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    return render_template("instructor/checkSectionsTeaching.html", sections=sections)

@app.route("/instructor/modifyPersonalInformation")
def modify_personal_information():
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("select first_name, middle_name, last_name, email from instructor where user_id = %s", (session["user_id"]))
    instructor = cursor.fetchone()
    return render_template("instructor/modifyPersonalInformation.html", instructor=instructor)

@app.route("/instructor/modifyPersonalInformationData", methods=["POST"])
def modify_personal_information_data():
    first_name = request.form["first_name"]
    middle_name = request.form["middle_name"]
    last_name = request.form["last_name"]
    email = request.form["email"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("select instructor_id from instructor where user_id = %s", (session["user_id"]))
    instructor = cursor.fetchone()
    instructor_id = instructor["instructor_id"]

    try:
        cursor.callproc("instructor_modify_information", [instructor_id, first_name, middle_name, last_name, email])
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

    return render_template("instructor/modifyPersonalInformation.html", success=True, instructor=instructor)

if __name__ == "__main__":
    app.run(debug=True)