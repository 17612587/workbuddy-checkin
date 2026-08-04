#!/usr/bin/env python3
"""WorkBuddy/CodeBuddy CN 每日签到（含本次获得/累计获得/真实余额，直接输出中文结果）。"""

import json
import os
import stat
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

BASE_URL = "https://www.codebuddy.cn"
URL = f"{BASE_URL}/v2/billing/meter/daily-checkin"
STATUS_PATHS = ("/v2/billing/meter/checkin-activity-status", "/v2/billing/meter/checkin-status")
BALANCE_URL = f"{BASE_URL}/v2/billing/meter/get-user-resource"


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def default_auth_file(env=os.environ, home=None, platform=sys.platform):
    home = Path.home() if home is None else Path(home)
    if platform == "darwin":
        base = home / "Library/Application Support"
    elif platform == "win32":
        base = Path(env.get("LOCALAPPDATA") or home / "AppData/Local")
    else:
        base = Path(env.get("XDG_DATA_HOME") or home / ".local/share")
    return base / "CodeBuddyExtension/Data/Public/auth/workbuddy-desktop.info"


def read_login_file(path):
    if path.is_symlink():
        raise ValueError("WorkBuddy 登录文件不能是符号链接")
    try:
        info = path.stat()
    except FileNotFoundError:
        return {}
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("WorkBuddy 登录路径不是普通文件")
    if hasattr(os, "getuid") and info.st_uid != os.getuid():
        raise ValueError("WorkBuddy 登录文件属于其他用户")
    if os.name != "nt" and info.st_mode & 0o022:
        raise ValueError("WorkBuddy 登录文件可被其他用户写入")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError("WorkBuddy 登录文件不是有效的 JSON") from error
    if not isinstance(data, dict) or not isinstance(data.get("auth"), dict):
        raise ValueError("WorkBuddy 登录文件缺少 auth 字段")
    return data


def load_credentials(env=os.environ, home=None, platform=sys.platform):
    path = default_auth_file(env, home, platform)
    if Path(f"{path}.logged-out").exists():
        raise ValueError("WorkBuddy 已退出登录，请先在客户端登录")
    data = read_login_file(path)
    if not data:
        raise ValueError(f"未找到 WorkBuddy 登录文件：{path}")
    auth = data.get("auth") if isinstance(data.get("auth"), dict) else {}
    file_token = auth.get("accessToken") or auth.get("access_token") or ""
    token = file_token.strip() if isinstance(file_token, str) else ""

    if "+" in token:
        token_uid, token = (part.strip() for part in token.split("+", 1))
    else:
        token_uid = ""
    if not token:
        raise ValueError("WorkBuddy 登录文件缺少 access token")

    account = data.get("account") if isinstance(data.get("account"), dict) else {}
    return {
        "token": token,
        "uid": str(account.get("uid") or account.get("id") or token_uid).strip(),
        "enterprise_id": str(
            account.get("enterpriseId") or account.get("enterprise_id") or ""
        ).strip(),
        "domain": str(auth.get("domain") or data.get("domain") or "").strip(),
    }


def build_headers(credentials):
    token = credentials["token"]

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    optional = {
        "uid": ("X-User-Id",),
        "enterprise_id": ("X-Enterprise-Id", "X-Tenant-Id"),
        "domain": ("X-Domain",),
    }
    for field, names in optional.items():
        value = credentials[field]
        for name in names:
            if value:
                headers[name] = value
    return headers


