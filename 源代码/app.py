from __future__ import annotations

from datetime import datetime
from io import BytesIO
from inspect import signature

from compat import patch_flask_jinja_compat

patch_flask_jinja_compat()

from flask import Flask, abort, flash, redirect, render_template, request, send_file, session, url_for
from openpyxl import Workbook

from config import Config
from extensions import Base, db
from hr_rules import (
    COURSE_NATURES,
    EMPLOYEE_STATUSES,
    GENDER_OPTIONS,
    PUBLICATION_TYPES,
    RESEARCH_STATUSES,
    PUNISHMENT_RULES,
    REWARD_RULES,
    SALARY_GRADE_OPTIONS,
    SALARY_RULES,
    estimate_monthly_salary,
    format_currency,
    get_salary_rule,
)
from models import Course, Department, Employee, Patent, Publication, ResearchProject, TeachingAssignment, User
from seed_data import seed_database
from utils import get_current_user, login_required, parse_date, role_required


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        Base.metadata.create_all(bind=Base.metadata.bind)
        seed_database(db)

    register_context(app)
    register_routes(app)
    return app


def register_context(app: Flask) -> None:
    @app.context_processor
    def inject_user():
        return {
            "current_user": get_current_user(),
            "employee_statuses": EMPLOYEE_STATUSES,
            "gender_options": GENDER_OPTIONS,
            "salary_grade_options": SALARY_GRADE_OPTIONS,
            "course_natures": COURSE_NATURES,
            "research_statuses": RESEARCH_STATUSES,
            "publication_types": PUBLICATION_TYPES,
        }


def export_workbook(title: str, headers: list[str], rows: list[list]):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = title
    sheet.append(headers)
    for row in rows:
        sheet.append(row)

    stream = BytesIO()
    workbook.save(stream)
    stream.seek(0)
    return stream


