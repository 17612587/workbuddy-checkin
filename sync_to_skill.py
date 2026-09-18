#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把本目录（开发副本）同步到 WorkBuddy 技能目录。

开发流程
--------
1. 在本目录（工作区里的 daily-credits-checkin\\）直接改代码；
2. 本地测试，例如：
       python scripts\\daily-credits-checkin.py
3. 测试没问题后，运行本脚本把改动同步到技能目录：
       python sync_to_skill.py
4. 技能目录才是 WorkBuddy 真正加载的那份，同步后立即生效。

目录关系
--------
  工作区副本（本目录）＝ 真源，改这里，git 仓库也在这里
  ~/.workbuddy/skills/<技能名>/ ＝ 部署副本，由本脚本写入，不要手改

脚本会自动从 SKILL.md 的 front-matter 读取技能名，因此路径可移植。
"""

import hashlib
import os
import shutil
import subprocess
import sys

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_ROOT = os.path.join(os.path.expanduser("~"), ".workbuddy", "skills")

# 需要同步的文件 / 目录（相对 SRC_DIR）
FILES = ["SKILL.md", "README.md", ".gitignore"]
DIRS = ["scripts"]
EXCLUDE = {"__pycache__", ".git", ".DS_Store"}


def read_skill_name():
    """从 SKILL.md 的 front-matter 读取 name 字段。"""
    path = os.path.join(SRC_DIR, "SKILL.md")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    head = text.split("---", 2)
    if len(head) < 3:
        raise SystemExit("SKILL.md 缺少 front-matter")
    for line in head[1].splitlines():
        if line.strip().startswith("name:"):
            return line.split(":", 1)[1].strip()
    raise SystemExit("SKILL.md 的 front-matter 里找不到 name 字段")


def md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def collect(src_root):
    """返回 {相对路径: 绝对路径}。"""
    out = {}
    for name in FILES:
        p = os.path.join(src_root, name)
        if os.path.isfile(p):
            out[name] = p
    for name in DIRS:
        base = os.path.join(src_root, name)
        for dp, dn, fn in os.walk(base):
            dn[:] = [d for d in dn if d not in EXCLUDE]
            for f in fn:
                if f in EXCLUDE or f.endswith(".pyc"):
                    continue
                p = os.path.join(dp, f)
                out[os.path.relpath(p, src_root)] = p
    return out


def main():
    name = read_skill_name()
    dst_dir = os.path.join(SKILLS_ROOT, name)

    print(f"技能名   : {name}")
    print(f"同步源   : {SRC_DIR}")
    print(f"同步目标 : {dst_dir}")
    print("-" * 60)

    if not os.path.isdir(dst_dir):
        print(f"⚠ 技能目录不存在，将创建：{dst_dir}")
        os.makedirs(dst_dir, exist_ok=True)

    changed, same = [], []
    src_map = collect(SRC_DIR)
    for rel, src in sorted(src_map.items()):
        dst = os.path.join(dst_dir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.isfile(dst) and md5(src) == md5(dst):
            same.append(rel)
            continue
        shutil.copy2(src, dst)
        changed.append(rel)

    for rel in changed:
        print(f"  ✔ 更新 {rel}")
    for rel in same:
        print(f"    = 未变 {rel}")

    # 清理部署副本里已不存在的陈旧文件（例如源码里的文件被改名/删除）
    removed = []
    for rel in collect(dst_dir):
        if rel in src_map:
            continue
        os.remove(os.path.join(dst_dir, rel))
        removed.append(rel)
    for rel in removed:
        print(f"  ✘ 删除陈旧文件 {rel}")

    # 语法校验
    for rel in collect(SRC_DIR):
        if rel.endswith(".py"):
            target = os.path.join(dst_dir, rel)
            r = subprocess.run([sys.executable, "-m", "py_compile", target],
                               capture_output=True, text=True)
            if r.returncode != 0:
                print(f"\n✗ 语法错误：{rel}\n{r.stderr}")
                return 1

    print("-" * 60)
    if changed or removed:
        print(f"同步完成：{len(changed)} 个文件已更新，"
              f"{len(removed)} 个陈旧文件已删除，{len(same)} 个未变。")
    else:
        print(f"无需同步：{len(same)} 个文件与技能目录一致。")
    print("提示：技能目录是部署副本，请不要直接手改。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
