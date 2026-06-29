"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-27
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column("description", sa.String(length=255)),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )

    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_no", sa.String(length=32), nullable=False, unique=True),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("gender", sa.String(length=10), nullable=False),
        sa.Column("birth_date", sa.Date()),
        sa.Column("education", sa.String(length=50)),
        sa.Column("degree", sa.String(length=50)),
        sa.Column("major", sa.String(length=100)),
        sa.Column("hire_date", sa.Date()),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("title", sa.String(length=50)),
        sa.Column("position", sa.String(length=50)),
        sa.Column("salary_grade", sa.String(length=20)),
        sa.Column("phone", sa.String(length=30)),
        sa.Column("email", sa.String(length=120)),
        sa.Column("reward_punishment", sa.Text()),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_index("ix_employees_education", "employees", ["education"], unique=False)
    op.create_index("ix_employees_title", "employees", ["title"], unique=False)
    op.create_index("ix_employees_status", "employees", ["status"], unique=False)

    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_no", sa.String(length=32), nullable=False, unique=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("nature", sa.String(length=20), nullable=False),
        sa.Column("credits", sa.Float(), nullable=False),
        sa.Column("hours", sa.Integer(), nullable=False),
        sa.Column("applicable_major", sa.String(length=100)),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_index("ix_courses_name", "courses", ["name"], unique=False)
    op.create_index("ix_courses_nature", "courses", ["nature"], unique=False)

    op.create_table(
        "research_projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("research_direction", sa.String(length=150), nullable=False),
        sa.Column("project_no", sa.String(length=32), nullable=False, unique=True),
        sa.Column("project_name", sa.String(length=150), nullable=False),
        sa.Column("sponsor", sa.String(length=100)),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_index("ix_research_projects_project_name", "research_projects", ["project_name"], unique=False)
    op.create_index("ix_research_projects_status", "research_projects", ["status"], unique=False)
    op.create_index("ix_research_employee_project", "research_projects", ["employee_id", "project_no"], unique=False)

    op.create_table(
        "patents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("patent_no", sa.String(length=32), nullable=False, unique=True),
        sa.Column("patent_name", sa.String(length=150), nullable=False),
        sa.Column("grant_date", sa.Date()),
        sa.Column("patent_type", sa.String(length=50)),
        sa.Column("inventors", sa.String(length=255)),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_index("ix_patents_patent_name", "patents", ["patent_name"], unique=False)

    op.create_table(
        "publications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("work_name", sa.String(length=150), nullable=False),
        sa.Column("publisher", sa.String(length=150)),
        sa.Column("publish_date", sa.Date()),
        sa.Column("author_order", sa.String(length=50)),
        sa.Column("isbn_issn", sa.String(length=50)),
        sa.Column("work_type", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_index("ix_publications_work_name", "publications", ["work_name"], unique=False)

    op.create_table(
        "teaching_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("class_name", sa.String(length=100), nullable=False),
        sa.Column("student_count", sa.Integer(), nullable=False),
        sa.Column("semester", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_index("ix_teaching_assignments_semester", "teaching_assignments", ["semester"], unique=False)
    op.create_index("ix_teaching_employee_course", "teaching_assignments", ["employee_id", "course_id"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=64), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id")),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_index("ix_users_role", "users", ["role"], unique=False)


def downgrade():
    op.drop_index("ix_users_role", table_name="users")
    op.drop_table("users")
    op.drop_index("ix_teaching_employee_course", table_name="teaching_assignments")
    op.drop_index("ix_teaching_assignments_semester", table_name="teaching_assignments")
    op.drop_table("teaching_assignments")
    op.drop_index("ix_publications_work_name", table_name="publications")
    op.drop_table("publications")
    op.drop_index("ix_patents_patent_name", table_name="patents")
    op.drop_index("ix_patents_patent_no", table_name="patents")
    op.drop_table("patents")
    op.drop_index("ix_research_employee_project", table_name="research_projects")
    op.drop_index("ix_research_projects_status", table_name="research_projects")
    op.drop_index("ix_research_projects_project_name", table_name="research_projects")
    op.drop_index("ix_research_projects_project_no", table_name="research_projects")
    op.drop_table("research_projects")
    op.drop_index("ix_courses_nature", table_name="courses")
    op.drop_index("ix_courses_name", table_name="courses")
    op.drop_table("courses")
    op.drop_index("ix_employees_status", table_name="employees")
    op.drop_index("ix_employees_title", table_name="employees")
    op.drop_index("ix_employees_education", table_name="employees")
    op.drop_table("employees")
    op.drop_table("departments")
