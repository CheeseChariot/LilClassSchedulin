import json
import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, abort

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
TEACHER_DIR = os.path.join(DATA_DIR, "teacher")
STUDENT_DIR = os.path.join(DATA_DIR, "student")
KARDEX_DIR = os.path.join(DATA_DIR, "kardex")
CLASSROOM_DIR = os.path.join(DATA_DIR, "classroom")
BADGES_FILE = os.path.join(DATA_DIR, "badges.json")
PROGRESSION_FILE = os.path.join(DATA_DIR, "progression.json")
COURSES_FILE = os.path.join(DATA_DIR, "courses.json")
SCHEDBLOCKS_FILE = os.path.join(DATA_DIR, "scheblocks.json")
SCHEDULES_DIR = os.path.join(DATA_DIR, "schedules")

CLASS_STATUSES = ["Untaken", "Pass", "Fail", "Retry", "Force", "Taken"]
CURRENT_SCHEDULE_SEMESTER = "2026_1"
DEFAULT_SCHEDULE_GROUP = "group_1"
WEEK_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

# Source of truth for schedule blocks is data/scheblocks.json.


def _default_badges_data() -> dict:
    return {
        "badges": [
            {
                "id": "first_pass",
                "name": "First Pass",
                "description": "Pass your first class",
                "achieved": False,
            },
            {
                "id": "honor_roll",
                "name": "Honor Roll",
                "description": "Pass 5 classes with distinction",
                "achieved": False,
            },
            {
                "id": "perfect_semester",
                "name": "Perfect Semester",
                "description": "Pass all classes in a single semester without retries",
                "achieved": False,
            },
        ]
    }


def _default_progression_data() -> dict:
    return {
        "requirements": [
            {
                "badge_id": "first_pass",
                "description": "Pass at least 1 class",
            },
            {
                "badge_id": "honor_roll",
                "description": "Accumulate 5 passed classes",
            },
            {
                "badge_id": "perfect_semester",
                "description": "Complete a full semester (all classes passed, none retried)",
            },
        ]
    }


def _default_courses_data() -> dict:
    return {
        "program_name": "Ingenieria Civil en Computacion e Informatica",
        "plan_year": 2020,
        "source": "General course metadata catalog (no student performance data).",
        "courses": [],
    }


def _default_scheblocks_data() -> dict:
    return {
        "blocks": [],
    }


def _default_semester_schedule(semester: str) -> dict:
    return {
        "semester": semester,
        "default_group": DEFAULT_SCHEDULE_GROUP,
        "university": None,
        "program": None,
        "plans": [],
        "classes": [],
    }


def _parse_optional_int(value):
    """Return int from string/number, or None if blank/invalid."""
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_optional_float(value):
    """Return float from string/number, or None if blank/invalid."""
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_text(value, default="") -> str:
    if value is None:
        return default
    return str(value).strip() or default


def _normalize_teacher(data: dict, fallback_id: str) -> dict:
    teacher_id = _safe_filename(_coerce_text(data.get("id"))) or _safe_filename(fallback_id) or fallback_id
    name = _coerce_text(data.get("name"), teacher_id.replace("_", " ").title())
    raw_classes = data.get("classes")
    if not isinstance(raw_classes, list):
        raw_classes = []

    classes = []
    seen_ids = set()
    for cls in raw_classes:
        if not isinstance(cls, dict):
            continue
        class_name = _coerce_text(cls.get("name"))
        class_id = _safe_filename(_coerce_text(cls.get("id")) or class_name)
        if not class_id or class_id in seen_ids:
            continue
        seen_ids.add(class_id)

        classes.append({"id": class_id, "name": class_name or class_id})

    return {"id": teacher_id, "name": name, "classes": classes}


def _normalize_student(data: dict, fallback_id: str) -> dict:
    student_id = _safe_filename(_coerce_text(data.get("id"))) or _safe_filename(fallback_id) or fallback_id
    name = _coerce_text(data.get("name"), student_id.replace("_", " ").title())
    raw_career = data.get("career")
    if not isinstance(raw_career, list):
        raw_career = []

    career = []
    seen_ids = set()
    for entry in raw_career:
        if not isinstance(entry, dict):
            continue
        class_name = _coerce_text(entry.get("class_name"))
        class_id = _safe_filename(_coerce_text(entry.get("class_id")) or class_name)
        if not class_id or class_id in seen_ids:
            continue
        seen_ids.add(class_id)
        status = _coerce_text(entry.get("status"), "Untaken")
        if status not in CLASS_STATUSES:
            status = "Untaken"
        career.append(
            {
                "class_id": class_id,
                "class_name": class_name or class_id,
                "status": status,
            }
        )

    return {"id": student_id, "name": name, "career": career}