def request_json(url, headers):
    request = Request(url, data=b"{}", headers=headers, method="POST")
    try:
        with build_opener(NoRedirects).open(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as error:
        try:
            body = json.loads(error.read().decode("utf-8"))
            message = body.get("message") if isinstance(body, dict) else None
        except (json.JSONDecodeError, UnicodeDecodeError):
            message = None
        raise ValueError(f"HTTP {error.code}：{message or error.reason}") from error
    try:
        body = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError("WorkBuddy 返回了无效 JSON") from error
    if not isinstance(body, dict):
        raise ValueError("WorkBuddy 返回了无效 JSON")
    return body


def checked_state(data):
    if "today_checked_in" in data:
        value = data["today_checked_in"]
    elif "todayCheckedIn" in data:
        value = data["todayCheckedIn"]
    else:
        return None
    if value is True or value == 1 or (
        isinstance(value, str) and value.strip().lower() in {"true", "1"}
    ):
        return True
    if value is False or value == 0 or (
        isinstance(value, str) and value.strip().lower() in {"false", "0"}
    ):
        return False
    return None


def already_checked_result(data):
    if checked_state(data) is not True:
        return None
    return {
        "status": "already_checked",
        "success": True,
        "message": "今天已经签到过了",
        "credit": data.get("today_credit", data.get("todayCredit", data.get("daily_credit", data.get("dailyCredit")))),
        "streak_days": data.get("streak_days", data.get("streakDays")),
        "balance": data.get("total_credits", data.get("totalCredits")),
        "reward": None,
    }


def get_checkin_status(headers):
    for path in STATUS_PATHS:
        try:
            body = request_json(f"{BASE_URL}{path}", headers)
            data = body.get("data")
            if body.get("code") == 0 and isinstance(data, dict) and checked_state(data) is not None:
                return data
        except (URLError, TimeoutError, ValueError):
            continue
    return None


def parse_response(body):
    if body.get("code") != 0:
        raise ValueError(body.get("message") or body.get("msg") or "签到失败")
    data = body.get("data")
    if not isinstance(data, dict):
        raise ValueError("WorkBuddy 响应缺少 data 字段")
    return {
        "success": data.get("success", True),
        "message": data.get("message") or body.get("message") or "签到成功",
        "credit": data.get("credit", data.get("today_credit")),
        "streak_days": data.get("streak_days"),
        "balance": data.get("total_credits", data.get("totalCredits")),
        "reward": data.get("reward"),
    }


def fetch_activity(headers):
    """查询活动状态接口，获取本次/累计积分。"""
    try:
        body = request_json(f"{BASE_URL}{STATUS_PATHS[0]}", headers)
        data = body.get("data") if body.get("code") == 0 else None
        if isinstance(data, dict):
            return {
                "today_credit": data.get("today_credit") or data.get("daily_credit"),
                "total_credits": data.get("total_credits"),
                "activity_name": data.get("activity_name", ""),
                "season": data.get("season"),
            }
    except Exception:
        pass
    return None


def fetch_balance(headers):
    """查询真实账户余额（get-user-resource 接口）。"""
    try:
        body = request_json(BALANCE_URL, headers)
        resp = (
            body.get("data", {}).get("Response", {}).get("Data")
            if body.get("code") == 0
            else None
        )
        if isinstance(resp, dict):
            return resp.get("TotalDosage")
    except Exception:
        pass
    return None


def main():
    try:
        headers = build_headers(load_credentials())

        # 1) 签到
        status = get_checkin_status(headers)
        result = already_checked_result(status) if status else None
        if result is None:
            result = parse_response(request_json(URL, headers))

        # 2) 活动信息（本次 / 累计积分）
        activity = fetch_activity(headers)

        # 3) 真实余额
        balance = fetch_balance(headers)

        # 4) 直接输出格式化中文结果，方便自动化推送
        is_ok = result.get("success")
        icon = "✅" if is_ok else "❌"
        status_text = (
            "签到完成"
            if result.get("status") != "already_checked"
            else "今天已签到过"
        )
        today_cr = (activity or {}).get("today_credit") or result.get("credit") or "-"
        total_cr = (activity or {}).get("total_credits") or "-"
        bal = balance or "-"
        streak = result.get("streak_days") or "-"
        act = (activity or {}).get("activity_name", "") or "-"

        print(f"{icon} {status_text}")
        print(f"• 本次签到获得：{today_cr} 积分")
        print(f"• 累计签到获得：{total_cr} 积分")
        print(f"• 当前余额：{bal} 积分")
        print(f"• 连续天数：{streak} 天")
        print(f"• 当前活动：{act}")

        # 同时输出 JSON 供程序化使用（用 --- 分隔）
        print("---")
        out = {
            "status": result.get("status"),
            "success": is_ok,
            "today_credit": today_cr,
            "total_credits": total_cr,
            "balance": bal,
            "streak_days": streak,
            "activity_name": act,
        }
        print(json.dumps(out, ensure_ascii=False))

    except SystemExit:
        raise
    except Exception as error:
        print(f"❌ 签到失败：{error}")


if __name__ == "__main__":
    main()
