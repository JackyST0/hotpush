# Changelog

本项目的所有重要变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本管理遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.5.0] - 2026-02-24

### Added
- 推送数据源选择功能，支持自定义 RSS 源
- 忘记密码提示联系管理员重置
- 推送配置保存前验证必填字段
- SMTP 服务器和端口默认值
- 首次打开默认使用白天模式
- 数据加载失败时显示失败源提示
- 在线演示站点
- JWT_SECRET 环境变量，防止重启后登录失效
- 基础测试框架（pytest）
- GitHub Actions CI/CD 流水线
- CHANGELOG 文件

### Fixed
- 修复邮件和 Webhook 推送渠道配置状态检测（之前始终显示未配置）
- 修复推送规则保存时字段格式不匹配
- 修复验证错误时 toast 显示 `[object Object]`
- 修复推送消息中重复的 emoji
- 修复弹窗遮罩层未覆盖全屏
- 修复 Sidebar 统计信息加载逻辑
- 修复前端路由 Nginx 配置
- 生产环境禁用 Swagger 文档

### Changed
- 邮件配置所有字段改为用户填写
- 后端只在启用推送时验证必填字段
- 统一自定义数据源和内置数据源的标题样式
- 错误提示显示具体原因，不再只显示通用文案

### Security
- 生产环境禁用 Swagger API 文档
- 添加安全提醒注释

## [0.1.0] - 2026-02-03

### Added
- 热点聚合：支持微博、知乎、B站、GitHub 等 15+ 平台热榜
- 多渠道推送：Telegram、Discord、企业微信、飞书、钉钉、邮件、Webhook
- 分钟级热点监控与实时推送
- 智能过滤：关键词过滤、时间段限制、来源过滤
- Vue 3 + Tailwind CSS 现代化管理界面
- 多用户与权限管理
- Docker 一键部署
- Redis 缓存
- MySQL 持久化
- 自定义 RSS 数据源
- APScheduler 定时任务调度
