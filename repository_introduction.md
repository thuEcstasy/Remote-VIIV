# Remote-VIIV 项目介绍

## 🎯 项目概述

Remote-VIIV 是一个基于 Web 的实时多人在线游戏平台，主要用于支持"六人四副滚子"卡牌游戏。该项目采用前后端分离架构，提供用户认证、实时通信、游戏房间管理等功能。

## 🛠️ 技术栈

### 后端技术
- **框架**: Django 4.2.7
- **实时通信**: Django Channels 4.0.0 + WebSocket
- **数据库**: SQLite (开发环境)，支持 MySQL 
- **API**: Django REST Framework
- **其他依赖**:
  - `django-cors-headers`: 跨域资源共享
  - `daphne`: ASGI 服务器
  - `twilio`: 短信服务
  - `email-validator`: 邮箱验证
  - `pymysql`: MySQL 数据库连接

### 前端技术
- **框架**: Next.js 13.4.12
- **UI 库**: React 18.2.0 + TypeScript 5.1.6
- **组件库**: Ant Design 5.16.0
- **状态管理**: Redux Toolkit + React Redux
- **实时通信**: Socket.IO Client 4.7.5
- **数据持久化**: Redux Persist
- **测试**: Jest + Testing Library

## ✨ 主要功能特性

### 🔐 用户认证系统
- 用户注册与登录
- 邮箱验证绑定
- JWT Token 认证
- WebSocket 连接身份验证

### 🎮 游戏功能
- **六人四副滚子游戏**: 支持多人在线卡牌游戏
- **房间管理**: 创建、加入、退出游戏房间
- **实时游戏状态同步**: 基于 WebSocket 的实时通信

### 💬 实时通信
- WebSocket 长连接
- 实时消息推送
- 群组聊天功能
- 用户状态同步

## 📁 项目结构

```
Remote-VIIV/
├── frontend/                 # 前端项目
│   ├── src/
│   │   ├── pages/           # 页面组件
│   │   │   ├── index.tsx    # 登录页面
│   │   │   ├── room.tsx     # 游戏房间页面
│   │   │   └── _app.tsx     # 应用入口
│   │   ├── redux/           # 状态管理
│   │   ├── utils/           # 工具函数
│   │   └── constants/       # 常量定义
│   ├── public/              # 静态资源
│   └── package.json         # 前端依赖配置
├── backend/                  # 后端项目
│   ├── VIIV/                # Django 主配置
│   │   ├── settings.py      # 项目设置
│   │   ├── urls.py          # 路由配置
│   │   └── asgi.py          # ASGI 配置
│   ├── main/                # 主应用
│   │   ├── models.py        # 数据模型
│   │   ├── views.py         # 视图函数
│   │   ├── consumers.py     # WebSocket 消费者
│   │   └── urls.py          # 应用路由
│   ├── middleware/          # 中间件
│   └── requirements.txt     # 后端依赖
└── rules/                   # 游戏规则文档
    ├── 六人四副滚子规则拟定 1.3.1.pdf
    └── 六人四副滚子规则拟定 1.3.1.docx
```

## 🚀 快速开始

### 环境要求
- Python 3.11+
- Node.js 20.17.0+
- Conda (推荐)

### 后端启动
1. 创建并激活虚拟环境：
```bash
conda create -n django_hw python=3.11 -y
conda activate django_hw
```

2. 安装依赖：
```bash
cd backend
pip install -r requirements.txt
```

3. 启动开发服务器：
```bash
python manage.py runserver
```
访问 http://127.0.0.1:8000/main/1 验证后端服务

### 前端启动
1. 安装 Node.js 和 Yarn：
```bash
npm install -g yarn
```

2. 安装依赖：
```bash
cd frontend
yarn install
```

3. 启动开发服务器：
```bash
yarn dev
```
访问 http://127.0.0.1:3000 查看前端页面

## 🎲 游戏规则

项目支持"六人四副滚子"卡牌游戏，详细游戏规则请参考 `rules/` 目录下的规则文档。

## 🔧 开发特性

- **容器化支持**: 提供 Dockerfile 和 .dockerignore 配置
- **CI/CD**: 集成 GitLab CI/CD 配置
- **代码质量**: ESLint + SonarQube 代码检查
- **测试覆盖**: Jest 单元测试 + Coverage 覆盖率报告
- **类型安全**: TypeScript 静态类型检查

## 📊 当前开发进度

- ✅ 登录页面 (VIIV backend + index.tsx frontend)
- ✅ 主页面/房间页面 (main backend + room.tsx frontend)  
- ✅ WebSocket 实时通信
- ✅ 用户认证系统
- ✅ 邮箱验证功能

## 🤝 协作指南

项目采用前后端分离架构，开发者可以并行开发前后端功能。请确保：
1. 遵循现有的代码规范和目录结构
2. 及时更新依赖版本
3. 编写对应的测试用例
4. 更新相关文档

---

*这是一个功能完整的实时多人在线游戏平台，适合学习 Web 全栈开发、实时通信、游戏开发等技术。*