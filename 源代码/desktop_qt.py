from __future__ import annotations

import sys
from collections import Counter
from datetime import datetime

from compat import patch_flask_jinja_compat

patch_flask_jinja_compat()

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QAction, QColor
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config import Config
from app import create_app
from desktop_export import export_to_excel
from extensions import db
from hr_rules import (
    COURSE_NATURES,
    EMPLOYEE_STATUSES,
    GENDER_OPTIONS,
    PUNISHMENT_RULES,
    PUBLICATION_TYPES,
    REWARD_RULES,
    RESEARCH_STATUSES,
    SALARY_GRADE_OPTIONS,
    SALARY_RULES,
    estimate_monthly_salary,
    format_currency,
    get_salary_rule,
)
from models import Course, Department, Employee, Patent, Publication, ResearchProject, TeachingAssignment, User
from seed_data import seed_database


def _text(value) -> str:
    return "" if value is None else str(value)


def _date_text(value) -> str:
    return _text(value)[:10] if value else ""


def _parse_date_text(value: str):
    value = value.strip()
    return datetime.strptime(value, "%Y-%m-%d").date() if value else None


def _course_scope(employee_id: int | None = None):
    query = Course.query
    if employee_id is not None:
        query = query.join(TeachingAssignment).filter(TeachingAssignment.employee_id == employee_id).distinct()
    return query


def _employee_form_payload(data: dict, *, is_admin: bool) -> dict:
    payload = {
        "name": data["name"].strip(),
        "gender": data["gender"],
        "birth_date": _parse_date_text(data.get("birth_date", "")),
        "education": data.get("education", "").strip(),
        "degree": data.get("degree", "").strip(),
        "major": data.get("major", "").strip(),
        "hire_date": _parse_date_text(data.get("hire_date", "")),
        "phone": data.get("phone", "").strip(),
        "email": data.get("email", "").strip(),
        "reward_punishment": data.get("reward_punishment", "").strip(),
        "notes": data.get("notes", "").strip(),
    }
    if is_admin:
        payload.update(
            {
                "employee_no": data["employee_no"].strip(),
                "department_id": int(data["department_id"]),
                "title": data.get("title", "").strip(),
                "position": data.get("position", "").strip(),
                "salary_grade": data.get("salary_grade", "").strip(),
                "status": data.get("status", EMPLOYEE_STATUSES[0]),
            }
        )
    return payload


def _apply_employee_payload(employee: Employee, payload: dict, *, is_admin: bool) -> None:
    employee.name = payload["name"]
    employee.gender = payload["gender"]
    employee.birth_date = payload["birth_date"]
    employee.education = payload["education"]
    employee.degree = payload["degree"]
    employee.major = payload["major"]
    employee.hire_date = payload["hire_date"]
    employee.phone = payload["phone"]
    employee.email = payload["email"]
    employee.reward_punishment = payload["reward_punishment"]
    employee.notes = payload["notes"]
    if is_admin:
        employee.employee_no = payload["employee_no"]
        employee.department_id = payload["department_id"]
        employee.title = payload["title"]
        employee.position = payload["position"]
        employee.salary_grade = payload["salary_grade"]
        employee.status = payload["status"]


