from datetime import datetime

from models import Course, Department, Employee, Patent, Publication, ResearchProject, TeachingAssignment, User
from utils import parse_date


DEPARTMENT_DATA = [
    ("计算机学院", "负责计算机类专业教学、科研与实验平台建设"),
    ("数学学院", "负责数学、统计学相关专业教学与科研"),
    ("外国语学院", "负责语言教学、国际合作与学科建设"),
    ("机电工程学院", "负责机电、自动化方向人才培养"),
    ("经济管理学院", "负责经管类专业教学与实践基地建设"),
    ("教务处", "负责学校教学运行与课程管理"),
]


EMPLOYEE_DATA = [
    {
        "employee_no": "T2024001",
        "name": "张敏",
        "gender": "女",
        "birth_date": "1985-03-12",
        "education": "研究生",
        "degree": "博士",
        "major": "计算机科学与技术",
        "hire_date": "2012-09-01",
        "department": "计算机学院",
        "title": "教授",
        "position": "系主任",
        "salary_grade": "G8",
        "phone": "13800000001",
        "email": "zhangmin@example.edu.cn",
        "reward_punishment": "2023年获省级教学成果二等奖",
        "status": "在职",
    },
    {
        "employee_no": "T2024002",
        "name": "李强",
        "gender": "男",
        "birth_date": "1989-08-25",
        "education": "研究生",
        "degree": "硕士",
        "major": "软件工程",
        "hire_date": "2016-07-15",
        "department": "计算机学院",
        "title": "副教授",
        "position": "专业负责人",
        "salary_grade": "G6",
        "phone": "13800000002",
        "email": "liqiang@example.edu.cn",
        "reward_punishment": "2024年指导学生竞赛获国家级奖项",
        "status": "在职",
    },
    {
        "employee_no": "T2024003",
        "name": "王雪",
        "gender": "女",
        "birth_date": "1978-11-03",
        "education": "研究生",
        "degree": "博士",
        "major": "应用数学",
        "hire_date": "2008-03-10",
        "department": "数学学院",
        "title": "教授",
        "position": "教师",
        "salary_grade": "G7",
        "phone": "13800000003",
        "email": "wangxue@example.edu.cn",
        "reward_punishment": "2022年获校级优秀教师",
        "status": "退休",
    },
    {
        "employee_no": "T2024004",
        "name": "陈磊",
        "gender": "男",
        "birth_date": "1982-01-17",
        "education": "研究生",
        "degree": "博士",
        "major": "人工智能",
        "hire_date": "2011-04-08",
        "department": "计算机学院",
        "title": "教授",
        "position": "实验中心主任",
        "salary_grade": "G8",
        "phone": "13800000004",
        "email": "chenlei@example.edu.cn",
        "reward_punishment": "2021年获省科技进步三等奖",
        "status": "在职",
    },
    {
        "employee_no": "T2024005",
        "name": "赵琳",
        "gender": "女",
        "birth_date": "1990-06-22",
        "education": "研究生",
        "degree": "硕士",
        "major": "数据科学",
        "hire_date": "2018-09-10",
        "department": "计算机学院",
        "title": "讲师",
        "position": "教师",
        "salary_grade": "G4",
        "phone": "13800000005",
        "email": "zhaolin@example.edu.cn",
        "reward_punishment": "2024年获青年教师教学竞赛一等奖",
        "status": "在职",
    },
    {
        "employee_no": "T2024006",
        "name": "孙浩",
        "gender": "男",
        "birth_date": "1987-09-14",
        "education": "研究生",
        "degree": "博士",
        "major": "控制工程",
        "hire_date": "2014-02-18",
        "department": "机电工程学院",
        "title": "副教授",
        "position": "教研室主任",
        "salary_grade": "G6",
        "phone": "13800000006",
        "email": "sunhao@example.edu.cn",
        "reward_punishment": "主持省级教改项目1项",
        "status": "在职",
    },
    {
        "employee_no": "T2024007",
        "name": "周妍",
        "gender": "女",
        "birth_date": "1992-12-09",
        "education": "研究生",
        "degree": "硕士",
        "major": "英语语言文学",
        "hire_date": "2019-08-26",
        "department": "外国语学院",
        "title": "讲师",
        "position": "教师",
        "salary_grade": "G4",
        "phone": "13800000007",
        "email": "zhouyan@example.edu.cn",
        "reward_punishment": "获校级课程思政示范课",
        "status": "在职",
    },
    {
        "employee_no": "T2024008",
        "name": "刘洋",
        "gender": "男",
        "birth_date": "1984-07-19",
        "education": "研究生",
        "degree": "博士",
        "major": "金融学",
        "hire_date": "2010-11-12",
        "department": "经济管理学院",
        "title": "教授",
        "position": "院长助理",
        "salary_grade": "G7",
        "phone": "13800000008",
        "email": "liuyang@example.edu.cn",
        "reward_punishment": "获省哲社优秀成果奖",
        "status": "在职",
    },
    {
        "employee_no": "T2024009",
        "name": "许晴",
        "gender": "女",
        "birth_date": "1988-04-03",
        "education": "研究生",
        "degree": "硕士",
        "major": "会计学",
        "hire_date": "2015-03-09",
        "department": "经济管理学院",
        "title": "副教授",
        "position": "教师",
        "salary_grade": "G5",
        "phone": "13800000009",
        "email": "xuqing@example.edu.cn",
        "reward_punishment": "2023年获教学优秀奖",
        "status": "在职",
    },
    {
        "employee_no": "T2024010",
        "name": "高翔",
        "gender": "男",
        "birth_date": "1979-02-27",
        "education": "研究生",
        "degree": "博士",
        "major": "统计学",
        "hire_date": "2007-06-21",
        "department": "数学学院",
        "title": "教授",
        "position": "副院长",
        "salary_grade": "G8",
        "phone": "13800000010",
        "email": "gaoxiang@example.edu.cn",
        "reward_punishment": "国家自然科学基金项目负责人",
        "status": "在职",
    },
    {
        "employee_no": "T2024011",
        "name": "唐婧",
        "gender": "女",
        "birth_date": "1991-05-16",
        "education": "研究生",
        "degree": "硕士",
        "major": "翻译",
        "hire_date": "2020-09-01",
        "department": "外国语学院",
        "title": "助教",
        "position": "教师",
        "salary_grade": "G3",
        "phone": "13800000011",
        "email": "tangjing@example.edu.cn",
        "reward_punishment": "参与国际合作课程建设",
        "status": "在职",
    },
    {
        "employee_no": "T2024012",
        "name": "顾峰",
        "gender": "男",
        "birth_date": "1986-10-31",
        "education": "研究生",
        "degree": "博士",
        "major": "机械设计制造",
        "hire_date": "2013-01-14",
        "department": "机电工程学院",
        "title": "副教授",
        "position": "教师",
        "salary_grade": "G6",
        "phone": "13800000012",
        "email": "gufeng@example.edu.cn",
        "reward_punishment": "获得发明专利授权2项",
        "status": "在职",
    },
]


