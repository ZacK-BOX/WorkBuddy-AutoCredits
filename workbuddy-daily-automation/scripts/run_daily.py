#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WorkBuddy 每日自动化 · 执行包装器
═══════════════════════════════════════════════════════════════

职责（只做这四件事，不替换主脚本的任何业务逻辑）：

  1. 定位工作区与解释器，同步等待主脚本跑完（绝不后台化、绝不超时截断）。
  2. 原样保留 http_proxy / https_proxy，并显式传给子进程（不清空、不改代理）。
  3. 原样透传主脚本 stdout / stderr 与退出码，不吞错误。
  4. 从日志中稳定抽取「汇报三要素」——结尾 🏁 进度行、✅签到 行、⚠️ 人工介入行，
     便于上层按固定口径生成汇报，避免凭记忆编造数字。

用法：
  python run_daily.py                       # 默认工作区 + 默认解释器
  WBDAILY_WORKSPACE=<dir> python run_daily.py
  WBDAILY_PYTHON=<exe> python run_daily.py  # 指定解释器
  python run_daily.py --no-summary          # 只打印原始输出，不打印摘要
"""

import glob
import os
import re
import subprocess
import sys

DEFAULT_WORKSPACE = r"D:/WorkbuddyDoc/2026-09-22-15-41-36"
DEFAULT_SCRIPT = "workbuddy_daily.py"
# 主脚本依赖 requests；托管 Python 常缺该包，故按「探测可用」而非「写死顺序」选解释器。
REQUIRED_MODULE = "requests"
_ANACONDA = r"C:/ProgramData/Anaconda3/python.exe"
_MANAGED_GLOB = r"C:/Users/Administrator/.workbuddy/binaries/python/versions/*/python.exe"

ERROR_KEYWORDS = (
    "登录态已失效",
    "未找到登录凭据",
    "网络不可达",
    "Traceback",
    "NoAccessToken",
    "ConnectionError",
)


def _candidate_pythons():
    """候选解释器，按优先级排列。"""
    cands = [_ANACONDA]
    try:
        cands.extend(sorted(glob.glob(_MANAGED_GLOB), reverse=True))
    except Exception:  # noqa: BLE001
        pass
    cands.append(sys.executable)
    # 去重并保持顺序
    seen, out = set(), []
    for c in cands:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _can_import(exe, module=REQUIRED_MODULE, timeout=25):
    try:
        r = subprocess.run([exe, "-c", "import %s" % module],
                           capture_output=True, timeout=timeout)
        return r.returncode == 0
    except Exception:  # noqa: BLE001
        return False


def resolve_python(verbose=True):
    """选一个真的能 import requests 的解释器；选不出就明确报错，不静默降级。"""
    env_py = os.environ.get("WBDAILY_PYTHON", "").strip()
    if env_py:
        if os.path.exists(env_py):
            ok = _can_import(env_py)
            if verbose:
                print("[run_daily] ▶ 解释器(显式指定): %s %s"
                      % (env_py, "可用" if ok else "但缺少 %s，可能失败" % REQUIRED_MODULE))
            return env_py
        print("[run_daily] ⚠️ WBDAILY_PYTHON 指向不存在的可执行文件：%s" % env_py,
              file=sys.stderr)

    usable = []
    for cand in _candidate_pythons():
        if not os.path.exists(cand):
            continue
        if _can_import(cand):
            usable.append(cand)

    if usable:
        if verbose and len(usable) > 1:
            print("[run_daily] ▶ 解释器探测: %d 个可用，选首选 %s"
                  % (len(usable), usable[0]))
        return usable[0]

    raise SystemExit(
        "[run_daily] ❌ 找不到任何可 import %s 的 Python 候选，已中止。"
        "请设置 WBDAILY_PYTHON=<解释器绝对路径> 后重试。候选：%s"
        % (REQUIRED_MODULE, ", ".join(_candidate_pythons()) or "(无)")
    )


def summarise(log):
    """抽取汇报三要素。全部用正则，找不到就返回 None，绝不臆造。"""
    summary = {"finish_line": None, "checkin_line": None,
               "manual_lines": [], "error_hits": [], "exit_code": None}

    m = re.search(r"🏁.*$", log, flags=re.M)
    if m:
        summary["finish_line"] = m.group(0).strip()

    m = re.search(r"✅签到[^\n]*", log)
    if m:
        summary["checkin_line"] = m.group(0).strip()

    summary["manual_lines"] = [
        ln.strip() for ln in log.splitlines() if "⚠️" in ln and ln.strip()
    ]

    summary["error_hits"] = [
        kw for kw in ERROR_KEYWORDS if kw in log
    ]
    return summary


def main():
    argv = [a for a in sys.argv[1:]]
    want_summary = "--no-summary" not in argv
    if "--no-summary" in argv:
        argv.remove("--no-summary")

    workspace = os.environ.get("WBDAILY_WORKSPACE", "").strip() or DEFAULT_WORKSPACE
    script_name = os.environ.get("WBDAILY_SCRIPT", "").strip() or DEFAULT_SCRIPT
    python_exe = resolve_python()

    script_path = os.path.join(workspace, script_name)
    if not os.path.exists(script_path):
        print("[run_daily] ❌ 主脚本不存在：%s" % script_path, file=sys.stderr)
        return 2
    if not os.path.exists(workspace):
        print("[run_daily] ❌ 工作区不存在：%s" % workspace, file=sys.stderr)
        return 2

    child_env = os.environ.copy()  # 关键：继承即保留 http_proxy/https_proxy/NO_PROXY
    proxy_note = "http_proxy=%s https_proxy=%s no_proxy=%s" % (
        child_env.get("http_proxy") or child_env.get("HTTP_PROXY") or "(空)",
        child_env.get("https_proxy") or child_env.get("HTTPS_PROXY") or "(空)",
        child_env.get("no_proxy") or child_env.get("NO_PROXY") or "(空)",
    )

    print("[run_daily] ▶ 工作区: %s" % workspace)
    print("[run_daily] ▶ 解释器: %s" % python_exe)
    print("[run_daily] ▶ 代理(原样保留): %s" % proxy_note)
    print("[run_daily] ▶ 同步等待主脚本执行完成…")
    print("──────────── 主脚本输出开始 ────────────")

    try:
        proc = subprocess.run(
            [python_exe, script_name] + argv,
            cwd=workspace,
            env=child_env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except Exception as exc:  # noqa: BLE001 - 包装器自身必须兜住异常并保留退出码语义
        print("[run_daily] ❌ 无法启动主脚本: %r" % (exc,), file=sys.stderr)
        return 3

    print(proc.stdout if proc.stdout else "")
    if proc.stderr:
        print("[run_daily] stderr: %s" % proc.stderr.rstrip(), file=sys.stderr)

    print("──────────── 主脚本输出结束 ────────────")

    exit_code = proc.returncode

    if want_summary:
        log = (proc.stdout or "") + "\n" + (proc.stderr or "")
        s = summarise(log)
        s["exit_code"] = exit_code
        print("\n════════ 汇总（供汇报使用）════════")
        print("退出码: %s" % exit_code)
        print("进度行: %s" % (s["finish_line"] or "（未找到 🏁 行）"))
        print("签到行: %s" % (s["checkin_line"] or "（未找到 ✅签到 行）"))
        if s["manual_lines"]:
            print("人工介入提示 (%d 条):" % len(s["manual_lines"]))
            for ln in s["manual_lines"]:
                print("  - %s" % ln)
        else:
            print("人工介入提示: 无")
        if s["error_hits"]:
            print("⚠️ 命中风险关键词: %s" % ", ".join(s["error_hits"]))
        else:
            print("⚠️ 命中风险关键词: 无")
        print("════════════════════════════════")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
