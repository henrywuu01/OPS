# IOPS - 智能运营系统

智能运营系统（Intelligent Operations System）是一个企业级运营管理平台，涵盖用户权限、任务调度、数据报表、配置管理、流程审批、审计监控、消息通知等核心功能。

## 功能模块

| 模块 | 说明 | 状态 |
|------|------|------|
| 登录鉴权中心 | 用户认证、RBAC权限、SSO集成 | 开发中 |
| 智能调度中心 | 定时任务、DAG工作流、监控告警 | 开发中 |
| 低代码报表引擎 | 多数据源、可视化配置、自动推送 | 规划中 |
| 通用配置中心 | 动态CRUD、版本控制、审批发布 | 规划中 |
| 流程审批中心 | 可视化流程设计、多级审批 | 规划中 |
| 全局审计监控 | 操作日志、数据变更、系统监控 | 规划中 |
| 消息通知中心 | 多渠道推送、模板管理 | 规划中 |

## 技术栈

### 后端
- Python 3.10+
- Django 4.2 LTS
- Django REST Framework
- Celery + Redis
- MySQL 8.0

### 前端
- Vue 3
- Vite
- Ant Design Vue 4
- Pinia
- ECharts

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 18+
- MySQL 8.0
- Redis 7.0

### 本地开发

1. 克隆项目
```bash
git clone https://github.com/your-repo/OPS.git
cd OPS
```

2. 配置数据库
```bash
cp config/sys.ini.example config/sys.ini
# 编辑 config/sys.ini 配置数据库连接
```

3. 启动后端
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

4. 启动前端
```bash
cd frontend
npm install
npm run dev
```

### Docker 部署

```bash
docker-compose up -d
```

访问：
- 前端: http://localhost:5173
- 后端 API: http://localhost:8000/api/docs/swagger/

## 项目结构

```
OPS/
├── backend/                # Django 后端
│   ├── apps/              # 应用模块
│   │   ├── auth/          # 认证授权
│   │   ├── scheduler/     # 任务调度
│   │   ├── report/        # 报表引擎
│   │   ├── config/        # 配置中心
│   │   ├── workflow/      # 审批流程
│   │   ├── audit/         # 审计日志
│   │   └── notification/  # 消息通知
│   └── ops/               # 项目配置
├── frontend/              # Vue 前端
│   ├── src/
│   │   ├── views/         # 页面组件
│   │   ├── components/    # 公共组件
│   │   ├── stores/        # 状态管理
│   │   ├── api/           # API 接口
│   │   └── router/        # 路由配置
│   └── public/
├── config/                # 配置文件
├── doc/                   # 项目文档
└── scripts/               # 脚本工具
```

## 文档

- [系统设计文档](doc/系统设计文档.md)
- [开发计划文档](doc/开发计划文档.md)
- [API 文档](http://localhost:8000/api/docs/swagger/)

## 开发规范

- 后端代码遵循 PEP 8 规范，使用 Black 格式化
- 前端代码遵循 ESLint + Prettier 规范
- Git 提交信息遵循 Conventional Commits

## License

MIT License
