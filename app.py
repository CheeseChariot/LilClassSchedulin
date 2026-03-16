import json
import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, abort

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
TEACHER_DIR = os.path.join(DATA_DIR, "teacher")
STUDENT_DIR = os.path.join(DATA_DIR, "student")
BADGES_FILE = os.path.join(DATA_DIR, "badges.json")
PROGRESSION_FILE = os.path.join(DATA_DIR, "progression.json")

CLASS_STATUSES = ["Untaken", "Pass", "Fail", "Retry", "Force"]


# ── helpers ──────────────────────────────────────────────────────────────────

def _load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def _save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _safe_filename(name: str) -> str:
    """Convert a display name into a safe file/id slug."""
    return "".join(c if (c.isalnum() or c in "-_") else "_" for c in name.lower())


def _list_profiles(directory: str) -> list[dict]:
    if not os.path.isdir(directory):
        return []
    profiles = []
    for fname in sorted(os.listdir(directory)):
        if fname.endswith(".json"):
            profile = _load_json(os.path.join(directory, fname))
            if profile:
                profiles.append(profile)
    return profiles


# ── views ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    teachers = _list_profiles(TEACHER_DIR)
    students = _list_profiles(STUDENT_DIR)
    badges = _load_json(BADGES_FILE).get("badges", [])
    achieved = sum(1 for b in badges if b.get("achieved"))
    return render_template(
        "index.html",
        teachers=teachers,
        students=students,
        badges=badges,
        achieved=achieved,
    )


# ── teachers ──────────────────────────────────────────────────────────────────

@app.route("/teachers")
def teachers():
    profiles = _list_profiles(TEACHER_DIR)
    return render_template("teachers.html", teachers=profiles)


@app.route("/teacher/<teacher_id>")
def teacher_profile(teacher_id):
    path = os.path.join(TEACHER_DIR, f"{teacher_id}.json")
    if not os.path.isfile(path):
        abort(404)
    teacher = _load_json(path)
    return render_template("teacher_profile.html", teacher=teacher)


@app.route("/teacher/add", methods=["GET", "POST"])
def add_teacher():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            return render_template("add_teacher.html", error="Name is required.")
        teacher_id = _safe_filename(name)
        path = os.path.join(TEACHER_DIR, f"{teacher_id}.json")
        if os.path.isfile(path):
            return render_template("add_teacher.html", error="A teacher with that name already exists.")
        _save_json(path, {"id": teacher_id, "name": name, "classes": []})
        return redirect(url_for("teacher_profile", teacher_id=teacher_id))
    return render_template("add_teacher.html", error=None)


@app.route("/teacher/<teacher_id>/class/add", methods=["GET", "POST"])
def add_class(teacher_id):
    path = os.path.join(TEACHER_DIR, f"{teacher_id}.json")
    if not os.path.isfile(path):
        abort(404)
    teacher = _load_json(path)
    if request.method == "POST":
        class_name = request.form.get("class_name", "").strip()
        if not class_name:
            return render_template("add_class.html", teacher=teacher, error="Class name is required.")
        class_id = _safe_filename(class_name)
        new_class = {"id": class_id, "name": class_name, "schedule": None, "status": None}
        teacher["classes"].append(new_class)
        _save_json(path, teacher)
        return redirect(url_for("teacher_profile", teacher_id=teacher_id))
    return render_template("add_class.html", teacher=teacher, error=None)


@app.route("/teacher/<teacher_id>/class/<class_id>/schedule", methods=["GET", "POST"])
def edit_schedule(teacher_id, class_id):
    path = os.path.join(TEACHER_DIR, f"{teacher_id}.json")
    if not os.path.isfile(path):
        abort(404)
    teacher = _load_json(path)
    cls = next((c for c in teacher["classes"] if c["id"] == class_id), None)
    if cls is None:
        abort(404)
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    if request.method == "POST":
        schedule = {}
        for day in days:
            val = request.form.get(day, "").strip()
            if val:
                schedule[day] = val
        cls["schedule"] = schedule if schedule else None
        status = request.form.get("status", "").strip() or None
        cls["status"] = status
        _save_json(path, teacher)
        return redirect(url_for("teacher_profile", teacher_id=teacher_id))
    return render_template("edit_schedule.html", teacher=teacher, cls=cls, days=days)


# ── students ──────────────────────────────────────────────────────────────────

@app.route("/students")
def students():
    profiles = _list_profiles(STUDENT_DIR)
    return render_template("students.html", students=profiles)


