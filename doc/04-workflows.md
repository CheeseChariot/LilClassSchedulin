# Workflows

## Teacher workflow

1. Open `/teachers`.
2. Create a teacher from `/teacher/add`.
3. Open teacher profile.
4. Add classes with `/teacher/<teacher_id>/class/add`.
5. Edit each class schedule from `/teacher/<teacher_id>/class/<class_id>/schedule`.

## Student workflow

1. Open `/students`.
2. Create a student from `/student/add`.
3. Open student profile.
4. Add classes to career from `/student/<student_id>/career/add`.
5. Update status from student profile table.

When student status changes, kardex is synchronized automatically.

## Kardex workflow

1. Open `/student/<student_id>/kardex`.
2. Review totals and status breakdown.
3. Edit per-class fields: grade, period, notes.
4. Save updates.

## Classroom workflow

1. Open `/classrooms`.
2. Add classroom from `/classroom/add`.
3. Edit details from `/classroom/<classroom_id>/edit`.

## Badge and progression workflow

1. Open `/badges` to toggle achieved state.
2. Open `/progression` to see requirement list with achieved indicator.

## Data consistency notes

- Student career is authoritative for class status.
- Kardex keeps additional details per class while status mirrors career.
- Teacher classes and student career classes are linked by `class_id`.