def send_excel_file(stream, filename: str):
    send_file_params = signature(send_file).parameters
    kwargs = {
        "as_attachment": True,
        "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    if "download_name" in send_file_params:
        kwargs["download_name"] = filename
    else:
        kwargs["attachment_filename"] = filename
    return send_file(stream, **kwargs)


def get_or_404(model, object_id: int):
    obj = db.session.get(model, object_id)
    if obj is None:
        abort(404)
    return obj


def touch_record(record) -> None:
    record.updated_at = datetime.utcnow()


def course_scope(user: User):
    if user.role == "admin":
        return Course.query
    return (
        Course.query.join(TeachingAssignment)
        .filter(TeachingAssignment.employee_id == user.employee_id)
        .distinct()
    )


def can_manage_employee(user: User, employee_id: int) -> bool:
    return user.role == "admin" or user.employee_id == employee_id


def employee_scope(user: User):
    query = Employee.query.join(Department)
    if user.role != "admin":
        query = query.filter(Employee.id == user.employee_id)
    return query


def teaching_scope(user: User):
    query = TeachingAssignment.query.join(Employee).join(Course)
    if user.role != "admin":
        query = query.filter(TeachingAssignment.employee_id == user.employee_id)
    return query


def research_scope(user: User):
    project_query = ResearchProject.query.join(Employee)
    patent_query = Patent.query.join(Employee)
    publication_query = Publication.query.join(Employee)
    if user.role != "admin":
        project_query = project_query.filter(ResearchProject.employee_id == user.employee_id)
        patent_query = patent_query.filter(Patent.employee_id == user.employee_id)
        publication_query = publication_query.filter(Publication.employee_id == user.employee_id)
    return project_query, patent_query, publication_query


def employee_form_data(form, *, is_admin: bool) -> dict:
    data = {
        "name": form["name"].strip(),
        "gender": form["gender"],
        "birth_date": parse_date(form.get("birth_date", "")),
        "education": form.get("education", "").strip(),
        "degree": form.get("degree", "").strip(),
        "major": form.get("major", "").strip(),
        "hire_date": parse_date(form.get("hire_date", "")),
        "phone": form.get("phone", "").strip(),
        "email": form.get("email", "").strip(),
        "reward_punishment": form.get("reward_punishment", "").strip(),
        "notes": form.get("notes", "").strip(),
    }
    if is_admin:
        data.update(
            {
                "employee_no": form["employee_no"].strip(),
                "department_id": int(form["department_id"]),
                "title": form.get("title", "").strip(),
                "position": form.get("position", "").strip(),
                "salary_grade": form.get("salary_grade", "").strip(),
                "status": form.get("status", EMPLOYEE_STATUSES[0]),
            }
        )
    return data


def apply_employee_form(employee: Employee, data: dict, *, is_admin: bool) -> None:
    employee.name = data["name"]
    employee.gender = data["gender"]
    employee.birth_date = data["birth_date"]
    employee.education = data["education"]
    employee.degree = data["degree"]
    employee.major = data["major"]
    employee.hire_date = data["hire_date"]
    employee.phone = data["phone"]
    employee.email = data["email"]
    employee.reward_punishment = data["reward_punishment"]
    employee.notes = data["notes"]
    if is_admin:
        employee.employee_no = data["employee_no"]
        employee.department_id = data["department_id"]
        employee.title = data["title"]
        employee.position = data["position"]
        employee.salary_grade = data["salary_grade"]
        employee.status = data["status"]


def register_routes(app: Flask) -> None:
    @app.route("/")
    def index():
        if get_current_user():
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form["username"].strip()
            password = request.form["password"]
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                session["user_id"] = user.id
                flash("登录成功。", "success")
                return redirect(url_for("dashboard"))
            flash("用户名或密码错误。", "danger")
        return render_template("auth/login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("已退出登录。", "info")
        return redirect(url_for("login"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        user = get_current_user()
        current_employee = user.employee
        employee_query = employee_scope(user)
        teaching_query = teaching_scope(user)
        course_query = course_scope(user)
        project_query, patent_query, publication_query = research_scope(user)
        if user.role == "admin":
            department_stats = (
                db.session.query(Department.name, db.func.count(Employee.id))
                .outerjoin(Employee, Employee.department_id == Department.id)
                .group_by(Department.id, Department.name)
                .all()
            )
            title_stats = (
                db.session.query(Employee.title, db.func.count(Employee.id))
                .group_by(Employee.title)
                .all()
            )
        else:
            department_stats = [(current_employee.department.name, 1)] if current_employee and current_employee.department else []
            title_stats = [(current_employee.title or "未填写", 1)] if current_employee else []

        employee_count = employee_query.count()
        course_count = course_query.count()
        teaching_count = teaching_query.count()
        research_count = project_query.count() + patent_query.count() + publication_query.count()
        salary_rule = get_salary_rule(current_employee.salary_grade) if current_employee else None
        return render_template(
            "dashboard.html",
            employee_count=employee_count,
            course_count=course_count,
            teaching_count=teaching_count,
            research_count=research_count,
            department_stats=department_stats,
            title_stats=title_stats,
            current_employee=current_employee,
            current_salary_rule=salary_rule,
            current_salary_total=format_currency(estimate_monthly_salary(current_employee.salary_grade) if current_employee else None),
        )

    @app.route("/employees")
    @login_required
    def employee_list():
        user = get_current_user()
        query = employee_scope(user)
        filters = {
            "employee_no": request.args.get("employee_no", "").strip(),
            "name": request.args.get("name", "").strip(),
            "department_id": request.args.get("department_id", "").strip(),
            "title": request.args.get("title", "").strip(),
            "education": request.args.get("education", "").strip(),
            "status": request.args.get("status", "").strip(),
        }
        if filters["employee_no"]:
            query = query.filter(Employee.employee_no.contains(filters["employee_no"]))
        if filters["name"]:
            query = query.filter(Employee.name.contains(filters["name"]))
        if filters["department_id"]:
            query = query.filter(Employee.department_id == int(filters["department_id"]))
        if filters["title"]:
            query = query.filter(Employee.title.contains(filters["title"]))
        if filters["education"]:
            query = query.filter(Employee.education.contains(filters["education"]))
        if filters["status"]:
            query = query.filter(Employee.status == filters["status"])

        employees = query.order_by(Employee.employee_no.asc()).all()
        departments = Department.query.order_by(Department.name.asc()).all()
        return render_template(
            "employees/list.html",
            employees=employees,
            departments=departments,
            filters=filters,
            salary_rule_map={rule["grade"]: rule for rule in SALARY_RULES},
            format_currency=format_currency,
            estimate_monthly_salary=estimate_monthly_salary,
        )

    @app.route("/employees/new", methods=["GET", "POST"])
    @role_required("admin")
    def employee_create():
        departments = Department.query.order_by(Department.name.asc()).all()
        if request.method == "POST":
            now = datetime.utcnow()
            employee = Employee(created_at=now, updated_at=now)
            apply_employee_form(employee, employee_form_data(request.form, is_admin=True), is_admin=True)
            db.session.add(employee)
            db.session.commit()
            flash("教职工信息已新增。", "success")
            return redirect(url_for("employee_list"))
        return render_template("employees/form.html", employee=None, departments=departments)

    @app.route("/employees/<int:employee_id>/edit", methods=["GET", "POST"])
    @login_required
    def employee_edit(employee_id: int):
        user = get_current_user()
        employee = get_or_404(Employee, employee_id)
        if not can_manage_employee(user, employee_id):
            abort(403)
        departments = Department.query.order_by(Department.name.asc()).all()
        if request.method == "POST":
            data = employee_form_data(request.form, is_admin=user.role == "admin")
            apply_employee_form(employee, data, is_admin=user.role == "admin")
            touch_record(employee)
            db.session.commit()
            flash("教职工信息已更新。", "success")
            return redirect(url_for("employee_list"))
        return render_template("employees/form.html", employee=employee, departments=departments)

    @app.route("/employees/<int:employee_id>/deactivate", methods=["POST"])
    @role_required("admin")
    def employee_deactivate(employee_id: int):
        employee = get_or_404(Employee, employee_id)
        employee.status = request.form.get("status", EMPLOYEE_STATUSES[1])
        touch_record(employee)
        db.session.commit()
        flash("人员状态已更新，历史记录已保留。", "info")
        return redirect(url_for("employee_list"))

    @app.route("/courses")
    @login_required
    def course_list():
        user = get_current_user()
        courses = course_scope(user).order_by(Course.course_no.asc()).all()
        return render_template("courses/list.html", courses=courses)

    @app.route("/courses/new", methods=["GET", "POST"])
    @role_required("admin")
    def course_create():
        if request.method == "POST":
            now = datetime.utcnow()
            course = Course(
                course_no=request.form["course_no"].strip(),
                name=request.form["name"].strip(),
                nature=request.form["nature"],
                credits=float(request.form["credits"] or 0),
                hours=int(request.form["hours"] or 0),
                applicable_major=request.form.get("applicable_major", "").strip(),
                description=request.form.get("description", "").strip(),
                created_at=now,
                updated_at=now,
            )
            db.session.add(course)
            db.session.commit()
            flash("课程信息已新增。", "success")
            return redirect(url_for("course_list"))
        return render_template("courses/form.html", course=None)

    @app.route("/courses/<int:course_id>/edit", methods=["GET", "POST"])
    @role_required("admin")
    def course_edit(course_id: int):
        course = get_or_404(Course, course_id)
        if request.method == "POST":
            course.course_no = request.form["course_no"].strip()
            course.name = request.form["name"].strip()
            course.nature = request.form["nature"]
            course.credits = float(request.form["credits"] or 0)
            course.hours = int(request.form["hours"] or 0)
            course.applicable_major = request.form.get("applicable_major", "").strip()
            course.description = request.form.get("description", "").strip()
            touch_record(course)
            db.session.commit()
            flash("课程信息已更新。", "success")
            return redirect(url_for("course_list"))
        return render_template("courses/form.html", course=course)

    @app.route("/teaching")
    @login_required
    def teaching_list():
        user = get_current_user()
        query = teaching_scope(user)
        course_name = request.args.get("course_name", "").strip()
        teacher_name = request.args.get("teacher_name", "").strip()
        if course_name:
            query = query.filter(Course.name.contains(course_name))
        if teacher_name:
            query = query.filter(Employee.name.contains(teacher_name))
        assignments = query.order_by(TeachingAssignment.semester.desc()).all()
        employees = Employee.query.order_by(Employee.name.asc()).all() if user.role == "admin" else []
        courses = Course.query.order_by(Course.name.asc()).all()
        return render_template(
            "courses/teaching_list.html",
            assignments=assignments,
            employees=employees,
            courses=courses,
            filters={"course_name": course_name, "teacher_name": teacher_name},
        )

    @app.route("/teaching/new", methods=["GET", "POST"])
    @role_required("admin")
    def teaching_create():
        employees = Employee.query.order_by(Employee.name.asc()).all()
        courses = Course.query.order_by(Course.name.asc()).all()
        if request.method == "POST":
            now = datetime.utcnow()
            assignment = TeachingAssignment(
                employee_id=int(request.form["employee_id"]),
                course_id=int(request.form["course_id"]),
                class_name=request.form["class_name"].strip(),
                student_count=int(request.form["student_count"] or 0),
                semester=request.form["semester"].strip(),
                created_at=now,
                updated_at=now,
            )
            db.session.add(assignment)
            db.session.commit()
            flash("授课任务已新增。", "success")
            return redirect(url_for("teaching_list"))
        return render_template(
            "courses/teaching_form.html", assignment=None, employees=employees, courses=courses
        )

    @app.route("/teaching/<int:assignment_id>/edit", methods=["GET", "POST"])
    @role_required("admin")
    def teaching_edit(assignment_id: int):
        assignment = get_or_404(TeachingAssignment, assignment_id)
        employees = Employee.query.order_by(Employee.name.asc()).all()
        courses = Course.query.order_by(Course.name.asc()).all()
        if request.method == "POST":
            assignment.employee_id = int(request.form["employee_id"])
            assignment.course_id = int(request.form["course_id"])
            assignment.class_name = request.form["class_name"].strip()
            assignment.student_count = int(request.form["student_count"] or 0)
            assignment.semester = request.form["semester"].strip()
            touch_record(assignment)
            db.session.commit()
            flash("授课任务已更新。", "success")
            return redirect(url_for("teaching_list"))
        return render_template(
            "courses/teaching_form.html",
            assignment=assignment,
            employees=employees,
            courses=courses,
        )

    @app.route("/research")
    @login_required
    def research_home():
        user = get_current_user()
        project_query, patent_query, publication_query = research_scope(user)
        keyword = request.args.get("keyword", "").strip()
        if keyword:
            project_query = project_query.filter(ResearchProject.project_name.contains(keyword))
            patent_query = patent_query.filter(Patent.patent_name.contains(keyword))
            publication_query = publication_query.filter(Publication.work_name.contains(keyword))
        return render_template(
            "research/index.html",
            projects=project_query.order_by(ResearchProject.start_date.desc()).all(),
            patents=patent_query.order_by(Patent.grant_date.desc()).all(),
            publications=publication_query.order_by(Publication.publish_date.desc()).all(),
            keyword=keyword,
            employees=Employee.query.order_by(Employee.name.asc()).all(),
        )

    @app.route("/research/project/new", methods=["GET", "POST"])
    @role_required("admin")
    def project_create():
        employees = Employee.query.order_by(Employee.name.asc()).all()
        if request.method == "POST":
            now = datetime.utcnow()
            record = ResearchProject(
                employee_id=int(request.form["employee_id"]),
                research_direction=request.form["research_direction"].strip(),
                project_no=request.form["project_no"].strip(),
                project_name=request.form["project_name"].strip(),
                sponsor=request.form.get("sponsor", "").strip(),
                start_date=parse_date(request.form.get("start_date", "")),
                end_date=parse_date(request.form.get("end_date", "")),
                status=request.form.get("status", RESEARCH_STATUSES[0]),
                created_at=now,
                updated_at=now,
            )
            db.session.add(record)
            db.session.commit()
            flash("课题信息已新增。", "success")
            return redirect(url_for("research_home"))
        return render_template("research/project_form.html", record=None, employees=employees)

    @app.route("/research/project/<int:record_id>/edit", methods=["GET", "POST"])
    @role_required("admin")
    def project_edit(record_id: int):
        employees = Employee.query.order_by(Employee.name.asc()).all()
        record = get_or_404(ResearchProject, record_id)
        if request.method == "POST":
            record.employee_id = int(request.form["employee_id"])
            record.research_direction = request.form["research_direction"].strip()
            record.project_no = request.form["project_no"].strip()
            record.project_name = request.form["project_name"].strip()
            record.sponsor = request.form.get("sponsor", "").strip()
            record.start_date = parse_date(request.form.get("start_date", ""))
            record.end_date = parse_date(request.form.get("end_date", ""))
            record.status = request.form.get("status", RESEARCH_STATUSES[0])
            touch_record(record)
            db.session.commit()
            flash("课题信息已更新。", "success")
            return redirect(url_for("research_home"))
        return render_template("research/project_form.html", record=record, employees=employees)

    @app.route("/research/project/<int:record_id>/delete", methods=["POST"])
    @role_required("admin")
    def project_delete(record_id: int):
        record = get_or_404(ResearchProject, record_id)
        db.session.delete(record)
        db.session.commit()
        flash("课题信息已删除。", "info")
        return redirect(url_for("research_home"))

    @app.route("/research/patent/new", methods=["GET", "POST"])
    @role_required("admin")
    def patent_create():
        employees = Employee.query.order_by(Employee.name.asc()).all()
        if request.method == "POST":
            now = datetime.utcnow()
            record = Patent(
                employee_id=int(request.form["employee_id"]),
                patent_no=request.form["patent_no"].strip(),
                patent_name=request.form["patent_name"].strip(),
                grant_date=parse_date(request.form.get("grant_date", "")),
                patent_type=request.form.get("patent_type", "").strip(),
                inventors=request.form.get("inventors", "").strip(),
                created_at=now,
                updated_at=now,
            )
            db.session.add(record)
            db.session.commit()
            flash("专利信息已新增。", "success")
            return redirect(url_for("research_home"))
        return render_template("research/patent_form.html", record=None, employees=employees)

    @app.route("/research/patent/<int:record_id>/edit", methods=["GET", "POST"])
    @role_required("admin")
    def patent_edit(record_id: int):
        employees = Employee.query.order_by(Employee.name.asc()).all()
        record = get_or_404(Patent, record_id)
        if request.method == "POST":
            record.employee_id = int(request.form["employee_id"])
            record.patent_no = request.form["patent_no"].strip()
            record.patent_name = request.form["patent_name"].strip()
            record.grant_date = parse_date(request.form.get("grant_date", ""))
            record.patent_type = request.form.get("patent_type", "").strip()
            record.inventors = request.form.get("inventors", "").strip()
            touch_record(record)
            db.session.commit()
            flash("专利信息已更新。", "success")
            return redirect(url_for("research_home"))
        return render_template("research/patent_form.html", record=record, employees=employees)

    @app.route("/research/patent/<int:record_id>/delete", methods=["POST"])
    @role_required("admin")
    def patent_delete(record_id: int):
        record = get_or_404(Patent, record_id)
        db.session.delete(record)
        db.session.commit()
        flash("专利信息已删除。", "info")
        return redirect(url_for("research_home"))

    @app.route("/research/publication/new", methods=["GET", "POST"])
    @role_required("admin")
    def publication_create():
        employees = Employee.query.order_by(Employee.name.asc()).all()
        if request.method == "POST":
            now = datetime.utcnow()
            record = Publication(
                employee_id=int(request.form["employee_id"]),
                work_name=request.form["work_name"].strip(),
                publisher=request.form.get("publisher", "").strip(),
                publish_date=parse_date(request.form.get("publish_date", "")),
                author_order=request.form.get("author_order", "").strip(),
                isbn_issn=request.form.get("isbn_issn", "").strip(),
                work_type=request.form.get("work_type", PUBLICATION_TYPES[0]),
                created_at=now,
                updated_at=now,
            )
            db.session.add(record)
            db.session.commit()
            flash("论文/著作信息已新增。", "success")
            return redirect(url_for("research_home"))
        return render_template("research/publication_form.html", record=None, employees=employees)

    @app.route("/research/publication/<int:record_id>/edit", methods=["GET", "POST"])
    @role_required("admin")
    def publication_edit(record_id: int):
        employees = Employee.query.order_by(Employee.name.asc()).all()
        record = get_or_404(Publication, record_id)
        if request.method == "POST":
            record.employee_id = int(request.form["employee_id"])
            record.work_name = request.form["work_name"].strip()
            record.publisher = request.form.get("publisher", "").strip()
            record.publish_date = parse_date(request.form.get("publish_date", ""))
            record.author_order = request.form.get("author_order", "").strip()
            record.isbn_issn = request.form.get("isbn_issn", "").strip()
            record.work_type = request.form.get("work_type", PUBLICATION_TYPES[0])
            touch_record(record)
            db.session.commit()
            flash("论文/著作信息已更新。", "success")
            return redirect(url_for("research_home"))
        return render_template("research/publication_form.html", record=record, employees=employees)

    @app.route("/research/publication/<int:record_id>/delete", methods=["POST"])
    @role_required("admin")
    def publication_delete(record_id: int):
        record = get_or_404(Publication, record_id)
        db.session.delete(record)
        db.session.commit()
        flash("论文/著作信息已删除。", "info")
        return redirect(url_for("research_home"))

    @app.route("/statistics")
    @role_required("admin")
    def statistics():
        department_stats = (
            db.session.query(Department.name, db.func.count(Employee.id))
            .outerjoin(Employee, Employee.department_id == Department.id)
            .group_by(Department.id, Department.name)
            .all()
        )
        title_stats = (
            db.session.query(Employee.title, db.func.count(Employee.id))
            .group_by(Employee.title)
            .all()
        )
        education_stats = (
            db.session.query(Employee.education, db.func.count(Employee.id))
            .group_by(Employee.education)
            .all()
        )
        research_stats = {
            "projects": ResearchProject.query.count(),
            "patents": Patent.query.count(),
            "publications": Publication.query.count(),
        }
        return render_template(
            "stats/index.html",
            department_stats=department_stats,
            title_stats=title_stats,
            education_stats=education_stats,
            research_stats=research_stats,
        )

    @app.route("/salary-rules")
    @login_required
    def salary_rules():
        user = get_current_user()
        current_employee = user.employee
        current_rule = get_salary_rule(current_employee.salary_grade) if current_employee else None
        return render_template(
            "salary_rules.html",
            salary_rules=SALARY_RULES,
            reward_rules=REWARD_RULES,
            punishment_rules=PUNISHMENT_RULES,
            current_employee=current_employee,
            current_rule=current_rule,
            current_total=format_currency(estimate_monthly_salary(current_employee.salary_grade) if current_employee else None),
            format_currency=format_currency,
        )

    @app.route("/export/<string:table_name>")
    @login_required
    def export_excel(table_name: str):
        user = get_current_user()
        if table_name == "employees":
            query = employee_scope(user)
            rows = [
                [
                    item.employee_no,
                    item.name,
                    item.gender,
                    item.department.name,
                    item.title,
                    item.salary_grade,
                    format_currency(estimate_monthly_salary(item.salary_grade)),
                    item.education,
                    item.status,
                    item.phone,
                    item.email,
                    item.reward_punishment,
                ]
                for item in query.all()
            ]
            stream = export_workbook(
                "教职工信息表",
                ["编号", "姓名", "性别", "部门", "职称", "薪资等级", "参考月薪", "学历", "状态", "电话", "邮箱", "奖惩记录"],
                rows,
            )
            filename = "employees.xlsx"
        elif table_name == "teaching":
            query = teaching_scope(user)
            rows = [
                [
                    item.employee.name,
                    item.course.name,
                    item.class_name,
                    item.student_count,
                    item.semester,
                ]
                for item in query.all()
            ]
            stream = export_workbook(
                "教学任务表",
                ["教师", "课程", "班级", "学生人数", "学期"],
                rows,
            )
            filename = "teaching.xlsx"
        elif table_name == "research":
            project_query, patent_query, publication_query = research_scope(user)
            project_rows = [
                [
                    "课题",
                    item.employee.name,
                    item.project_no,
                    item.project_name,
                    item.sponsor,
                    item.status,
                ]
                for item in project_query.all()
            ]
            patent_rows = [
                [
                    "专利",
                    item.employee.name,
                    item.patent_no,
                    item.patent_name,
                    item.patent_type,
                    item.grant_date,
                ]
                for item in patent_query.all()
            ]
            publication_rows = [
                [
                    item.work_type,
                    item.employee.name,
                    "",
                    item.work_name,
                    item.publisher,
                    item.publish_date,
                ]
                for item in publication_query.all()
            ]
            stream = export_workbook(
                "科研成果表",
                ["类型", "教师", "编号", "名称", "单位/期刊/出版社", "时间/状态"],
                project_rows + patent_rows + publication_rows,
            )
            filename = "research.xlsx"
        else:
            flash("不支持的导出类型。", "warning")
            return redirect(url_for("dashboard"))

        return send_excel_file(stream, filename)


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
