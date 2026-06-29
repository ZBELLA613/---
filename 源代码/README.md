# 高校人事信息管理系统

## 项目简介

本项目是一个基于 Python 开发的高校人事信息管理系统，现已提供两种使用方式：

- `Web 版`：基于 Flask，适合浏览器演示
- `Qt 桌面版`：基于 PySide6，适合本地直接打开运行

本系统面向高校人事部门、教务管理人员和教师用户，围绕教职工基础信息、课程与授课、科研成果、统计分析和数据导出展开。

## 当前推荐使用方式

如果你希望“像本地软件一样双击打开使用”，推荐使用：

- [desktop_qt.py](D:/数据库课程设计/高校人事信息管理系统/desktop_qt.py)
- 或直接双击 [run_desktop.bat](D:/数据库课程设计/高校人事信息管理系统/run_desktop.bat)

Qt 桌面版无需浏览器，更接近本地管理软件的使用方式。

## 主要功能

### 1. 教职工基础信息管理
- 管理教职工编号、姓名、性别、出生日期、学历、学位、专业、入职时间、所属部门、职称、职务、薪资等级、联系方式、奖惩记录、在职状态等信息。
- 支持多位教师、多部门展示。
- 当前已内置较丰富样例数据，便于课程设计演示。

### 2. 教学信息管理
- 管理课程信息：课程编号、课程名称、课程性质、学分、学时、适用专业。
- 管理授课任务：教师、课程、班级、学生人数、学期。

### 3. 科研信息管理
- 管理课题信息、专利信息、论文与著作信息。
- 展示研究方向、项目编号、专利类型、期刊/出版社、ISBN/ISSN 等内容。

### 4. 查询统计
- 首页可查看教职工总数、部门数、课程数、授课任务数、科研成果数。
- 支持职称分布、人员状态统计。


## 技术栈

### Web 版
- Flask
- SQLAlchemy
- openpyxl
- Alembic

### 桌面版
- PySide6（Qt for Python）

### 数据库
- SQLite
- MySQL

## 项目结构

```text
高校人事信息管理系统/
├─ app.py                    # Flask Web 主程序
├─ desktop_qt.py             # Qt 桌面版主程序
├─ run_desktop.bat           # Windows 下桌面版启动脚本
├─ config.py                 # 配置文件
├─ models.py                 # 数据模型
├─ seed_data.py              # 初始化样例数据
├─ extensions.py             # 数据库连接扩展
├─ utils.py                  # 工具函数
├─ requirements.txt          # 依赖列表
├─ templates/                # Web 模板
├─ static/                   # Web 静态资源
├─ migrations/               # Alembic 迁移目录
└─ instance/                 # SQLite 数据库文件目录
```

## 环境要求

- Python 3.9 及以上
- Windows 环境下可直接运行 `run_desktop.bat`

## 安装依赖

在项目目录下执行：

```bash
pip install -r requirements.txt
```

## 使用方法

## 方式一：运行 Qt 桌面版

### 方法 1：双击启动
直接双击：

```text
run_desktop.bat
```

### 方法 2：命令行启动

```bash
python desktop_qt.py
```

启动后会打开一个本地桌面软件窗口，包含以下模块：

- 系统概览
- 教职工档案
- 课程与授课
- 科研成果
- 数据字典

## 方式二：运行 Flask Web 版

```bash
python app.py
```

浏览器访问：

```text
http://127.0.0.1:5000
```

## 默认账号

### 管理员
- 用户名：`admin`
- 密码：`admin123`

### 教师账号
- `T2024001 / T2024001@123`
- `T2024002 / T2024002@123`
- `T2024003 / T2024003@123`
- 其余教师账号默认也按同样规则生成：
  `教职工编号 + @123`

例如：

```text
T2024008 / T2024008@123
```

完整账号清单见：

- [登录账号说明.md](D:/数据库课程设计/高校人事信息管理系统/登录账号说明.md)

## Qt 桌面版内容说明

### 1. 系统概览
- 展示教职工总数、部门数量、课程数量、授课任务数量、科研成果数量
- 展示职称统计和人员状态统计

### 2. 教职工档案
- 查看所有教职工详细信息
- 支持关键字筛选

### 3. 课程与授课
- 查看课程基础信息
- 查看授课任务信息

### 4. 科研成果
- 分页签查看课题、专利、论文与著作

### 5. 数据字典
- 查看系统关系设计说明
- 查看主要表及字段含义

## Web 版导出 Excel

当前 Excel 导出主要在 Web 版中提供，导出方式如下：

### 管理员导出
- 登录后点击首页右上角：
  - `导出教职工`
  - `导出教学任务`
  - `导出科研成果`

### 教师导出
- 教师账号只能导出本人可见的数据

导出文件格式：

```text
.xlsx
```

## 数据库说明

默认使用 SQLite，适合本地直接运行。

如果需要切换到 MySQL，可在 `config.py` 中配置以下环境变量：

```bash
set DB_DRIVER=mysql
set DB_HOST=127.0.0.1
set DB_PORT=3306
set DB_NAME=hr_personnel
set DB_USER=root
set DB_PASSWORD=password
```

MySQL 连接示例：

```python
mysql+pymysql://root:password@127.0.0.1:3306/hr_personnel?charset=utf8mb4
```

## E-R 设计说明

本系统主要实体包括：

- `Department`：部门
- `Employee`：教职工
- `User`：系统用户
- `Course`：课程
- `TeachingAssignment`：授课任务
- `ResearchProject`：科研课题
- `Patent`：专利
- `Publication`：论文与著作

### 关系说明

- 一个部门对应多个教职工
- 一个教职工可绑定一个登录账号
- 一个教职工可承担多个授课任务
- 一个课程可被多个教师授课
- 一个教职工可拥有多个课题、专利、论文和著作

## 主要表结构与字段说明

### 1. departments
- `id`：主键
- `name`：部门名称
- `description`：部门说明

### 2. employees
- `employee_no`：教职工编号
- `name`：姓名
- `gender`：性别
- `birth_date`：出生日期
- `education`：学历
- `degree`：学位
- `major`：专业
- `hire_date`：入职时间
- `department_id`：所属部门
- `title`：职称
- `position`：职务
- `salary_grade`：薪资等级
- `phone`：联系电话
- `email`：邮箱
- `reward_punishment`：奖惩记录
- `status`：人员状态
- `notes`：备注

### 3. users
- `username`：登录用户名
- `password_hash`：加密密码
- `role`：角色
- `employee_id`：关联教职工

### 4. courses
- `course_no`：课程编号
- `name`：课程名称
- `nature`：课程性质
- `credits`：学分
- `hours`：学时
- `applicable_major`：适用专业
- `description`：课程说明

### 5. teaching_assignments
- `employee_id`：授课教师
- `course_id`：课程编号
- `class_name`：授课班级
- `student_count`：学生人数
- `semester`：学期

### 6. research_projects
- `research_direction`：研究方向
- `project_no`：课题编号
- `project_name`：课题名称
- `sponsor`：立项单位
- `start_date`：立项时间
- `end_date`：结题时间
- `status`：课题状态

### 7. patents
- `patent_no`：专利编号
- `patent_name`：专利名称
- `grant_date`：授权时间
- `patent_type`：专利类型
- `inventors`：发明人

### 8. publications
- `work_name`：作品名称
- `publisher`：期刊或出版社
- `publish_date`：发表时间
- `author_order`：作者排序
- `isbn_issn`：ISBN/ISSN
- `work_type`：论文或著作