class DataService:
    def __init__(self, user=None) -> None:
        self.user = user
        self.app = create_app()
        with self.app.app_context():
            seed_database(db)

    def _is_admin(self) -> bool:
        return not self.user or getattr(self.user, "role", "admin") == "admin"

    def _employee_id(self):
        return getattr(self.user, "employee_id", None)

    def _scope_employee_query(self):
        query = Employee.query.join(Department)
        if not self._is_admin():
            query = query.filter(Employee.id == self._employee_id())
        return query

    def _scope_teaching_query(self):
        query = TeachingAssignment.query.join(Employee).join(Department).join(Course)
        if not self._is_admin():
            query = query.filter(TeachingAssignment.employee_id == self._employee_id())
        return query

    def _scope_research_queries(self):
        project_query = ResearchProject.query.join(Employee)
        patent_query = Patent.query.join(Employee)
        publication_query = Publication.query.join(Employee)
        if not self._is_admin():
            project_query = project_query.filter(ResearchProject.employee_id == self._employee_id())
            patent_query = patent_query.filter(Patent.employee_id == self._employee_id())
            publication_query = publication_query.filter(Publication.employee_id == self._employee_id())
        return project_query, patent_query, publication_query

    def _scope_course_query(self):
        return _course_scope(None if self._is_admin() else self._employee_id())

    def login(self, username: str, password: str):
        with self.app.app_context():
            user = User.query.filter_by(username=username.strip()).first()
            if user and user.check_password(password):
                return user
        return None

    def employees(self, filters: dict | None = None):
        filters = filters or {}
        with self.app.app_context():
            query = self._scope_employee_query()
            if filters.get("keyword"):
                kw = filters["keyword"]
                query = query.filter(
                    db.func.lower(Employee.employee_no).contains(kw.lower())
                    | db.func.lower(Employee.name).contains(kw.lower())
                    | db.func.lower(Department.name).contains(kw.lower())
                    | db.func.lower(Employee.title).contains(kw.lower())
                    | db.func.lower(Employee.education).contains(kw.lower())
                )
            if filters.get("name"):
                query = query.filter(Employee.name.contains(filters["name"]))
            if filters.get("employee_no"):
                query = query.filter(Employee.employee_no.contains(filters["employee_no"]))
            if filters.get("department_id"):
                query = query.filter(Employee.department_id == int(filters["department_id"]))
            if filters.get("title"):
                query = query.filter(Employee.title.contains(filters["title"]))
            if filters.get("education"):
                query = query.filter(Employee.education.contains(filters["education"]))
            if filters.get("status"):
                query = query.filter(Employee.status == filters["status"])
            items = query.order_by(Employee.employee_no.asc()).all()
            return [
                {
                    "id": item.id,
                    "employee_no": item.employee_no,
                    "name": item.name,
                    "gender": item.gender,
                    "department_id": item.department_id,
                    "department": item.department.name if item.department else "",
                    "education": item.education or "",
                    "degree": item.degree or "",
                    "major": item.major or "",
                    "title": item.title or "",
                    "position": item.position or "",
                    "salary_grade": item.salary_grade or "",
                    "salary_total": format_currency(estimate_monthly_salary(item.salary_grade)),
                    "status": item.status or "",
                    "phone": item.phone or "",
                    "email": item.email or "",
                    "reward_punishment": item.reward_punishment or "",
                }
                for item in items
            ]

    def departments(self):
        with self.app.app_context():
            return Department.query.order_by(Department.name.asc()).all()

    def courses(self):
        with self.app.app_context():
            items = self._scope_course_query().order_by(Course.course_no.asc()).all()
            return [
                {
                    "id": item.id,
                    "course_no": item.course_no,
                    "name": item.name,
                    "nature": item.nature,
                    "credits": item.credits,
                    "hours": item.hours,
                    "applicable_major": item.applicable_major or "",
                    "description": item.description or "",
                }
                for item in items
            ]

    def course_lookup(self):
        with self.app.app_context():
            return [
                {"id": item.id, "name": item.name, "course_no": item.course_no}
                for item in Course.query.order_by(Course.course_no.asc()).all()
            ]

    def employees_lookup(self):
        with self.app.app_context():
            return [
                {"id": item.id, "name": item.name, "employee_no": item.employee_no}
                for item in self._scope_employee_query().order_by(Employee.name.asc()).all()
            ]

    def assignments(self, filters: dict | None = None):
        filters = filters or {}
        with self.app.app_context():
            query = self._scope_teaching_query()
            if filters.get("course_name"):
                query = query.filter(Course.name.contains(filters["course_name"]))
            if filters.get("teacher_name"):
                query = query.filter(Employee.name.contains(filters["teacher_name"]))
            if filters.get("semester"):
                query = query.filter(TeachingAssignment.semester.contains(filters["semester"]))
            items = query.order_by(TeachingAssignment.semester.desc()).all()
            return [
                {
                    "id": item.id,
                    "employee_id": item.employee_id,
                    "course_id": item.course_id,
                    "teacher": item.employee.name if item.employee else "",
                    "course": item.course.name if item.course else "",
                    "class_name": item.class_name,
                    "student_count": item.student_count,
                    "semester": item.semester,
                    "department": item.employee.department.name if item.employee and item.employee.department else "",
                }
                for item in items
            ]

    def projects(self, keyword: str = ""):
        with self.app.app_context():
            query = self._scope_research_queries()[0]
            if keyword:
                query = query.filter(ResearchProject.project_name.contains(keyword))
            items = query.order_by(ResearchProject.start_date.desc()).all()
            return [
                {
                    "id": item.id,
                    "employee_id": item.employee_id,
                    "teacher": item.employee.name if item.employee else "",
                    "research_direction": item.research_direction,
                    "project_no": item.project_no,
                    "project_name": item.project_name,
                    "sponsor": item.sponsor or "",
                    "start_date": _date_text(item.start_date),
                    "end_date": _date_text(item.end_date),
                    "status": item.status,
                }
                for item in items
            ]

    def patents(self, keyword: str = ""):
        with self.app.app_context():
            query = self._scope_research_queries()[1]
            if keyword:
                query = query.filter(Patent.patent_name.contains(keyword))
            items = query.order_by(Patent.grant_date.desc()).all()
            return [
                {
                    "id": item.id,
                    "employee_id": item.employee_id,
                    "teacher": item.employee.name if item.employee else "",
                    "patent_no": item.patent_no,
                    "patent_name": item.patent_name,
                    "grant_date": _date_text(item.grant_date),
                    "patent_type": item.patent_type or "",
                    "inventors": item.inventors or "",
                }
                for item in items
            ]

    def publications(self, keyword: str = ""):
        with self.app.app_context():
            query = self._scope_research_queries()[2]
            if keyword:
                query = query.filter(Publication.work_name.contains(keyword))
            items = query.order_by(Publication.publish_date.desc()).all()
            return [
                {
                    "id": item.id,
                    "employee_id": item.employee_id,
                    "teacher": item.employee.name if item.employee else "",
                    "work_type": item.work_type,
                    "work_name": item.work_name,
                    "publisher": item.publisher or "",
                    "publish_date": _date_text(item.publish_date),
                    "author_order": item.author_order or "",
                    "isbn_issn": item.isbn_issn or "",
                }
                for item in items
            ]

    def dashboard_metrics(self):
        with self.app.app_context():
            employee_query = self._scope_employee_query()
            employees = employee_query.all()
            department_count = Department.query.count() if self._is_admin() else (1 if employees else 0)
            course_count = self._scope_course_query().count()
            assignment_count = self._scope_teaching_query().count()
            project_query, patent_query, publication_query = self._scope_research_queries()
            title_counter = Counter(item.title or "未填写" for item in employees)
            status_counter = Counter(item.status or "未知" for item in employees)
            salary_counter = Counter(item.salary_grade or "未定级" for item in employees)
            current_employee = employees[0] if (employees and not self._is_admin()) else None
            return {
                "employee_count": len(employees),
                "department_count": department_count,
                "course_count": course_count,
                "assignment_count": assignment_count,
                "research_count": project_query.count() + patent_query.count() + publication_query.count(),
                "title_counter": title_counter,
                "status_counter": status_counter,
                "salary_counter": salary_counter,
                "current_salary_rule": get_salary_rule(current_employee.salary_grade) if current_employee else None,
                "current_salary_total": format_currency(
                    estimate_monthly_salary(current_employee.salary_grade) if current_employee else None
                ),
            }

    def save_employee(self, data: dict, employee_id: int | None = None):
        with self.app.app_context():
            now = datetime.utcnow()
            if employee_id:
                employee = db.session.get(Employee, employee_id)
                if employee is None:
                    raise ValueError("员工不存在")
                if not self._is_admin() and employee.id != self._employee_id():
                    raise PermissionError("无权限")
            else:
                employee = Employee(created_at=now, updated_at=now)
                db.session.add(employee)
            payload = _employee_form_payload(data, is_admin=self._is_admin())
            _apply_employee_payload(employee, payload, is_admin=self._is_admin())
            employee.updated_at = now
            db.session.commit()
            return employee

    def deactivate_employee(self, employee_id: int, status: str):
        with self.app.app_context():
            employee = db.session.get(Employee, employee_id)
            if employee is None:
                raise ValueError("员工不存在")
            if not self._is_admin():
                raise PermissionError("无权限")
            employee.status = status
            employee.updated_at = datetime.utcnow()
            db.session.commit()

    def save_course(self, data: dict, course_id: int | None = None):
        with self.app.app_context():
            now = datetime.utcnow()
            if course_id:
                course = db.session.get(Course, course_id)
                if course is None:
                    raise ValueError("课程不存在")
            else:
                course = Course(created_at=now, updated_at=now)
                db.session.add(course)
            course.course_no = data["course_no"].strip()
            course.name = data["name"].strip()
            course.nature = data["nature"]
            course.credits = float(data.get("credits") or 0)
            course.hours = int(data.get("hours") or 0)
            course.applicable_major = data.get("applicable_major", "").strip()
            course.description = data.get("description", "").strip()
            course.updated_at = now
            db.session.commit()
            return course

    def delete_course(self, course_id: int):
        with self.app.app_context():
            course = db.session.get(Course, course_id)
            if course is None:
                raise ValueError("课程不存在")
            db.session.delete(course)
            db.session.commit()

    def save_assignment(self, data: dict, assignment_id: int | None = None):
        with self.app.app_context():
            now = datetime.utcnow()
            if assignment_id:
                assignment = db.session.get(TeachingAssignment, assignment_id)
                if assignment is None:
                    raise ValueError("授课任务不存在")
            else:
                assignment = TeachingAssignment(created_at=now, updated_at=now)
                db.session.add(assignment)
            assignment.employee_id = int(data["employee_id"])
            assignment.course_id = int(data["course_id"])
            assignment.class_name = data["class_name"].strip()
            assignment.student_count = int(data.get("student_count") or 0)
            assignment.semester = data["semester"].strip()
            assignment.updated_at = now
            db.session.commit()
            return assignment

    def delete_assignment(self, assignment_id: int):
        with self.app.app_context():
            assignment = db.session.get(TeachingAssignment, assignment_id)
            if assignment is None:
                raise ValueError("授课任务不存在")
            db.session.delete(assignment)
            db.session.commit()

    def save_project(self, data: dict, project_id: int | None = None):
        with self.app.app_context():
            now = datetime.utcnow()
            if project_id:
                record = db.session.get(ResearchProject, project_id)
                if record is None:
                    raise ValueError("课题不存在")
            else:
                record = ResearchProject(created_at=now, updated_at=now)
                db.session.add(record)
            record.employee_id = int(data["employee_id"])
            record.research_direction = data["research_direction"].strip()
            record.project_no = data["project_no"].strip()
            record.project_name = data["project_name"].strip()
            record.sponsor = data.get("sponsor", "").strip()
            record.start_date = _parse_date_text(data.get("start_date", ""))
            record.end_date = _parse_date_text(data.get("end_date", ""))
            record.status = data.get("status", RESEARCH_STATUSES[0])
            record.updated_at = now
            db.session.commit()
            return record

    def delete_project(self, project_id: int):
        with self.app.app_context():
            record = db.session.get(ResearchProject, project_id)
            if record is None:
                raise ValueError("课题不存在")
            db.session.delete(record)
            db.session.commit()

    def save_patent(self, data: dict, patent_id: int | None = None):
        with self.app.app_context():
            now = datetime.utcnow()
            if patent_id:
                record = db.session.get(Patent, patent_id)
                if record is None:
                    raise ValueError("专利不存在")
            else:
                record = Patent(created_at=now, updated_at=now)
                db.session.add(record)
            record.employee_id = int(data["employee_id"])
            record.patent_no = data["patent_no"].strip()
            record.patent_name = data["patent_name"].strip()
            record.grant_date = _parse_date_text(data.get("grant_date", ""))
            record.patent_type = data.get("patent_type", "").strip()
            record.inventors = data.get("inventors", "").strip()
            record.updated_at = now
            db.session.commit()
            return record

    def delete_patent(self, patent_id: int):
        with self.app.app_context():
            record = db.session.get(Patent, patent_id)
            if record is None:
                raise ValueError("专利不存在")
            db.session.delete(record)
            db.session.commit()

    def save_publication(self, data: dict, publication_id: int | None = None):
        with self.app.app_context():
            now = datetime.utcnow()
            if publication_id:
                record = db.session.get(Publication, publication_id)
                if record is None:
                    raise ValueError("成果不存在")
            else:
                record = Publication(created_at=now, updated_at=now)
                db.session.add(record)
            record.employee_id = int(data["employee_id"])
            record.work_name = data["work_name"].strip()
            record.publisher = data.get("publisher", "").strip()
            record.publish_date = _parse_date_text(data.get("publish_date", ""))
            record.author_order = data.get("author_order", "").strip()
            record.isbn_issn = data.get("isbn_issn", "").strip()
            record.work_type = data.get("work_type", PUBLICATION_TYPES[0])
            record.updated_at = now
            db.session.commit()
            return record

    def delete_publication(self, publication_id: int):
        with self.app.app_context():
            record = db.session.get(Publication, publication_id)
            if record is None:
                raise ValueError("成果不存在")
            db.session.delete(record)
            db.session.commit()