@app.route("/student/<student_id>")
def student_profile(student_id):
    path = os.path.join(STUDENT_DIR, f"{student_id}.json")
    if not os.path.isfile(path):
        abort(404)
    student = _load_json(path)
    return render_template("student_profile.html", student=student, statuses=CLASS_STATUSES)


@app.route("/student/add", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            return render_template("add_student.html", error="Name is required.")
        student_id = _safe_filename(name)
        path = os.path.join(STUDENT_DIR, f"{student_id}.json")
        if os.path.isfile(path):
            return render_template("add_student.html", error="A student with that name already exists.")
        _save_json(path, {"id": student_id, "name": name, "career": []})
        return redirect(url_for("student_profile", student_id=student_id))
    return render_template("add_student.html", error=None)


@app.route("/student/<student_id>/career/update", methods=["POST"])
def update_student_career(student_id):
    path = os.path.join(STUDENT_DIR, f"{student_id}.json")
    if not os.path.isfile(path):
        abort(404)
    student = _load_json(path)
    class_id = request.form.get("class_id", "").strip()
    new_status = request.form.get("status", "Untaken")
    if new_status not in CLASS_STATUSES:
        abort(400)
    entry = next((c for c in student["career"] if c["class_id"] == class_id), None)
    if entry:
        entry["status"] = new_status
    _save_json(path, student)
    return redirect(url_for("student_profile", student_id=student_id))


@app.route("/student/<student_id>/career/add", methods=["GET", "POST"])
def add_student_class(student_id):
    path = os.path.join(STUDENT_DIR, f"{student_id}.json")
    if not os.path.isfile(path):
        abort(404)
    student = _load_json(path)
    # Collect all classes from all teachers
    all_classes = []
    for teacher in _list_profiles(TEACHER_DIR):
        for cls in teacher.get("classes", []):
            all_classes.append({"id": cls["id"], "name": cls["name"], "teacher": teacher["name"]})
    if request.method == "POST":
        class_id = request.form.get("class_id", "").strip()
        class_name = request.form.get("class_name", "").strip()
        if not class_id or not class_name:
            return render_template("add_student_class.html", student=student, all_classes=all_classes, statuses=CLASS_STATUSES, error="Class info required.")
        # Prevent duplicates
        if any(c["class_id"] == class_id for c in student["career"]):
            return render_template("add_student_class.html", student=student, all_classes=all_classes, statuses=CLASS_STATUSES, error="Class already in career.")
        status = request.form.get("status", "Untaken")
        if status not in CLASS_STATUSES:
            status = "Untaken"
        student["career"].append({"class_id": class_id, "class_name": class_name, "status": status})
        _save_json(path, student)
        return redirect(url_for("student_profile", student_id=student_id))
    return render_template("add_student_class.html", student=student, all_classes=all_classes, statuses=CLASS_STATUSES, error=None)


# ── badges & progression ──────────────────────────────────────────────────────

@app.route("/badges")
def badges():
    data = _load_json(BADGES_FILE)
    progression = _load_json(PROGRESSION_FILE)
    req_map = {r["badge_id"]: r["description"] for r in progression.get("requirements", [])}
    for badge in data.get("badges", []):
        badge["requirement"] = req_map.get(badge["id"], "")
    return render_template("badges.html", badges=data.get("badges", []))


@app.route("/badge/<badge_id>/toggle", methods=["POST"])
def toggle_badge(badge_id):
    data = _load_json(BADGES_FILE)
    for badge in data.get("badges", []):
        if badge["id"] == badge_id:
            badge["achieved"] = not badge.get("achieved", False)
            break
    _save_json(BADGES_FILE, data)
    return redirect(url_for("badges"))


@app.route("/progression")
def progression():
    data = _load_json(PROGRESSION_FILE)
    badges_data = _load_json(BADGES_FILE)
    badge_map = {b["id"]: b for b in badges_data.get("badges", [])}
    requirements = data.get("requirements", [])
    for req in requirements:
        req["badge"] = badge_map.get(req["badge_id"], {})
    return render_template("progression.html", requirements=requirements)


# ── API (JSON) ────────────────────────────────────────────────────────────────

@app.route("/api/teachers")
def api_teachers():
    return jsonify(_list_profiles(TEACHER_DIR))


@app.route("/api/students")
def api_students():
    return jsonify(_list_profiles(STUDENT_DIR))


@app.route("/api/badges")
def api_badges():
    return jsonify(_load_json(BADGES_FILE))


@app.route("/api/progression")
def api_progression():
    return jsonify(_load_json(PROGRESSION_FILE))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
