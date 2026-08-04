---
name: workbuddy-checkin
description: 使用当前 WorkBuddy 或 CodeBuddy CN 账号签到（含本次获得/累计获得/真实余额三字段）。用户要求签到、打卡、check in 时使用。
---

# WorkBuddy 签到

用户明确要求签到后，直接运行，不要先读脚本：

```sh
python3 <skill-directory>/scripts/workbuddy-checkin.py
```

脚本会直接输出格式化的中文签到结果（含本次获得 / 累计获得 / 真实余额）。只回复一次：将脚本输出的中文结果原样返回给用户。不要泄露凭据或重试。不要添加任何额外解释。

## 自动签到

每日自动签到由 WorkBuddy 自动化负责（已配套创建「WorkBuddy 每日签到」自动化，每天 9:00 执行并推送结果）。修改时间或开关请直接在 WorkBuddy 自动化设置里操作，本技能脚本不参与定时调度。