COURSE_DATA = [
    ("C001", "数据库原理", "必修", 3.0, 48, "计算机科学与技术", "讲授关系模型、SQL 与数据库设计。"),
    ("C002", "Python程序设计", "通识", 2.0, 32, "全校选修", "培养基础编程能力。"),
    ("C003", "高等数学", "必修", 4.0, 64, "工科类专业", "数学基础课程。"),
    ("C004", "人工智能导论", "选修", 2.5, 40, "计算机类专业", "介绍机器学习与智能系统基本概念。"),
    ("C005", "自动控制原理", "必修", 3.5, 56, "自动化专业", "控制系统理论与工程应用。"),
    ("C006", "大学英语口语", "通识", 2.0, 32, "全校本科生", "提升英语表达与交流能力。"),
    ("C007", "财务管理", "必修", 3.0, 48, "经管类专业", "企业财务管理与分析基础。"),
    ("C008", "概率论与数理统计", "必修", 3.5, 56, "理工科专业", "概率与统计建模基础。"),
]


TEACHING_ASSIGNMENT_DATA = [
    ("T2024001", "C001", "计科2301", 52, "2025-2026-1"),
    ("T2024002", "C002", "通识2402", 86, "2025-2026-2"),
    ("T2024003", "C003", "自动化2303", 60, "2025-2026-1"),
    ("T2024004", "C004", "计科2202", 48, "2025-2026-1"),
    ("T2024005", "C002", "大数据2401", 58, "2025-2026-1"),
    ("T2024006", "C005", "机电2301", 64, "2025-2026-2"),
    ("T2024007", "C006", "英语口语2304", 92, "2025-2026-1"),
    ("T2024008", "C007", "金融2301", 71, "2025-2026-1"),
    ("T2024010", "C008", "数学2302", 66, "2025-2026-2"),
]


