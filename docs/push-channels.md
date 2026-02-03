# 推送渠道配置指南

> 💡 **提示**：推送渠道可以在管理界面的「推送配置」页面中配置，无需手动编辑环境变量。

## Telegram（推荐）

Telegram 是最容易配置的推送渠道，无需审核，API 友好。

### 步骤

1. **创建 Bot**
   - 在 Telegram 中找到 [@BotFather](https://t.me/BotFather)
   - 发送 `/newbot`
   - 按提示设置 Bot 名称
   - 获取 Bot Token（格式：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）

2. **获取 Chat ID**
   - 找到 [@userinfobot](https://t.me/userinfobot)
   - 发送任意消息
   - 它会返回你的 Chat ID（纯数字）

3. **配置环境变量**
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   ```

4. **与 Bot 对话**
   - 找到你创建的 Bot，发送 `/start`
   - 这样 Bot 才有权限给你发消息

---

## Discord

### 步骤

1. 打开 Discord 服务器设置
2. 点击「整合」→「Webhook」→「新 Webhook」
3. 复制 Webhook URL
4. 配置环境变量：
   ```
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxx/yyy
   ```

---

## 企业微信

### 步骤

1. 打开企业微信群
2. 点击群设置 → 群机器人 → 添加机器人
3. 复制 Webhook URL
4. 配置环境变量：
   ```
   WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
   ```

---

## 飞书

### 步骤

1. 打开飞书群
2. 点击群设置 → 群机器人 → 添加机器人 → 自定义机器人
3. 复制 Webhook URL
4. 配置环境变量：
   ```
   FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
   ```

---

## 钉钉

### 步骤

1. 打开钉钉群
2. 点击群设置 → 智能群助手 → 添加机器人
3. 选择「自定义」机器人
4. 安全设置选择「关键词」，添加关键词「热榜」或「HotPush」
5. 复制 Webhook URL
6. 配置环境变量：
   ```
   DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=xxx
   ```

---

## 邮件

通过 SMTP 发送邮件通知。

### 步骤

1. 获取邮箱的 SMTP 服务配置
   - Gmail：需要开启"应用专用密码"
   - QQ 邮箱：需要开启 SMTP 服务并获取授权码
   - 企业邮箱：联系管理员获取 SMTP 配置

2. 配置环境变量：
   ```
   EMAIL_SMTP_HOST=smtp.gmail.com
   EMAIL_SMTP_PORT=587
   EMAIL_USERNAME=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   EMAIL_FROM=your_email@gmail.com
   ```

### 常用 SMTP 服务器

| 邮箱 | SMTP 服务器 | 端口 |
|------|------------|------|
| Gmail | smtp.gmail.com | 587 |
| QQ 邮箱 | smtp.qq.com | 587 |
| 163 邮箱 | smtp.163.com | 25 |
| Outlook | smtp.office365.com | 587 |

---

## Webhook（通用）

如果你想接入自己的系统，可以使用通用 Webhook。

### 请求格式

HotPush 会向你的 Webhook URL 发送 POST 请求：

```json
{
  "title": "微博热搜 热榜更新",
  "content": "发现 5 条新热点",
  "source": "weibo",
  "items": [
    {
      "id": "abc123",
      "title": "热点标题",
      "url": "https://...",
      "hot_score": "123456",
      "source": "weibo"
    }
  ]
}
```

你的服务器应返回 2xx 状态码表示接收成功。