def _normalize_classroom(data: dict, fallback_id: str) -> dict:
    room_id = _safe_filename(_coerce_text(data.get("id"))) or _safe_filename(fallback_id) or fallback_id
    default_name = room_id.replace("_", " ").title()
    return {
        "id": room_id,
        "name": _coerce_text(data.get("name"), default_name),
        "location_guide": _coerce_text(data.get("location_guide")),
        "capabilities": _coerce_text(data.get("capabilities")),
        "space_sqm": _parse_optional_float(data.get("space_sqm")),
        "chairs": _parse_optional_int(data.get("chairs")),
        "description": _coerce_text(data.get("description")),
    }


def _normalize_badges(data) -> dict:
    raw_badges = data.get("badges") if isinstance(data, dict) else None
    if not isinstance(raw_badges, list):
        raw_badges = _default_badges_data()["badges"]

    badges = []
    seen_ids = set()
    for badge in raw_badges:
        if not isinstance(badge, dict):
            continue
        badge_id = _safe_filename(_coerce_text(badge.get("id")))
        if not badge_id or badge_id in seen_ids:
            continue
        seen_ids.add(badge_id)
        badges.append(
            {
                "id": badge_id,
                "name": _coerce_text(badge.get("name"), badge_id.replace("_", " ").title()),
                "description": _coerce_text(badge.get("description")),
                "achieved": bool(badge.get("achieved", False)),
            }
        )

    return {"badges": badges}


def _normalize_progression(data) -> dict:
    raw_requirements = data.get("requirements") if isinstance(data, dict) else None
    if not isinstance(raw_requirements, list):
        raw_requirements = _default_progression_data()["requirements"]

    requirements = []
    for req in raw_requirements:
        if not isinstance(req, dict):
            continue
        badge_id = _safe_filename(_coerce_text(req.get("badge_id")))
        if not badge_id:
            continue
        requirements.append(
            {
                "badge_id": badge_id,
                "description": _coerce_text(req.get("description")),
            }
        )

    return {"requirements": requirements}


def _normalize_courses(data) -> dict:
    if not isinstance(data, dict):
        data = {}

    raw_courses = data.get("courses")
    if not isinstance(raw_courses, list):
        raw_courses = []

    courses = []
    seen_ids = set()
    for course in raw_courses:
        if not isinstance(course, dict):
            continue

        course_name = _coerce_text(course.get("course_name") or course.get("name") or course.get("class_name"))
        course_id = _safe_filename(_coerce_text(course.get("course_id") or course.get("id")) or course_name)
        if not course_id or course_id in seen_ids:
            continue
        seen_ids.add(course_id)

        duration = _coerce_text(course.get("duration"), "S").upper()
        if duration not in {"S", "A", "CV", "EE"}:
            duration = "S"

        legacy_year = _parse_optional_int(course.get("year"))
        semester = _parse_optional_int(course.get("semester"))
        if legacy_year is not None and semester is not None:
            semester = ((legacy_year - 1) * 2) + semester

        courses.append(
            {
                "course_id": course_id,
                "course_name": course_name or course_id,
                "semester": semester,
                "hp": _parse_optional_float(course.get("hp")),
                "hnp": _parse_optional_float(course.get("hnp")),
                "ct": _parse_optional_int(course.get("ct")),
                "duration": duration,
            }
        )

    courses.sort(
        key=lambda c: (
            c.get("semester") if c.get("semester") is not None else 99,
            c.get("course_name", "").lower(),
        )
    )

    return {
        "program_name": _coerce_text(data.get("program_name"), "Course Catalog"),
        "plan_year": _parse_optional_int(data.get("plan_year")),
        "source": _coerce_text(data.get("source")),
        "courses": courses,
    }


def _normalize_scheblocks(data) -> dict:
    if not isinstance(data, dict):
        data = {}

    raw_blocks = data.get("blocks")
    if not isinstance(raw_blocks, list):
        raw_blocks = []

    blocks = []
    seen_ids = set()
    for i, block in enumerate(raw_blocks, start=1):
        if not isinstance(block, dict):
            continue

        time_range = _coerce_text(block.get("time"))
        if not time_range:
            continue

        block_id = _safe_filename(_coerce_text(block.get("id"))) or f"b{i}"
        if block_id in seen_ids:
            continue
        seen_ids.add(block_id)

        label = _coerce_text(block.get("label"), f"Block {len(blocks) + 1}")
        blocks.append(
            {
                "id": block_id,
                "label": label,
                "time": time_range,
            }
        )

    return {"blocks": blocks}