PROJECT_DATA = [
    ("T2024001", "教育大数据与智能分析", "P2025001", "高校教学数据治理关键技术研究", "省教育厅", "2025-01-10", "2026-12-31", "进行中"),
    ("T2024002", "软件测试自动化", "P2024008", "面向教学平台的自动化测试框架研究", "校级科研基金", "2024-04-01", "2025-11-30", "结题"),
    ("T2024004", "智能视觉检测", "P2025002", "实验教学设备视觉识别系统研究", "市科技局", "2025-02-01", "2027-01-31", "进行中"),
    ("T2024006", "工业控制优化", "P2024013", "复杂机电系统节能控制算法研究", "企业横向项目", "2024-07-15", "2026-07-14", "进行中"),
    ("T2024008", "区域经济分析", "P2024015", "数字经济背景下地方产业升级路径研究", "省哲社基金", "2024-05-01", "2026-04-30", "进行中"),
    ("T2024010", "统计建模", "P2024018", "高维数据统计推断方法研究", "国家自然科学基金", "2024-09-01", "2027-08-31", "进行中"),
]


PATENT_DATA = [
    ("T2024001", "ZL202510001", "一种教师科研成果归档方法", "2025-09-18", "发明专利", "张敏;李强"),
    ("T2024002", "ZL202410123", "一种实验教学管理辅助系统", "2024-10-05", "实用新型", "李强"),
    ("T2024004", "ZL202510002", "一种实验室设备异常检测方法", "2025-11-10", "发明专利", "陈磊;赵琳"),
    ("T2024012", "ZL202410888", "一种机电设备装配定位夹具", "2024-12-22", "实用新型", "顾峰"),
]


PUBLICATION_DATA = [
    ("T2024001", "高校人事数据治理框架研究", "中国教育信息化", "2025-06-01", "第一作者", "ISSN 1000-0001", "论文"),
    ("T2024002", "Python在教学管理系统中的实践", "高等教育出版社", "2024-12-20", "独著", "ISBN 978-7-000-00000-0", "著作"),
    ("T2024004", "人工智能实验课程建设研究", "现代教育技术", "2025-03-12", "第一作者", "ISSN 1002-1234", "论文"),
    ("T2024008", "地方高校经管人才培养模式创新", "经济管理出版社", "2024-10-08", "主编", "ISBN 978-7-111-22222-3", "著作"),
    ("T2024010", "高维数据统计分析方法综述", "统计研究", "2025-01-15", "通讯作者", "ISSN 1002-4567", "论文"),
]


