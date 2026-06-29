from __future__ import annotations

EMPLOYEE_STATUSES = ["在职", "退休", "转出", "辞退"]
GENDER_OPTIONS = ["男", "女"]
COURSE_NATURES = ["必修", "选修", "通识"]
RESEARCH_STATUSES = ["进行中", "结题", "暂缓"]
PUBLICATION_TYPES = ["论文", "著作"]

SALARY_RULES = [
    {
        "grade": "G3",
        "base_salary": 4200,
        "post_allowance": 700,
        "performance_salary": 600,
        "applicable_to": "助教、试用期教师",
        "description": "适用于初级教学辅助岗位。",
    },
    {
        "grade": "G4",
        "base_salary": 5000,
        "post_allowance": 900,
        "performance_salary": 900,
        "applicable_to": "讲师",
        "description": "适用于独立承担课程的青年教师。",
    },
    {
        "grade": "G5",
        "base_salary": 5800,
        "post_allowance": 1200,
        "performance_salary": 1200,
        "applicable_to": "骨干讲师、教研室成员",
        "description": "适用于承担稳定教学任务与基础管理工作的教师。",
    },
    {
        "grade": "G6",
        "base_salary": 6800,
        "post_allowance": 1700,
        "performance_salary": 1800,
        "applicable_to": "副教授、专业负责人",
        "description": "适用于中高级职称和学院骨干岗位。",
    },
    {
        "grade": "G7",
        "base_salary": 7800,
        "post_allowance": 2200,
        "performance_salary": 2400,
        "applicable_to": "教授、院级管理岗位",
        "description": "适用于高级职称教师和重点管理岗位。",
    },
    {
        "grade": "G8",
        "base_salary": 9200,
        "post_allowance": 3200,
        "performance_salary": 3200,
        "applicable_to": "教授、系主任、学院核心负责人",
        "description": "适用于高层级教学科研带头人与核心管理岗位。",
    },
]

REWARD_RULES = [
    {
        "item": "国家级教学/科研项目立项",
        "impact": "月度绩效上浮 3000 元，连续发放 12 个月",
        "note": "适用于负责人或第一完成人。",
    },
    {
        "item": "省部级教学成果奖或科研奖励",
        "impact": "月度绩效上浮 1500 元，连续发放 6 个月",
        "note": "按获奖级别折算，核心完成人优先。",
    },
    {
        "item": "校级优秀教师、竞赛指导一等奖",
        "impact": "月度绩效上浮 800 元，连续发放 3 个月",
        "note": "与常规教学绩效可叠加。",
    },
]

PUNISHMENT_RULES = [
    {
        "item": "一般教学事故",
        "impact": "扣减当月绩效 20%",
        "note": "需提交整改说明并完成复盘。",
    },
    {
        "item": "严重教学事故",
        "impact": "扣减当月绩效 50%，取消当年评优资格",
        "note": "由学院和人事部门联合认定。",
    },
    {
        "item": "科研或师德违规",
        "impact": "停发绩效并转入正式问责流程",
        "note": "最终处理以学校正式制度和调查结论为准。",
    },
]

SALARY_RULE_MAP = {rule["grade"]: rule for rule in SALARY_RULES}
SALARY_GRADE_OPTIONS = [rule["grade"] for rule in SALARY_RULES]


def get_salary_rule(grade: str | None):
    if not grade:
        return None
    return SALARY_RULE_MAP.get(grade)


def estimate_monthly_salary(grade: str | None) -> int | None:
    rule = get_salary_rule(grade)
    if not rule:
        return None
    return rule["base_salary"] + rule["post_allowance"] + rule["performance_salary"]


def format_currency(amount: int | float | None) -> str:
    if amount is None:
        return ""
    return f"{amount:,.0f} 元"