def _normalize_semester_schedule(data, semester: str) -> dict:
    if not isinstance(data, dict):
        data = {}

    sem_id = _safe_filename(_coerce_text(semester, CURRENT_SCHEDULE_SEMESTER)) or CURRENT_SCHEDULE_SEMESTER
    default_group = _safe_filename(_coerce_text(data.get("default_group"), DEFAULT_SCHEDULE_GROUP))
    if not default_group:
        default_group = DEFAULT_SCHEDULE_GROUP

    university = _coerce_text(data.get("university")) or None
    program = _coerce_text(data.get("program")) or None
    raw_plans = data.get("plans")
    if not isinstance(raw_plans, list):
        raw_plans = []
    plans = []
    seen_plans = set()
    for plan_ref in raw_plans:
        plan_id = _safe_filename(_coerce_text(plan_ref))
        if not plan_id or plan_id in seen_plans:
            continue
        seen_plans.add(plan_id)
        plans.append(plan_id)

    raw_classes = data.get("classes")
    if not isinstance(raw_classes, list):
        raw_classes = []

    classes = []
    seen_class_ids = set()
    for schedule_class in raw_classes:
        if not isinstance(schedule_class, dict):
            continue

        class_name = _coerce_text(schedule_class.get("class_name") or schedule_class.get("name"))
        class_id = _safe_filename(_coerce_text(schedule_class.get("class_id") or schedule_class.get("id")) or class_name)
        plan = _safe_filename(_coerce_text(schedule_class.get("plan"))) or None
        academic_semester = _parse_optional_int(schedule_class.get("academic_semester"))
        if not class_id or class_id in seen_class_ids:
            continue
        seen_class_ids.add(class_id)

        teacher_ids = []
        seen_teacher_ids = set()
        raw_teacher_ids = schedule_class.get("teacher_ids")
        if not isinstance(raw_teacher_ids, list):
            raw_teacher_ids = schedule_class.get("teachers") if isinstance(schedule_class.get("teachers"), list) else []
        for teacher_ref in raw_teacher_ids:
            if isinstance(teacher_ref, dict):
                teacher_id = _safe_filename(_coerce_text(teacher_ref.get("teacher_id") or teacher_ref.get("id")))
            else:
                teacher_id = _safe_filename(_coerce_text(teacher_ref))
            if not teacher_id or teacher_id in seen_teacher_ids:
                continue
            seen_teacher_ids.add(teacher_id)
            teacher_ids.append(teacher_id)

        raw_times = schedule_class.get("times")
        if not isinstance(raw_times, list):
            raw_times = []

        times = []
        for slot in raw_times:
            if not isinstance(slot, dict):
                continue
            day = _coerce_text(slot.get("day")).lower()
            if day not in WEEK_DAYS:
                continue
            raw_group = slot.get("group") if "group" in slot else default_group
            group = _safe_filename(_coerce_text(raw_group)) or None
            block = _coerce_text(slot.get("block"), "custom") or "custom"
            normalized_slot = {
                "day": day,
                "block": block,
                "group": group,
            }
            room = _safe_filename(_coerce_text(slot.get("room"))) or None
            tipo = _coerce_text(slot.get("tipo")) or None
            time_value = _coerce_text(slot.get("time"))
            time_raw = _coerce_text(slot.get("time_raw"))
            if time_value:
                normalized_slot["time"] = time_value
            elif time_raw:
                normalized_slot["time_raw"] = time_raw
            if "room" in slot or room is not None:
                normalized_slot["room"] = room
            if "tipo" in slot or tipo is not None:
                normalized_slot["tipo"] = tipo
            times.append(normalized_slot)

        classes.append(
            {
                "class_id": class_id,
                "class_name": class_name or class_id,
                "plan": plan,
                "academic_semester": academic_semester,
                "teacher_ids": teacher_ids,
                "status": _coerce_text(schedule_class.get("status"), "") or None,
                "times": times,
            }
        )

    classes.sort(
        key=lambda c: (
            c.get("plan") or "zzz",
            c.get("academic_semester") if c.get("academic_semester") is not None else 999,
            c.get("class_name", "").lower(),
        )
    )

    return {
        "semester": _coerce_text(data.get("semester"), sem_id) or sem_id,
        "default_group": default_group,
        "university": university,
        "program": program,
        "plans": plans,
        "classes": classes,
    }


