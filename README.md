# workbuddy-checkin

WorkBuddy / CodeBuddy CN 每日签到 Skill，支持三字段输出：**本次签到获得 / 累计签到获得 / 当前余额**。

## 功能

- 自动读取本地 WorkBuddy/CodeBuddy 登录凭据完成每日签到
- 输出格式化中文结果（可直接用于推送通知）：
  ```
  ✅ 签到完成
  • 本次签到获得：100 积分
  • 累计签到获得：700 积分
  • 当前余额：2286 积分
  • 连续天数：7 天
  • 当前活动：本期：项目
  ---
  {"status":"ok","today_credit":100,"total_credits":700,"balance":2286,...}
  ```

## 使用方式

### 手动执行

```sh
python3 <skill-directory>/scripts/workbuddy-checkin.py
```

### 自动化定时签到

本脚本**不含通知/推送功能**，仅负责签到并输出结果。

使用本 Skill 时，WorkBuddy 会自动创建每日签到自动化（默认每天 09:00 执行）。

如需接收企业微信通知推送，只需：

1. 打开 WorkBuddy → 左侧「自动化」
2. 找到「WorkBuddy 每日签到」自动化，点击进入编辑
3. 开启**「推送到自动化企微通知 bot」**开关

> ⚠️ 企微通知需在自动化设置中手动开启该开关，脚本本身不包含任何推送逻辑。

## 隐私说明

- 脚本从本地 WorkBuddy 客户端的登录文件读取令牌（`%LOCALAPPDATA%/CodeBuddyExtension/Data/Public/auth/workbuddy-desktop.info`），**不会将令牌打印、写出或上传至任何外部服务**
- 所有 API 请求均通过 HTTPS 加密传输
- 仓库内不包含任何密钥、密码或个人凭据

## 文件结构

```
workbuddy-checkin/
├── SKILL.md                        # 技能说明（WorkBuddy Skill 入口）
├── scripts/
│   └── workbuddy-checkin.py        # 签到脚本（唯一核心文件）
├── .gitignore                      # 排除 __pycache__ 等非源码文件
└── README.md                       # 本文件
```

## 🚀 小白一键使用

不想敲命令？**直接复制下面这一整段话，粘到 WorkBuddy / CodeBuddy 对话框里发送**，它会自动下载、安装并创建好每日签到自动化，一步到位：

```
请从这个 GitHub 仓库下载并安装签到 Skill：https://github.com/17612587/workbuddy-checkin
安装完成后，帮我创建一个每天早上 9 点自动执行该 Skill 签到的自动化任务（WorkBuddy 每日签到）。
```

发完这条就完成了。之后想每天收到企业微信推送，只需：

1. 打开 WorkBuddy → 左侧「自动化」
2. 找到「WorkBuddy 每日签到」自动化，进入编辑
3. 开启**「推送到自动化企微通知 bot」**开关

> 脚本本身不含通知功能，企微推送开关需手动打开一次（见上方）。

## 依赖

- Python 3.x（标准库即可，无需安装第三方包）
- 已安装并登录的 WorkBuddy 或 CodeBuddy CN 客户端

## License

MIT
