from __future__ import annotations

from datetime import date

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, Index, String, Text
from sqlalchemy.orm import relationship
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import Base


class TimestampMixin:
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="teacher", index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))

    employee = relationship("Employee", back_populates="user", uselist=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Department(TimestampMixin, Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255))

    employees = relationship("Employee", back_populates="department")


class Employee(TimestampMixin, Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True)
    employee_no = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(50), nullable=False)
    gender = Column(String(10), nullable=False)
    birth_date = Column(Date)
    education = Column(String(50), index=True)
    degree = Column(String(50))
    major = Column(String(100))
    hire_date = Column(Date)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    title = Column(String(50), index=True)
    position = Column(String(50))
    salary_grade = Column(String(20))
    phone = Column(String(30))
    email = Column(String(120))
    reward_punishment = Column(Text)
    status = Column(String(20), nullable=False, default="在职", index=True)
    notes = Column(Text)

    department = relationship("Department", back_populates="employees")
    user = relationship("User", back_populates="employee", uselist=False)
    course_assignments = relationship("TeachingAssignment", back_populates="employee")
    research_projects = relationship("ResearchProject", back_populates="employee")
    patents = relationship("Patent", back_populates="employee")
    publications = relationship("Publication", back_populates="employee")

    @property
    def age(self) -> int | None:
        if not self.birth_date:
            return None
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )


class Course(TimestampMixin, Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)
    course_no = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    nature = Column(String(20), nullable=False, index=True)
    credits = Column(Float, nullable=False, default=0)
    hours = Column(Integer, nullable=False, default=0)
    applicable_major = Column(String(100))
    description = Column(Text)

    assignments = relationship("TeachingAssignment", back_populates="course")


class TeachingAssignment(TimestampMixin, Base):
    __tablename__ = "teaching_assignments"

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    class_name = Column(String(100), nullable=False)
    student_count = Column(Integer, nullable=False, default=0)
    semester = Column(String(30), nullable=False, index=True)

    employee = relationship("Employee", back_populates="course_assignments")
    course = relationship("Course", back_populates="assignments")


class ResearchProject(TimestampMixin, Base):
    __tablename__ = "research_projects"

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    research_direction = Column(String(150), nullable=False)
    project_no = Column(String(32), unique=True, nullable=False, index=True)
    project_name = Column(String(150), nullable=False, index=True)
    sponsor = Column(String(100))
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(String(20), nullable=False, default="进行中", index=True)

    employee = relationship("Employee", back_populates="research_projects")


class Patent(TimestampMixin, Base):
    __tablename__ = "patents"

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    patent_no = Column(String(32), unique=True, nullable=False, index=True)
    patent_name = Column(String(150), nullable=False, index=True)
    grant_date = Column(Date)
    patent_type = Column(String(50))
    inventors = Column(String(255))

    employee = relationship("Employee", back_populates="patents")


class Publication(TimestampMixin, Base):
    __tablename__ = "publications"

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    work_name = Column(String(150), nullable=False, index=True)
    publisher = Column(String(150))
    publish_date = Column(Date)
    author_order = Column(String(50))
    isbn_issn = Column(String(50))
    work_type = Column(String(20), nullable=False, default="论文")

    employee = relationship("Employee", back_populates="publications")


Index("ix_teaching_employee_course", TeachingAssignment.employee_id, TeachingAssignment.course_id)
Index("ix_research_employee_project", ResearchProject.employee_id, ResearchProject.project_no)