def _find_schedule_class(schedule_data: dict, class_id: str):
    for schedule_class in schedule_data.get("classes", []):
        if schedule_class.get("class_id") == class_id:
            return schedule_class
    return None


def _ensure_schedule_class(schedule_data: dict, class_id: str, class_name: str):
    schedule_class = _find_schedule_class(schedule_data, class_id)
    if schedule_class is None:
        schedule_class = {
            "class_id": class_id,
            "class_name": class_name or class_id,
            "plan": None,
            "academic_semester": None,
            "teacher_ids": [],
            "status": None,
            "times": [],
        }
        schedule_data.setdefault("classes", []).append(schedule_class)
    elif class_name:
        schedule_class["class_name"] = class_name
    return schedule_class


def _schedule_day_map(schedule_class: dict, group: str) -> dict:
    day_map = {}
    raw_times = schedule_class.get("times")
    if not isinstance(raw_times, list):
        return day_map

    for slot in raw_times:
        if not isinstance(slot, dict):
            continue
        if _coerce_text(slot.get("group"), group) != group:
            continue
        day = _coerce_text(slot.get("day")).lower()
        if day not in WEEK_DAYS:
            continue
        time_value = _coerce_text(slot.get("time")) or _coerce_text(slot.get("time_raw"))
        if time_value:
            day_map[day] = time_value
    return day_map


def _replace_schedule_group_times(schedule_class: dict, group: str, day_to_time: dict, block_by_time: dict):
    raw_times = schedule_class.get("times")
    if not isinstance(raw_times, list):
        raw_times = []

    kept = []
    for slot in raw_times:
        if not isinstance(slot, dict):
            continue
        if _coerce_text(slot.get("group"), group) == group:
            continue
        kept.append(slot)

    for day in WEEK_DAYS:
        time_value = _coerce_text(day_to_time.get(day))
        if not time_value:
            continue
        block = block_by_time.get(time_value)
        if block:
            kept.append(
                {
                    "day": day,
                    "block": block.get("id"),
                    "group": group,
                    "time": block.get("time"),
                }
            )
        else:
            kept.append(
                {
                    "day": day,
                    "block": "custom",
                    "group": group,
                    "time_raw": time_value,
                }
            )

    schedule_class["times"] = kept


def _normalizer_for_directory(directory: str):
    if os.path.normpath(directory) == os.path.normpath(TEACHER_DIR):
        return _normalize_teacher
    if os.path.normpath(directory) == os.path.normpath(STUDENT_DIR):
        return _normalize_student
    if os.path.normpath(directory) == os.path.normpath(CLASSROOM_DIR):
        return _normalize_classroom
    return None


# ── helpers ──────────────────────────────────────────────────────────────────

def _load_json(path):
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def _load_scheblocks() -> list[dict]:
    return _normalize_scheblocks(_load_json(SCHEDBLOCKS_FILE)).get("blocks", [])


def _schedule_path(semester: str = CURRENT_SCHEDULE_SEMESTER) -> str:
    sem_id = _safe_filename(_coerce_text(semester, CURRENT_SCHEDULE_SEMESTER)) or CURRENT_SCHEDULE_SEMESTER
    return os.path.join(SCHEDULES_DIR, f"{sem_id}.json")


def _load_semester_schedule(semester: str = CURRENT_SCHEDULE_SEMESTER) -> dict:
    sem_id = _safe_filename(_coerce_text(semester, CURRENT_SCHEDULE_SEMESTER)) or CURRENT_SCHEDULE_SEMESTER
    return _normalize_semester_schedule(_load_json(_schedule_path(sem_id)), sem_id)


def _save_semester_schedule(schedule_data: dict, semester: str = CURRENT_SCHEDULE_SEMESTER) -> dict:
    sem_id = _safe_filename(_coerce_text(semester, CURRENT_SCHEDULE_SEMESTER)) or CURRENT_SCHEDULE_SEMESTER
    normalized = _normalize_semester_schedule(schedule_data, sem_id)
    _save_json(_schedule_path(sem_id), normalized)
    return normalized


def _scheblock_map(blocks: list[dict]) -> dict:
    return {block["time"]: block for block in blocks if block.get("time")}


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

    normalizer = _normalizer_for_directory(directory)
    profiles = []
    for fname in sorted(os.listdir(directory)):
        if fname.endswith(".json"):
            fpath = os.path.join(directory, fname)
            profile = _load_json(fpath)
            if not isinstance(profile, dict):
                profile = {}
            if normalizer:
                fallback_id = os.path.splitext(fname)[0]
                profile = normalizer(profile, fallback_id)
            if profile:
                profiles.append(profile)
    return profiles


