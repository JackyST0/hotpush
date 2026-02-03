# 快速开始

## 环境要求

- Python 3.11+
- Node.js 18+
- MySQL 8.0+
- Redis 6.0+
- Docker（可选）

## 本地开发

### 1. 克隆项目

```bash
git clone https://github.com/JackyST0/hotpush.git
cd hotpush
```

### 2. 配置数据库

```bash
# 登录 MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE hotpush CHARACTER SET utf8mb4;
```

### 3. 启动 Redis

```bash
# macOS
brew services start redis

# Linux
sudo systemctl start redis

# 或使用 Docker
docker run -d -p 6379:6379 redis:alpine
```

### 4. 配置后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
```

编辑 `.env` 文件，配置以下内容：

```env
# 管理员账号
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password

# MySQL 数据库
DATABASE_URL=mysql://root:password@localhost:3306/hotpush

# Redis
REDIS_URL=redis://localhost:6379/0

# 推送渠道（至少配置一个）
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 5. 启动后端

```bash
uvicorn app.main:app --reload --port 8000
```

### 6. 配置前端

```bash
cd ../frontend

# 安装依赖
npm install
```

### 7. 启动前端

```bash
npm run dev
```

### 8. 访问服务

- 前端界面：http://localhost:3000
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

## Docker 部署

### 1. 配置环境变量

```bash
cp backend/.env.example backend/.env
# 编辑 .env 文件
```

### 2. 启动

```bash
docker-compose up -d
```

### 3. 查看日志

```bash
docker-compose logs -f hotpush
```

## 首次登录

1. 访问 http://localhost:3000
2. 使用 `.env` 中配置的管理员账号登录
3. 进入"推送配置"页面配置推送渠道
4. 进入"热搜榜"查看聚合的热点内容

## 常见问题

### Q: 推送失败怎么办？

A: 检查以下几点：
1. 环境变量是否正确配置
2. Bot Token 是否有效
3. Chat ID 是否正确
4. 网络是否能访问 Telegram API

### Q: Redis 连接失败？

A: 检查 Redis 服务是否启动：
```bash
redis-cli ping
# 应该返回 PONG
```

### Q: MySQL 连接失败？

A: 检查：
1. MySQL 服务是否启动
2. 数据库是否创建
3. 用户名密码是否正确
4. DATABASE_URL 格式是否正确

### Q: 如何自建 RSSHub？

A: 在 `docker-compose.yml` 中取消 rsshub 服务的注释，然后修改 `RSSHUB_URL` 为 `http://rsshub:1200`。

### Q: 如何添加自定义数据源？

A: 登录管理界面，进入"数据源"页面，点击"添加自定义源"，输入 RSS 地址即可。