def seed_database(db):
    now = datetime.utcnow()

    dept_map = {item.name: item for item in Department.query.all()}
    for name, description in DEPARTMENT_DATA:
        if name not in dept_map:
            department = Department(name=name, description=description, created_at=now, updated_at=now)
            db.session.add(department)
            db.session.flush()
            dept_map[name] = department

    employee_map = {item.employee_no: item for item in Employee.query.all()}
    for item in EMPLOYEE_DATA:
        if item["employee_no"] not in employee_map:
            employee = Employee(
                employee_no=item["employee_no"],
                name=item["name"],
                gender=item["gender"],
                birth_date=parse_date(item["birth_date"]),
                education=item["education"],
                degree=item["degree"],
                major=item["major"],
                hire_date=parse_date(item["hire_date"]),
                department_id=dept_map[item["department"]].id,
                title=item["title"],
                position=item["position"],
                salary_grade=item["salary_grade"],
                phone=item["phone"],
                email=item["email"],
                reward_punishment=item["reward_punishment"],
                status=item["status"],
                created_at=now,
                updated_at=now,
            )
            db.session.add(employee)
            db.session.flush()
            employee_map[item["employee_no"]] = employee

    course_map = {item.course_no: item for item in Course.query.all()}
    for course_no, name, nature, credits, hours, applicable_major, description in COURSE_DATA:
        if course_no not in course_map:
            course = Course(
                course_no=course_no,
                name=name,
                nature=nature,
                credits=credits,
                hours=hours,
                applicable_major=applicable_major,
                description=description,
                created_at=now,
                updated_at=now,
            )
            db.session.add(course)
            db.session.flush()
            course_map[course_no] = course

    if not TeachingAssignment.query.first():
        for employee_no, course_no, class_name, student_count, semester in TEACHING_ASSIGNMENT_DATA:
            db.session.add(
                TeachingAssignment(
                    employee_id=employee_map[employee_no].id,
                    course_id=course_map[course_no].id,
                    class_name=class_name,
                    student_count=student_count,
                    semester=semester,
                    created_at=now,
                    updated_at=now,
                )
            )

    if not ResearchProject.query.first():
        for employee_no, direction, project_no, project_name, sponsor, start_date, end_date, status in PROJECT_DATA:
            db.session.add(
                ResearchProject(
                    employee_id=employee_map[employee_no].id,
                    research_direction=direction,
                    project_no=project_no,
                    project_name=project_name,
                    sponsor=sponsor,
                    start_date=parse_date(start_date),
                    end_date=parse_date(end_date),
                    status=status,
                    created_at=now,
                    updated_at=now,
                )
            )

    if not Patent.query.first():
        for employee_no, patent_no, patent_name, grant_date, patent_type, inventors in PATENT_DATA:
            db.session.add(
                Patent(
                    employee_id=employee_map[employee_no].id,
                    patent_no=patent_no,
                    patent_name=patent_name,
                    grant_date=parse_date(grant_date),
                    patent_type=patent_type,
                    inventors=inventors,
                    created_at=now,
                    updated_at=now,
                )
            )

    if not Publication.query.first():
        for employee_no, work_name, publisher, publish_date, author_order, isbn_issn, work_type in PUBLICATION_DATA:
            db.session.add(
                Publication(
                    employee_id=employee_map[employee_no].id,
                    work_name=work_name,
                    publisher=publisher,
                    publish_date=parse_date(publish_date),
                    author_order=author_order,
                    isbn_issn=isbn_issn,
                    work_type=work_type,
                    created_at=now,
                    updated_at=now,
                )
            )

    if not User.query.filter_by(username="admin").first():
        admin = User(
            username="admin",
            role="admin",
            employee_id=employee_map["T2024001"].id,
            created_at=now,
            updated_at=now,
        )
        admin.set_password("admin123")
        db.session.add(admin)

    legacy_teacher = User.query.filter_by(username="teacher").first()
    if legacy_teacher:
        db.session.delete(legacy_teacher)

    for employee in employee_map.values():
        username = employee.employee_no
        if not User.query.filter_by(username=username).first():
            user = User(
                username=username,
                role="teacher",
                employee_id=employee.id,
                created_at=now,
                updated_at=now,
            )
            user.set_password(f"{employee.employee_no}@123")
            db.session.add(user)

    db.session.commit()