def _ensure_data_layout() -> None:
    for folder in [DATA_DIR, TEACHER_DIR, STUDENT_DIR, KARDEX_DIR, CLASSROOM_DIR, SCHEDULES_DIR]:
        os.makedirs(folder, exist_ok=True)

    badges_data = _load_json(BADGES_FILE)
    if not isinstance(badges_data, dict) or not isinstance(badges_data.get("badges"), list):
        _save_json(BADGES_FILE, _default_badges_data())

    progression_data = _load_json(PROGRESSION_FILE)
    if not isinstance(progression_data, dict) or not isinstance(progression_data.get("requirements"), list):
        _save_json(PROGRESSION_FILE, _default_progression_data())

    courses_data = _load_json(COURSES_FILE)
    if not isinstance(courses_data, dict) or not isinstance(courses_data.get("courses"), list):
        _save_json(COURSES_FILE, _default_courses_data())

    scheblocks_data = _load_json(SCHEDBLOCKS_FILE)
    if not isinstance(scheblocks_data, dict) or not isinstance(scheblocks_data.get("blocks"), list):
        _save_json(SCHEDBLOCKS_FILE, _default_scheblocks_data())

    semester_path = _schedule_path(CURRENT_SCHEDULE_SEMESTER)
    semester_data = _load_json(semester_path)
    if not isinstance(semester_data, dict) or not isinstance(semester_data.get("classes"), list):
        _save_json(semester_path, _default_semester_schedule(CURRENT_SCHEDULE_SEMESTER))
    else:
        normalized_semester = _normalize_semester_schedule(semester_data, CURRENT_SCHEDULE_SEMESTER)
        if normalized_semester != semester_data:
            _save_json(semester_path, normalized_semester)


# ── kardex helpers ───────────────────────────────────────────────────────────

def _kardex_path(student_id: str) -> str:
    return os.path.join(KARDEX_DIR, f"{student_id}.json")


def _init_kardex(student_id: str, student_name: str) -> None:
    """Create a blank kardex JSON for a brand-new student."""
    path = _kardex_path(student_id)
    if not os.path.isfile(path):
        _save_json(path, {
            "student_id": student_id,
            "student_name": student_name,
            "entries": [],
        })


def _normalize_kardex(data, student: dict) -> dict:
    if not isinstance(data, dict):
        data = {}

    entries = []
    entry_map = {}
    raw_entries = data.get("entries")
    if not isinstance(raw_entries, list):
        raw_entries = []

    for entry in raw_entries:
        if not isinstance(entry, dict):
            continue
        class_id = _safe_filename(_coerce_text(entry.get("class_id")))
        if not class_id:
            continue
        status = _coerce_text(entry.get("status"), "Untaken")
        if status not in CLASS_STATUSES:
            status = "Untaken"
        normalized = {
            "class_id": class_id,
            "class_name": _coerce_text(entry.get("class_name"), class_id),
            "status": status,
            "grade": _parse_optional_float(entry.get("grade")),
            "period": _coerce_text(entry.get("period"), "") or None,
            "notes": _coerce_text(entry.get("notes")),
        }
        entry_map[class_id] = normalized

    for career_entry in student.get("career", []):
        class_id = career_entry["class_id"]
        status = career_entry["status"]
        class_name = career_entry["class_name"]
        if class_id in entry_map:
            entry_map[class_id]["status"] = status
            entry_map[class_id]["class_name"] = class_name or entry_map[class_id]["class_name"]
        else:
            entry_map[class_id] = {
                "class_id": class_id,
                "class_name": class_name,
                "status": status,
                "grade": None,
                "period": None,
                "notes": "",
            }

    for entry in entry_map.values():
        entries.append(entry)

    return {
        "student_id": student["id"],
        "student_name": student["name"],
        "entries": entries,
    }


def _sync_kardex(student: dict) -> None:
    """Keep the kardex in sync with the student's career list.

    * Adds an entry for any career class not yet in the kardex.
    * Updates the status field to match the career (single source of truth).
    * Never removes entries — historical records are preserved.
    """
    path = _kardex_path(student["id"])
    kardex = _normalize_kardex(_load_json(path), student)
    _save_json(path, kardex)


_ensure_data_layout()