class TableView(QFrame):
    def __init__(self, headers: list[str]) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

    def render(self, rows: list[list]) -> None:
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                item = QTableWidgetItem(_text(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, c, item)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()


class LoginDialog(QDialog):
    def __init__(self, service: DataService) -> None:
        super().__init__()
        self.service = service
        self.user = None
        self.setWindowTitle("登录 - 高校人事信息管理系统")
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        title = QLabel("高校人事信息管理系统")
        title.setStyleSheet("font-size:22px;font-weight:700;color:#165dff;")
        layout.addWidget(title)
        form = QFormLayout()
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        form.addRow("用户名", self.username)
        form.addRow("密码", self.password)
        layout.addLayout(form)
        helper = QLabel(
            "默认账号：\n"
            "管理员：admin / admin123\n"
            "教师：教职工编号 / 教职工编号@123\n"
            "示例：T2024001 / T2024001@123\n\n"
            f"当前数据库：{Config.SQLALCHEMY_DATABASE_URI}"
        )
        helper.setWordWrap(True)
        helper.setStyleSheet("color:#5b6b82;")
        layout.addWidget(helper)
        btn = QPushButton("登录")
        btn.clicked.connect(self._login)
        layout.addWidget(btn)

    def _login(self) -> None:
        user = self.service.login(self.username.text(), self.password.text())
        if not user:
            QMessageBox.warning(self, "登录失败", "用户名或密码错误")
            return
        self.user = user
        self.accept()


class EntityFormDialog(QDialog):
    def __init__(self, title: str, fields: list[tuple], values: dict | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.values = values or {}
        self.inputs = {}
        layout = QVBoxLayout(self)
        form = QFormLayout()
        for field in fields:
            kind = field[0]
            name = field[1]
            label = field[2]
            default = self.values.get(name, field[3] if len(field) > 3 else "")
            if kind == "text":
                widget = QLineEdit(_text(default))
            elif kind == "number":
                widget = QLineEdit(_text(default))
            elif kind == "date":
                widget = QDateEdit()
                widget.setCalendarPopup(True)
                if default:
                    widget.setDate(QDate.fromString(_date_text(default), "yyyy-MM-dd"))
                else:
                    widget.setSpecialValueText("")
                    widget.setDate(QDate.currentDate())
                    widget.clear()
            elif kind == "select":
                widget = QComboBox()
                for option in field[3]:
                    widget.addItem(option)
                if default:
                    idx = widget.findText(str(default))
                    if idx >= 0:
                        widget.setCurrentIndex(idx)
            else:
                widget = QLineEdit(_text(default))
            self.inputs[name] = widget
            form.addRow(label, widget)
        layout.addLayout(form)
        row = QHBoxLayout()
        ok = QPushButton("保存")
        cancel = QPushButton("取消")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        row.addWidget(ok)
        row.addWidget(cancel)
        layout.addLayout(row)

    def data(self) -> dict:
        result = {}
        for name, widget in self.inputs.items():
            if isinstance(widget, QComboBox):
                result[name] = widget.currentText()
            elif isinstance(widget, QDateEdit):
                result[name] = widget.date().toString("yyyy-MM-dd")
            else:
                result[name] = widget.text().strip()
        return result


class DesktopWindow(QMainWindow):
    def __init__(self, user) -> None:
        super().__init__()
        self.user = user
        self.service = DataService(user)
        self.setWindowTitle("高校人事信息管理系统")
        self.resize(1600, 960)
        self.employee_rows: list[list] = []
        self.employee_records: list[dict] = []
        self.course_records: list[dict] = []
        self.assignment_records: list[dict] = []
        self.project_records: list[dict] = []
        self.patent_records: list[dict] = []
        self.publication_records: list[dict] = []
        self.salary_rows: list[list] = []
        self._build_ui()
        self.refresh_all()

    def _build_ui(self) -> None:
        container = QWidget()
        root = QVBoxLayout(container)
        self.title = QLabel("高校人事信息管理系统")
        self.subtitle = QLabel("Qt 桌面端与 Web 端共用同一数据库")
        root.addWidget(self.title)
        root.addWidget(self.subtitle)

        top = QHBoxLayout()
        self.login_state = QLabel(f"当前用户：{self.user.username} / {self.user.role}")
        top.addWidget(self.login_state)
        top.addStretch()
        for text, handler in [
            ("刷新", self.refresh_all),
            ("导出当前页", self.export_current_view),
            ("打印当前页", self.print_current_view),
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(handler)
            top.addWidget(btn)
        root.addLayout(top)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_dashboard_tab(), "系统概览")
        self.tabs.addTab(self._build_employee_tab(), "教职工管理")
        self.tabs.addTab(self._build_teaching_tab(), "教学管理")
        self.tabs.addTab(self._build_research_tab(), "科研管理")
        self.tabs.addTab(self._build_salary_tab(), "工资与奖惩规则")
        self.tabs.addTab(self._build_schema_tab(), "数据字典")
        root.addWidget(self.tabs)
        self.setCentralWidget(container)
        self._build_menu()
        self._apply_style()

    def _build_menu(self) -> None:
        menu = self.menuBar().addMenu("系统")
        refresh = QAction("刷新", self)
        refresh.triggered.connect(self.refresh_all)
        export = QAction("导出当前页", self)
        export.triggered.connect(self.export_current_view)
        print_action = QAction("打印当前页", self)
        print_action.triggered.connect(self.print_current_view)
        menu.addAction(refresh)
        menu.addAction(export)
        menu.addAction(print_action)

    def _build_dashboard_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.cards = QHBoxLayout()
        layout.addLayout(self.cards)
        splitter = QSplitter(Qt.Horizontal)
        self.title_stat = QTextEdit()
        self.title_stat.setReadOnly(True)
        self.status_stat = QTextEdit()
        self.status_stat.setReadOnly(True)
        splitter.addWidget(self.title_stat)
        splitter.addWidget(self.status_stat)
        layout.addWidget(splitter)
        return tab

    def _build_employee_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        top = QHBoxLayout()
        self.employee_keyword = QLineEdit()
        self.employee_keyword.setPlaceholderText("姓名、编号、部门、职称、学历组合查询")
        self.employee_keyword.textChanged.connect(self.filter_employees)
        top.addWidget(self.employee_keyword)
        for text, handler in [("新增", self.add_employee), ("编辑", self.edit_employee), ("注销", self.deactivate_employee)]:
            btn = QPushButton(text)
            btn.clicked.connect(handler)
            top.addWidget(btn)
        layout.addLayout(top)
        self.employee_view = TableView(["编号", "姓名", "性别", "部门", "学历", "学位", "专业", "职称", "职务", "薪资等级", "参考月薪", "奖惩记录", "状态", "联系方式"])
        self.employee_table = self.employee_view.table
        layout.addWidget(self.employee_view)
        return tab

    def _build_teaching_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        btns = QHBoxLayout()
        for text, handler in [("新增课程", self.add_course), ("编辑课程", self.edit_course), ("删除课程", self.delete_course), ("新增授课", self.add_assignment), ("编辑授课", self.edit_assignment), ("删除授课", self.delete_assignment)]:
            btn = QPushButton(text)
            btn.clicked.connect(handler)
            btns.addWidget(btn)
        layout.addLayout(btns)
        self.course_view = TableView(["课程编号", "课程名称", "性质", "学分", "学时", "适用专业"])
        self.course_table = self.course_view.table
        self.assignment_view = TableView(["教师", "课程", "授课班级", "学生人数", "学期", "部门"])
        self.assignment_table = self.assignment_view.table
        layout.addWidget(self.course_view)
        layout.addWidget(self.assignment_view)
        return tab

    def _build_research_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        btns = QHBoxLayout()
        for text, handler in [
            ("新增课题", self.add_project),
            ("编辑课题", self.edit_project),
            ("删除课题", self.delete_project),
            ("新增专利", self.add_patent),
            ("编辑专利", self.edit_patent),
            ("删除专利", self.delete_patent),
            ("新增成果", self.add_publication),
            ("编辑成果", self.edit_publication),
            ("删除成果", self.delete_publication),
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(handler)
            btns.addWidget(btn)
        layout.addLayout(btns)
        self.research_tabs = QTabWidget()
        self.project_view = TableView(["教师", "研究方向", "课题编号", "课题名称", "立项单位", "起止时间", "状态"])
        self.project_table = self.project_view.table
        self.patent_view = TableView(["教师", "专利编号", "专利名称", "授权时间", "专利类型", "发明人"])
        self.patent_table = self.patent_view.table
        self.publication_view = TableView(["教师", "类型", "作品名称", "期刊/出版社", "发表时间", "作者排序", "ISBN/ISSN"])
        self.publication_table = self.publication_view.table
        self.research_tabs.addTab(self.project_view, "课题")
        self.research_tabs.addTab(self.patent_view, "专利")
        self.research_tabs.addTab(self.publication_view, "论文/著作")
        layout.addWidget(self.research_tabs)
        return tab

    def _build_salary_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.salary_summary = QTextEdit()
        self.salary_summary.setReadOnly(True)
        layout.addWidget(self.salary_summary)
        self.salary_view = TableView(["等级", "基础工资", "岗位津贴", "绩效工资", "参考月薪", "适用范围", "说明"])
        self.salary_table = self.salary_view.table
        layout.addWidget(self.salary_view)
        self.reward_view = TableView(["类型", "事项", "影响", "备注"])
        self.reward_table = self.reward_view.table
        layout.addWidget(self.reward_view)
        return tab

    def _build_schema_tab(self) -> QWidget:
        tab = QWidget()
        layout = QHBoxLayout(tab)
        left = QTextEdit()
        left.setReadOnly(True)
        left.setPlainText(
            "网页端与桌面端共用一套数据库。\n\n"
            
        )
        right = QTextEdit()
        right.setReadOnly(True)
        right.setPlainText(
            "权限说明：\n"
            "管理员可管理全部数据。\n"
            "普通教师仅可查看/修改本人信息，并仅可查看本人相关教学与科研数据。"
        )
        layout.addWidget(left)
        layout.addWidget(right)
        return tab

    def refresh_all(self) -> None:
        self.load_dashboard()
        self.load_employees()
        self.load_courses()
        self.load_assignments()
        self.load_projects()
        self.load_patents()
        self.load_publications()
        self.load_salary_rules()

    def load_dashboard(self) -> None:
        metrics = self.service.dashboard_metrics()
        while self.cards.count():
            item = self.cards.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for title, value, color in [
            ("教职工", metrics["employee_count"], "#165dff"),
            ("部门", metrics["department_count"], "#0f766e"),
            ("课程", metrics["course_count"], "#d97706"),
            ("授课", metrics["assignment_count"], "#7c3aed"),
            ("科研", metrics["research_count"], "#dc2626"),
        ]:
            card = QFrame()
            card.setStyleSheet("background:white;border:1px solid #d8e3ef;border-radius:14px;padding:10px;")
            box = QVBoxLayout(card)
            a = QLabel(title)
            b = QLabel(str(value))
            b.setStyleSheet(f"font-size:28px;font-weight:700;color:{color};")
            box.addWidget(a)
            box.addWidget(b)
            self.cards.addWidget(card)
        self.title_stat.setPlainText("职称统计\n" + "\n".join(f"{k}: {v}" for k, v in metrics["title_counter"].items()))
        salary_lines = "\n".join(f"{k}: {v}" for k, v in metrics["salary_counter"].items())
        status_lines = "\n".join(f"{k}: {v}" for k, v in metrics["status_counter"].items())
        current_salary = ""
        if metrics["current_salary_rule"]:
            current_salary = (
                f"\n\n当前账号薪资参考：{metrics['current_salary_rule']['grade']} / "
                f"{metrics['current_salary_total']}"
            )
        self.status_stat.setPlainText("状态统计\n" + status_lines + "\n\n薪资等级统计\n" + salary_lines + current_salary)

    def load_employees(self) -> None:
        self.employee_records = self.service.employees({"keyword": self.employee_keyword.text().strip()})
        self.employee_rows = []
        for item in self.employee_records:
            row = [
                item["employee_no"],
                item["name"],
                item["gender"],
                item["department"],
                item["education"],
                item["degree"],
                item["major"],
                item["title"],
                item["position"],
                item["salary_grade"] or "未定级",
                item["salary_total"] or "待配置",
                item["reward_punishment"] or "暂无",
                item["status"],
                f'{item["phone"]} {item["email"]}'.strip(),
            ]
            self.employee_rows.append(row)
        self._render_table(self.employee_table, self.employee_rows)

    def filter_employees(self) -> None:
        self.load_employees()

    def load_courses(self) -> None:
        self.course_records = self.service.courses()
        rows = [[c["course_no"], c["name"], c["nature"], c["credits"], c["hours"], c["applicable_major"]] for c in self.course_records]
        self._render_table(self.course_table, rows)

    def load_assignments(self) -> None:
        self.assignment_records = self.service.assignments()
        rows = [
            [
                a["teacher"],
                a["course"],
                a["class_name"],
                a["student_count"],
                a["semester"],
                a["department"],
            ]
            for a in self.assignment_records
        ]
        self._render_table(self.assignment_table, rows)

    def load_projects(self) -> None:
        self.project_records = self.service.projects()
        rows = [
            [p["teacher"], p["research_direction"], p["project_no"], p["project_name"], p["sponsor"], f'{p["start_date"]} 至 {p["end_date"]}', p["status"]]
            for p in self.project_records
        ]
        self._render_table(self.project_table, rows)

    def load_patents(self) -> None:
        self.patent_records = self.service.patents()
        rows = [[p["teacher"], p["patent_no"], p["patent_name"], p["grant_date"], p["patent_type"], p["inventors"]] for p in self.patent_records]
        self._render_table(self.patent_table, rows)

    def load_publications(self) -> None:
        self.publication_records = self.service.publications()
        rows = [[p["teacher"], p["work_type"], p["work_name"], p["publisher"], p["publish_date"], p["author_order"], p["isbn_issn"]] for p in self.publication_records]
        self._render_table(self.publication_table, rows)

    def load_salary_rules(self) -> None:
        self.salary_rows = [
            [
                rule["grade"],
                format_currency(rule["base_salary"]),
                format_currency(rule["post_allowance"]),
                format_currency(rule["performance_salary"]),
                format_currency(rule["base_salary"] + rule["post_allowance"] + rule["performance_salary"]),
                rule["applicable_to"],
                rule["description"],
            ]
            for rule in SALARY_RULES
        ]
        self._render_table(self.salary_table, self.salary_rows)
        reward_rows = [
            ["奖励", rule["item"], rule["impact"], rule["note"]]
            for rule in REWARD_RULES
        ] + [
            ["惩处", rule["item"], rule["impact"], rule["note"]]
            for rule in PUNISHMENT_RULES
        ]
        self._render_table(self.reward_table, reward_rows)
        summary = [
            "工资规则说明",
            "1. 参考月薪 = 基础工资 + 岗位津贴 + 绩效工资。",
            "2. 奖惩规则用于系统展示与档案说明，正式执行以学校制度为准。",
        ]
        metrics = self.service.dashboard_metrics()
        if metrics["current_salary_rule"]:
            summary.append(
                f"3. 当前账号对应等级：{metrics['current_salary_rule']['grade']}，参考月薪：{metrics['current_salary_total']}。"
            )
        self.salary_summary.setPlainText("\n".join(summary))

    def _render_table(self, table: QTableWidget, rows: list[list]) -> None:
        table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                item = QTableWidgetItem(_text(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if c == 9 and table is self.employee_table and value != "在职":
                    item.setBackground(QColor("#fef3c7"))
                table.setItem(r, c, item)
        table.resizeColumnsToContents()
        table.resizeRowsToContents()

    def _selected_row(self, table: QTableWidget):
        row = table.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请先选择一行数据")
            return None
        return row

    def _export_rows(self, title: str, headers: list[str], rows: list[list]) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "导出 Excel", "", "Excel 文件 (*.xlsx)")
        if path:
            export_to_excel(title, headers, rows, path)
            QMessageBox.information(self, "完成", f"已导出到 {path}")

    def export_current_view(self) -> None:
        tab = self.tabs.currentIndex()
        if tab == 0:
            metrics = self.service.dashboard_metrics()
            self._export_rows("系统概览", ["指标", "数值"], [["教职工", metrics["employee_count"]], ["部门", metrics["department_count"]], ["课程", metrics["course_count"]], ["授课", metrics["assignment_count"]], ["科研", metrics["research_count"]]])
        elif tab == 1:
            self._export_rows("教职工信息", ["编号", "姓名", "性别", "部门", "学历", "学位", "专业", "职称", "职务", "薪资等级", "参考月薪", "奖惩记录", "状态", "联系方式"], self.employee_rows)
        elif tab == 2:
            self._export_rows("课程信息", ["课程编号", "课程名称", "性质", "学分", "学时", "适用专业"], [[c["course_no"], c["name"], c["nature"], c["credits"], c["hours"], c["applicable_major"]] for c in self.service.courses()])
        elif tab == 3:
            current = self.research_tabs.currentIndex()
            if current == 0:
                self._export_rows("课题信息", ["教师", "研究方向", "课题编号", "课题名称", "立项单位", "起止时间", "状态"], [[p["teacher"], p["research_direction"], p["project_no"], p["project_name"], p["sponsor"], f'{p["start_date"]} 至 {p["end_date"]}', p["status"]] for p in self.service.projects()])
            elif current == 1:
                self._export_rows("专利信息", ["教师", "专利编号", "专利名称", "授权时间", "专利类型", "发明人"], [[p["teacher"], p["patent_no"], p["patent_name"], p["grant_date"], p["patent_type"], p["inventors"]] for p in self.service.patents()])
            else:
                self._export_rows("论文著作", ["教师", "类型", "作品名称", "期刊/出版社", "发表时间", "作者排序", "ISBN/ISSN"], [[p["teacher"], p["work_type"], p["work_name"], p["publisher"], p["publish_date"], p["author_order"], p["isbn_issn"]] for p in self.service.publications()])
        elif tab == 4:
            self._export_rows("工资与奖惩规则", ["等级", "基础工资", "岗位津贴", "绩效工资", "参考月薪", "适用范围", "说明"], self.salary_rows)
        else:
            self._export_rows("数据字典", ["说明", "内容"], [["数据库", "Qt 与 Web 共用同一数据库"]])

    def print_current_view(self) -> None:
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QDialog.Accepted:
            QMessageBox.information(self, "提示", "已打开打印对话框，请在系统打印界面完成输出。")

    def _selected_record_id(self, table: QTableWidget, records: list[dict], title: str) -> int | None:
        row = table.currentRow()
        if row < 0:
            QMessageBox.information(self, title, "请先在表格中选择一条记录")
            return None
        if row >= len(records):
            QMessageBox.warning(self, title, "当前选中记录无效，请刷新后重试")
            return None
        return int(records[row]["id"])

    def _selected_record(self, table: QTableWidget, records: list[dict], title: str):
        row = table.currentRow()
        if row < 0:
            QMessageBox.information(self, title, "请先在表格中选择一条记录")
            return None
        if row >= len(records):
            QMessageBox.warning(self, title, "当前选中记录无效，请刷新后重试")
            return None
        return records[row]

    def add_employee(self):
        departments = [f"{d.id}:{d.name}" for d in self.service.departments()]
        fields = [("text", "employee_no", "教职工编号"), ("text", "name", "姓名"), ("select", "gender", "性别", GENDER_OPTIONS), ("date", "birth_date", "出生日期"), ("text", "education", "学历"), ("text", "degree", "学位"), ("text", "major", "专业"), ("date", "hire_date", "入职时间"), ("select", "department_id", "所属部门", departments), ("text", "title", "职称"), ("text", "position", "职务"), ("select", "salary_grade", "薪资等级", SALARY_GRADE_OPTIONS), ("text", "phone", "联系电话"), ("text", "email", "电子邮箱"), ("select", "status", "状态", EMPLOYEE_STATUSES), ("text", "reward_punishment", "奖惩记录"), ("text", "notes", "备注")]
        dialog = EntityFormDialog("新增教职工", fields, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.data()
            data["department_id"] = data["department_id"].split(":")[0]
            try:
                self.service.save_employee(data)
                self.refresh_all()
            except Exception as exc:
                QMessageBox.critical(self, "失败", str(exc))

    def edit_employee(self):
        selected = self._selected_record(self.employee_table, self.employee_records, "编辑教职工")
        if not selected:
            return
        employee_id = int(selected["id"])
        with self.service.app.app_context():
            employee = db.session.get(Employee, employee_id)
            if employee is None:
                QMessageBox.warning(self, "提示", "记录不存在")
                return
            if not self.service._is_admin() and employee.id != self.service._employee_id():
                QMessageBox.warning(self, "无权限", "普通教师只能修改本人信息")
                return
            departments = [f"{d.id}:{d.name}" for d in self.service.departments()]
            values = {
                "employee_no": employee.employee_no,
                "name": employee.name,
                "gender": employee.gender,
                "birth_date": _date_text(employee.birth_date),
                "education": employee.education,
                "degree": employee.degree,
                "major": employee.major,
                "hire_date": _date_text(employee.hire_date),
                "department_id": f"{employee.department_id}:{selected.get('department', '')}",
                "title": employee.title,
                "position": employee.position,
                "salary_grade": employee.salary_grade,
                "phone": employee.phone,
                "email": employee.email,
                "status": employee.status,
                "reward_punishment": employee.reward_punishment,
                "notes": employee.notes,
            }
        fields = [("text", "employee_no", "教职工编号"), ("text", "name", "姓名"), ("select", "gender", "性别", GENDER_OPTIONS), ("date", "birth_date", "出生日期"), ("text", "education", "学历"), ("text", "degree", "学位"), ("text", "major", "专业"), ("date", "hire_date", "入职时间"), ("select", "department_id", "所属部门", departments), ("text", "title", "职称"), ("text", "position", "职务"), ("select", "salary_grade", "薪资等级", SALARY_GRADE_OPTIONS), ("text", "phone", "联系电话"), ("text", "email", "电子邮箱"), ("select", "status", "状态", EMPLOYEE_STATUSES), ("text", "reward_punishment", "奖惩记录"), ("text", "notes", "备注")]
        dialog = EntityFormDialog("编辑教职工", fields, values, self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.data()
            data["department_id"] = data["department_id"].split(":")[0]
            try:
                self.service.save_employee(data, employee_id)
                self.refresh_all()
            except Exception as exc:
                QMessageBox.critical(self, "失败", str(exc))

    def deactivate_employee(self):
        employee_id = self._selected_record_id(self.employee_table, self.employee_records, "注销教职工")
        if not employee_id:
            return
        status, ok = QInputDialog.getItem(self, "注销状态", "选择状态", EMPLOYEE_STATUSES[1:], 0, False)
        if ok:
            try:
                self.service.deactivate_employee(employee_id, status)
                self.refresh_all()
            except Exception as exc:
                QMessageBox.critical(self, "失败", str(exc))

    def add_course(self):
        fields = [("text", "course_no", "课程编号"), ("text", "name", "课程名称"), ("select", "nature", "课程性质", COURSE_NATURES), ("number", "credits", "学分"), ("number", "hours", "课程时数"), ("text", "applicable_major", "适用专业"), ("text", "description", "课程说明")]
        dialog = EntityFormDialog("新增课程", fields, parent=self)
        if dialog.exec() == QDialog.Accepted:
            try:
                self.service.save_course(dialog.data())
                self.refresh_all()
            except Exception as exc:
                QMessageBox.critical(self, "失败", str(exc))

    def edit_course(self):
        course_id = self._selected_record_id(self.course_table, self.course_records, "编辑课程")
        if not course_id:
            return
        with self.service.app.app_context():
            course = db.session.get(Course, course_id)
        if not course:
            return
        values = {
            "course_no": course.course_no,
            "name": course.name,
            "nature": course.nature,
            "credits": course.credits,
            "hours": course.hours,
            "applicable_major": course.applicable_major,
            "description": course.description,
        }
        fields = [("text", "course_no", "课程编号"), ("text", "name", "课程名称"), ("select", "nature", "课程性质", COURSE_NATURES), ("number", "credits", "学分"), ("number", "hours", "课程时数"), ("text", "applicable_major", "适用专业"), ("text", "description", "课程说明")]
        dialog = EntityFormDialog("编辑课程", fields, values, self)
        if dialog.exec() == QDialog.Accepted:
            try:
                self.service.save_course(dialog.data(), course_id)
                self.refresh_all()
            except Exception as exc:
                QMessageBox.critical(self, "失败", str(exc))

    def delete_course(self):
        course_id = self._selected_record_id(self.course_table, self.course_records, "删除课程")
        if course_id and QMessageBox.question(self, "确认", "确定删除该课程？") == QMessageBox.Yes:
            try:
                self.service.delete_course(course_id)
                self.refresh_all()
            except Exception as exc:
                QMessageBox.critical(self, "失败", str(exc))

    def add_assignment(self):
        employees = [f'{e["id"]}:{e["name"]}' for e in self.service.employees_lookup()]
        courses = [f'{c["id"]}:{c["name"]}' for c in self.service.course_lookup()]
        fields = [("select", "employee_id", "教师", employees), ("select", "course_id", "课程", courses), ("text", "class_name", "授课班级"), ("number", "student_count", "学生人数"), ("text", "semester", "学期")]
        dialog = EntityFormDialog("新增授课", fields, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.data()
            data["employee_id"] = data["employee_id"].split(":")[0]
            data["course_id"] = data["course_id"].split(":")[0]
            try:
                self.service.save_assignment(data)
                self.refresh_all()
            except Exception as exc:
                QMessageBox.critical(self, "失败", str(exc))

    def edit_assignment(self):
        selected = self._selected_record(self.assignment_table, self.assignment_records, "编辑授课")
        if not selected:
            return
        assignment_id = int(selected["id"])
        with self.service.app.app_context():
            assignment = db.session.get(TeachingAssignment, assignment_id)
        if not assignment:
            return
        employees = [f'{e["id"]}:{e["name"]}' for e in self.service.employees_lookup()]
        courses = [f'{c["id"]}:{c["name"]}' for c in self.service.course_lookup()]
        values = {"employee_id": f"{assignment.employee_id}:{selected.get('teacher', '')}", "course_id": f"{assignment.course_id}:{selected.get('course', '')}", "class_name": assignment.class_name, "student_count": assignment.student_count, "semester": assignment.semester}
        fields = [("select", "employee_id", "教师", employees), ("select", "course_id", "课程", courses), ("text", "class_name", "授课班级"), ("number", "student_count", "学生人数"), ("text", "semester", "学期")]
        dialog = EntityFormDialog("编辑授课", fields, values, self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.data()
            data["employee_id"] = data["employee_id"].split(":")[0]
            data["course_id"] = data["course_id"].split(":")[0]
            try:
                self.service.save_assignment(data, assignment_id)
                self.refresh_all()
            except Exception as exc:
                QMessageBox.critical(self, "失败", str(exc))

    def delete_assignment(self):
        assignment_id = self._selected_record_id(self.assignment_table, self.assignment_records, "删除授课")
        if assignment_id and QMessageBox.question(self, "确认", "确定删除该授课任务？") == QMessageBox.Yes:
            try:
                self.service.delete_assignment(assignment_id)
                self.refresh_all()
            except Exception as exc:
                QMessageBox.critical(self, "失败", str(exc))

    def add_project(self):
        employees = [f'{e["id"]}:{e["name"]}' for e in self.service.employees_lookup()]
        fields = [("select", "employee_id", "教师", employees), ("text", "research_direction", "研究方向"), ("text", "project_no", "课题编号"), ("text", "project_name", "课题名称"), ("text", "sponsor", "立项单位"), ("date", "start_date", "立项时间"), ("date", "end_date", "结题时间"), ("select", "status", "状态", RESEARCH_STATUSES)]
        dialog = EntityFormDialog("新增课题", fields, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.data()
            data["employee_id"] = data["employee_id"].split(":")[0]
            try:
                self.service.save_project(data)
                self.refresh_all()
            except Exception as exc:
                QMessageBox.critical(self, "失败", str(exc))

    def edit_project(self):
        selected = self._selected_record(self.project_table, self.project_records, "编辑课题")
        if not selected:
            return
        project_id = int(selected["id"])
        with self.service.app.app_context():
            record = db.session.get(ResearchProject, project_id)
        if not record:
            return
        employees = [f'{e["id"]}:{e["name"]}' for e in self.service.employees_lookup()]
        values = {"employee_id": f"{record.employee_id}:{selected.get('teacher', '')}", "research_direction": record.research_direction, "project_no": record.project_no, "project_name": record.project_name, "sponsor": record.sponsor, "start_date": _date_text(record.start_date), "end_date": _date_text(record.end_date), "status": record.status}
        fields = [("select", "employee_id", "教师", employees), ("text", "research_direction", "研究方向"), ("text", "project_no", "课题编号"), ("text", "project_name", "课题名称"), ("text", "sponsor", "立项单位"), ("date", "start_date", "立项时间"), ("date", "end_date", "结题时间"), ("select", "status", "状态", RESEARCH_STATUSES)]
        dialog = EntityFormDialog("编辑课题", fields, values, self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.data()
            data["employee_id"] = data["employee_id"].split(":")[0]
            try:
                self.service.save_project(data, project_id)
                self.refresh_all()
            except Exception as exc:
                QMessageBox.critical(self, "失败", str(exc))

    def delete_project(self):
        project_id = self._selected_record_id(self.project_table, self.project_records, "删除课题")
        if project_id and QMessageBox.question(self, "确认", "确定删除该课题？") == QMessageBox.Yes:
            try:
                self.service.delete_project(project_id)
                self.refresh_all()
            except Exception as exc:
                QMessageBox.critical(self, "失败", str(exc))

    def add_patent(self):
        employees = [f'{e["id"]}:{e["name"]}' for e in self.service.employees_lookup()]
        fields = [("select", "employee_id", "教师", employees), ("text", "patent_no", "专利编号"), ("text", "patent_name", "专利名称"), ("date", "grant_date", "授权时间"), ("text", "patent_type", "专利类型"), ("text", "inventors", "发明人")]
        dialog = EntityFormDialog("新增专利", fields, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.data()
            data["employee_id"] = data["employee_id"].split(":")[0]
            try:
                self.service.save_patent(data)
                self.refresh_all()
            except Exception as exc:
                QMessageBox.critical(self, "失败", str(exc))

    def edit_patent(self):
        selected = self._selected_record(self.patent_table, self.patent_records, "编辑专利")
        if not selected:
            return
        patent_id = int(selected["id"])
        with self.service.app.app_context():
            record = db.session.get(Patent, patent_id)
        if not record:
            return
        employees = [f'{e["id"]}:{e["name"]}' for e in self.service.employees_lookup()]
        values = {"employee_id": f"{record.employee_id}:{selected.get('teacher', '')}", "patent_no": record.patent_no, "patent_name": record.patent_name, "grant_date": _date_text(record.grant_date), "patent_type": record.patent_type, "inventors": record.inventors}
        fields = [("select", "employee_id", "教师", employees), ("text", "patent_no", "专利编号"), ("text", "patent_name", "专利名称"), ("date", "grant_date", "授权时间"), ("text", "patent_type", "专利类型"), ("text", "inventors", "发明人")]
        dialog = EntityFormDialog("编辑专利", fields, values, self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.data()
            data["employee_id"] = data["employee_id"].split(":")[0]
            try:
                self.service.save_patent(data, patent_id)
                self.refresh_all()
            except Exception as exc:
                QMessageBox.critical(self, "失败", str(exc))

    def delete_patent(self):
        patent_id = self._selected_record_id(self.patent_table, self.patent_records, "删除专利")
        if patent_id and QMessageBox.question(self, "确认", "确定删除该专利？") == QMessageBox.Yes:
            try:
                self.service.delete_patent(patent_id)
                self.refresh_all()
            except Exception as exc:
                QMessageBox.critical(self, "失败", str(exc))

    def add_publication(self):
        employees = [f'{e["id"]}:{e["name"]}' for e in self.service.employees_lookup()]
        fields = [("select", "employee_id", "教师", employees), ("text", "work_name", "作品名称"), ("text", "publisher", "期刊/出版社"), ("date", "publish_date", "发表时间"), ("text", "author_order", "作者排序"), ("text", "isbn_issn", "ISBN/ISSN"), ("select", "work_type", "类型", PUBLICATION_TYPES)]
        dialog = EntityFormDialog("新增成果", fields, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.data()
            data["employee_id"] = data["employee_id"].split(":")[0]
            try:
                self.service.save_publication(data)
                self.refresh_all()
            except Exception as exc:
                QMessageBox.critical(self, "失败", str(exc))

    def edit_publication(self):
        selected = self._selected_record(self.publication_table, self.publication_records, "编辑成果")
        if not selected:
            return
        publication_id = int(selected["id"])
        with self.service.app.app_context():
            record = db.session.get(Publication, publication_id)
        if not record:
            return
        employees = [f'{e["id"]}:{e["name"]}' for e in self.service.employees_lookup()]
        values = {"employee_id": f"{record.employee_id}:{selected.get('teacher', '')}", "work_name": record.work_name, "publisher": record.publisher, "publish_date": _date_text(record.publish_date), "author_order": record.author_order, "isbn_issn": record.isbn_issn, "work_type": record.work_type}
        fields = [("select", "employee_id", "教师", employees), ("text", "work_name", "作品名称"), ("text", "publisher", "期刊/出版社"), ("date", "publish_date", "发表时间"), ("text", "author_order", "作者排序"), ("text", "isbn_issn", "ISBN/ISSN"), ("select", "work_type", "类型", PUBLICATION_TYPES)]
        dialog = EntityFormDialog("编辑成果", fields, values, self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.data()
            data["employee_id"] = data["employee_id"].split(":")[0]
            try:
                self.service.save_publication(data, publication_id)
                self.refresh_all()
            except Exception as exc:
                QMessageBox.critical(self, "失败", str(exc))

    def delete_publication(self):
        publication_id = self._selected_record_id(self.publication_table, self.publication_records, "删除成果")
        if publication_id and QMessageBox.question(self, "确认", "确定删除该成果？") == QMessageBox.Yes:
            try:
                self.service.delete_publication(publication_id)
                self.refresh_all()
            except Exception as exc:
                QMessageBox.critical(self, "失败", str(exc))

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #f3f7fb; color: #132238; font-family: 'Microsoft YaHei'; font-size: 14px; }
            QLabel { font-size: 14px; }
            QTabWidget::pane { border: 1px solid #d8e3ef; border-radius: 12px; background: white; }
            QTabBar::tab { padding: 10px 16px; background: #eaf1fb; margin-right: 4px; border-top-left-radius: 8px; border-top-right-radius: 8px; }
            QTabBar::tab:selected { background: #165dff; color: white; }
            QLineEdit, QComboBox, QDateEdit, QTextEdit { background: white; border: 1px solid #d6dfeb; border-radius: 8px; padding: 6px 8px; }
            QPushButton { background: #165dff; color: white; border: none; padding: 8px 12px; border-radius: 8px; }
            QPushButton:hover { background: #0f4bd8; }
            QTableWidget { background: white; border: 1px solid #d6dfeb; border-radius: 10px; }
            QHeaderView::section { background: #eef4fb; padding: 8px; border: none; font-weight: 700; }
            """
        )


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("高校人事信息管理系统")
    service = DataService()
    login = LoginDialog(service)
    if login.exec() != QDialog.Accepted or not login.user:
        return 0
    window = DesktopWindow(login.user)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