# ── views ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    teachers = _list_profiles(TEACHER_DIR)
    students = _list_profiles(STUDENT_DIR)
    classrooms = _list_profiles(CLASSROOM_DIR)
    courses_count = len(_normalize_courses(_load_json(COURSES_FILE)).get("courses", []))
    badges = _normalize_badges(_load_json(BADGES_FILE)).get("badges", [])
    achieved = sum(1 for b in badges if b.get("achieved"))
    return render_template(
        "index.html",
        teachers=teachers,
        students=students,
        classrooms=classrooms,
        courses_count=courses_count,
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
    teacher = _normalize_teacher(_load_json(path), teacher_id)
    blocks = _load_scheblocks()
    schedule_data = _load_semester_schedule()
    default_group = _coerce_text(schedule_data.get("default_group"), DEFAULT_SCHEDULE_GROUP) or DEFAULT_SCHEDULE_GROUP

    teacher_ref = teacher.get("id")
    for cls in teacher.get("classes", []):
        cls["schedule"] = None
        cls["status"] = None
        schedule_class = _find_schedule_class(schedule_data, cls.get("id"))
        if not schedule_class:
            continue
        if teacher_ref not in schedule_class.get("teacher_ids", []):
            continue
        cls["schedule"] = _schedule_day_map(schedule_class, default_group) or None
        cls["status"] = schedule_class.get("status")

    return render_template("teacher_profile.html", teacher=teacher, block_map=_scheblock_map(blocks))


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
    teacher = _normalize_teacher(_load_json(path), teacher_id)
    if request.method == "POST":
        class_name = request.form.get("class_name", "").strip()
        if not class_name:
            return render_template("add_class.html", teacher=teacher, error="Class name is required.")
        class_id = _safe_filename(class_name)
        if any(existing.get("id") == class_id for existing in teacher.get("classes", [])):
            return render_template(
                "add_class.html",
                teacher=teacher,
                error="A class with that name already exists for this teacher.",
            )
        new_class = {"id": class_id, "name": class_name}
        teacher.setdefault("classes", []).append(new_class)
        _save_json(path, teacher)
        return redirect(url_for("teacher_profile", teacher_id=teacher_id))
    return render_template("add_class.html", teacher=teacher, error=None)


@app.route("/teacher/<teacher_id>/class/<class_id>/schedule", methods=["GET", "POST"])
def edit_schedule(teacher_id, class_id):
    path = os.path.join(TEACHER_DIR, f"{teacher_id}.json")
    if not os.path.isfile(path):
        abort(404)
    teacher = _normalize_teacher(_load_json(path), teacher_id)
    cls = next((c for c in teacher.get("classes", []) if c.get("id") == class_id), None)
    if cls is None:
        abort(404)

    schedule_data = _load_semester_schedule()
    default_group = _coerce_text(schedule_data.get("default_group"), DEFAULT_SCHEDULE_GROUP) or DEFAULT_SCHEDULE_GROUP
    schedule_class = _ensure_schedule_class(schedule_data, class_id, cls.get("name"))

    teacher_ref = teacher.get("id")
    if teacher_ref and teacher_ref not in schedule_class.get("teacher_ids", []):
        schedule_class.setdefault("teacher_ids", []).append(teacher_ref)

    blocks = _load_scheblocks()
    block_by_time = _scheblock_map(blocks)
    valid_times = set(block_by_time.keys())
    days = WEEK_DAYS

    cls_view = {
        "id": cls.get("id"),
        "name": cls.get("name"),
        "schedule": _schedule_day_map(schedule_class, default_group) or None,
        "status": schedule_class.get("status"),
    }

    if request.method == "POST":
        day_to_time = {}
        for day in days:
            val = request.form.get(day, "").strip()
            if val and (not valid_times or val in valid_times):
                day_to_time[day] = val

        _replace_schedule_group_times(schedule_class, default_group, day_to_time, block_by_time)
        schedule_class["status"] = request.form.get("status", "").strip() or None
        _save_semester_schedule(schedule_data)
        return redirect(url_for("teacher_profile", teacher_id=teacher_id))

    return render_template("edit_schedule.html", teacher=teacher, cls=cls_view, days=days, blocks=blocks)


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
    student = _normalize_student(_load_json(path), student_id)
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
        _init_kardex(student_id, name)
        return redirect(url_for("student_profile", student_id=student_id))
    return render_template("add_student.html", error=None)


@app.route("/student/<student_id>/career/update", methods=["POST"])
def update_student_career(student_id):
    path = os.path.join(STUDENT_DIR, f"{student_id}.json")
    if not os.path.isfile(path):
        abort(404)
    student = _normalize_student(_load_json(path), student_id)
    class_id = request.form.get("class_id", "").strip()
    if not class_id:
        abort(400)
    new_status = request.form.get("status", "Untaken")
    if new_status not in CLASS_STATUSES:
        abort(400)
    entry = next((c for c in student.get("career", []) if c.get("class_id") == class_id), None)
    if entry is None:
        abort(404)
    entry["status"] = new_status
    _save_json(path, student)
    _sync_kardex(student)
    return redirect(url_for("student_profile", student_id=student_id))


@app.route("/student/<student_id>/career/add", methods=["GET", "POST"])
def add_student_class(student_id):
    path = os.path.join(STUDENT_DIR, f"{student_id}.json")
    if not os.path.isfile(path):
        abort(404)
    student = _normalize_student(_load_json(path), student_id)
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
        class_id = _safe_filename(class_id)
        if not class_id:
            return render_template("add_student_class.html", student=student, all_classes=all_classes, statuses=CLASS_STATUSES, error="Class ID is invalid.")
        # Prevent duplicates
        if any(c.get("class_id") == class_id for c in student.get("career", [])):
            return render_template("add_student_class.html", student=student, all_classes=all_classes, statuses=CLASS_STATUSES, error="Class already in career.")
        status = request.form.get("status", "Untaken")
        if status not in CLASS_STATUSES:
            status = "Untaken"
        student["career"].append({"class_id": class_id, "class_name": class_name, "status": status})
        _save_json(path, student)
        _sync_kardex(student)
        return redirect(url_for("student_profile", student_id=student_id))
    return render_template("add_student_class.html", student=student, all_classes=all_classes, statuses=CLASS_STATUSES, error=None)


# ── kardex ────────────────────────────────────────────────────────────────────

@app.route("/student/<student_id>/kardex")
def student_kardex(student_id):
    student_path = os.path.join(STUDENT_DIR, f"{student_id}.json")
    if not os.path.isfile(student_path):
        abort(404)
    student = _normalize_student(_load_json(student_path), student_id)
    kardex_path = _kardex_path(student_id)
    if not os.path.isfile(kardex_path):
        _init_kardex(student_id, student["name"])
    kardex = _normalize_kardex(_load_json(kardex_path), student)
    badges = _normalize_badges(_load_json(BADGES_FILE)).get("badges", [])
    achieved_badges = [b for b in badges if b.get("achieved")]
    return render_template(
        "kardex.html",
        student=student,
        kardex=kardex,
        statuses=CLASS_STATUSES,
        achieved_badges=achieved_badges,
    )


@app.route("/student/<student_id>/kardex/update", methods=["POST"])
def update_kardex_entry(student_id):
    student_path = os.path.join(STUDENT_DIR, f"{student_id}.json")
    if not os.path.isfile(student_path):
        abort(404)
    student = _normalize_student(_load_json(student_path), student_id)

    kardex_path = _kardex_path(student_id)
    if not os.path.isfile(kardex_path):
        _init_kardex(student_id, student["name"])
    kardex = _normalize_kardex(_load_json(kardex_path), student)
    class_id = request.form.get("class_id", "").strip()
    if not class_id:
        abort(400)
    entry = next((e for e in kardex.get("entries", []) if e.get("class_id") == class_id), None)
    if entry is None:
        abort(404)
    entry["grade"] = _parse_optional_float(request.form.get("grade", ""))
    entry["period"] = request.form.get("period", "").strip() or None
    entry["notes"] = request.form.get("notes", "").strip()
    _save_json(kardex_path, kardex)
    return redirect(url_for("student_kardex", student_id=student_id))


# ── classrooms ────────────────────────────────────────────────────────────────

@app.route("/classrooms")
def classrooms():
    rooms = _list_profiles(CLASSROOM_DIR)
    return render_template("classrooms.html", classrooms=rooms)


@app.route("/courses")
def courses_catalog():
    catalog = _normalize_courses(_load_json(COURSES_FILE))

    groups = []
    current_semester = None
    for course in catalog.get("courses", []):
        semester = course.get("semester")
        if semester != current_semester:
            groups.append({"semester": semester, "courses": []})
            current_semester = semester
        groups[-1]["courses"].append(course)

    return render_template("courses.html", catalog=catalog, groups=groups)


@app.route("/classroom/<classroom_id>")
def classroom_profile(classroom_id):
    path = os.path.join(CLASSROOM_DIR, f"{classroom_id}.json")
    if not os.path.isfile(path):
        abort(404)
    room = _normalize_classroom(_load_json(path), classroom_id)
    return render_template("classroom_profile.html", room=room)


@app.route("/classroom/add", methods=["GET", "POST"])
def add_classroom():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            return render_template("add_classroom.html", error="Name is required.")
        classroom_id = _safe_filename(name)
        path = os.path.join(CLASSROOM_DIR, f"{classroom_id}.json")
        if os.path.isfile(path):
            return render_template("add_classroom.html", error="A classroom with that name already exists.")
        raw_chairs = request.form.get("chairs", "").strip()
        raw_space = request.form.get("space_sqm", "").strip()
        _save_json(path, {
            "id": classroom_id,
            "name": name,
            "location_guide": request.form.get("location_guide", "").strip(),
            "capabilities": request.form.get("capabilities", "").strip(),
            "space_sqm": _parse_optional_float(raw_space),
            "chairs": _parse_optional_int(raw_chairs),
            "description": request.form.get("description", "").strip(),
        })
        return redirect(url_for("classroom_profile", classroom_id=classroom_id))
    return render_template("add_classroom.html", error=None)


@app.route("/classroom/<classroom_id>/edit", methods=["GET", "POST"])
def edit_classroom(classroom_id):
    path = os.path.join(CLASSROOM_DIR, f"{classroom_id}.json")
    if not os.path.isfile(path):
        abort(404)
    room = _normalize_classroom(_load_json(path), classroom_id)
    if request.method == "POST":
        room["chairs"] = _parse_optional_int(request.form.get("chairs", ""))
        room["space_sqm"] = _parse_optional_float(request.form.get("space_sqm", ""))
        room["location_guide"] = request.form.get("location_guide", "").strip()
        room["capabilities"] = request.form.get("capabilities", "").strip()
        room["description"] = request.form.get("description", "").strip()
        _save_json(path, room)
        return redirect(url_for("classroom_profile", classroom_id=classroom_id))
    return render_template("edit_classroom.html", room=room)


# ── badges & progression ──────────────────────────────────────────────────────

@app.route("/badges")
def badges():
    data = _normalize_badges(_load_json(BADGES_FILE))
    progression = _normalize_progression(_load_json(PROGRESSION_FILE))
    req_map = {r.get("badge_id"): r.get("description", "") for r in progression.get("requirements", [])}
    for badge in data.get("badges", []):
        badge["requirement"] = req_map.get(badge.get("id"), "")
    return render_template("badges.html", badges=data.get("badges", []))


@app.route("/badge/<badge_id>/toggle", methods=["POST"])
def toggle_badge(badge_id):
    data = _normalize_badges(_load_json(BADGES_FILE))
    for badge in data.get("badges", []):
        if badge.get("id") == badge_id:
            badge["achieved"] = not badge.get("achieved", False)
            break
    _save_json(BADGES_FILE, data)
    return redirect(url_for("badges"))


@app.route("/progression")
def progression():
    data = _normalize_progression(_load_json(PROGRESSION_FILE))
    badges_data = _normalize_badges(_load_json(BADGES_FILE))
    badge_map = {b.get("id"): b for b in badges_data.get("badges", []) if b.get("id")}
    requirements = data.get("requirements", [])
    for req in requirements:
        req["badge"] = badge_map.get(req.get("badge_id"), {})
    return render_template("progression.html", requirements=requirements)


# ── API (JSON) ────────────────────────────────────────────────────────────────

@app.route("/api/teachers")
def api_teachers():
    return jsonify(_list_profiles(TEACHER_DIR))


@app.route("/api/students")
def api_students():
    return jsonify(_list_profiles(STUDENT_DIR))


@app.route("/api/student/<student_id>/kardex")
def api_student_kardex(student_id):
    student_path = os.path.join(STUDENT_DIR, f"{student_id}.json")
    if not os.path.isfile(student_path):
        abort(404)
    student = _normalize_student(_load_json(student_path), student_id)

    kardex_path = _kardex_path(student_id)
    if not os.path.isfile(kardex_path):
        _init_kardex(student_id, student["name"])
    kardex = _normalize_kardex(_load_json(kardex_path), student)
    return jsonify(kardex)


@app.route("/api/badges")
def api_badges():
    return jsonify(_normalize_badges(_load_json(BADGES_FILE)))


@app.route("/api/progression")
def api_progression():
    return jsonify(_normalize_progression(_load_json(PROGRESSION_FILE)))


@app.route("/api/courses")
def api_courses():
    return jsonify(_normalize_courses(_load_json(COURSES_FILE)))


@app.route("/api/classrooms")
def api_classrooms():
    return jsonify(_list_profiles(CLASSROOM_DIR))


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug, port=5000)
