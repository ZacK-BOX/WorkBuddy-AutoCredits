---
name: workbuddy-daily-automation
display_name: WorkBuddy 每日自动化执行
display_name_en: WorkBuddy Daily Automation Runner
description: "无人值守执行 WorkBuddy 每日自动化（签到/补签 + 成长中心全套任务 + 自动领奖），并输出固定口径的汇报。用于定时任务/自动化（automation）触发、每4小时签到、跑 workbuddy_daily.py、总结签到结果、成长中心完成进度。强约束：保持本机 http_proxy/https_proxy 环境变量原样，绝不清空；同步等待命令结束；只读 wb_refresh_tokens.json，不打印不上传 token；汇报只引用脚本日志原文，不臆造数字。含反幻觉排障规则：accessToken 已加密（$wbEncrypted）导致的登录态误报不是故障，切勿让用户重新登录。触发词：跑签到、定时任务、自动化任务、每4小时签到、WorkBuddy 签到、成长中心、自动领奖、查一下签到结果、workbuddy_daily。"
description_zh: "面向定时/无人值守场景的 WorkBuddy 每日自动化执行器。包装器负责保代理、同步等待、退出码透传与日志结构化抽取；本文定义执行口径、汇报三要素（结尾进度行 / ✅签到 行 / ⚠️ 人工介入提示）与排障边界（加密凭据误报不算故障）。与同目录下的 totorosir-workbuddy-score 分工：该技能是「用户交互式查询/播报」，本技能是「定时任务执行与汇报」。"
description_en: "Unattended runner for the WorkBuddy daily automation (check-in + all growth-center tasks + auto claim) with a fixed reporting protocol. Enforces: keep local http_proxy/https_proxy untouched, wait synchronously, never echo tokens, quote only log lines. Includes anti-hallucination triage: an 'invalid login state' warning caused by the AES-encrypted accessToken is NOT a failure — never ask the user to re-login. Distinct from totorosir-workbuddy-score, which is the interactive query/report skill."
category: automation
version: 1.0.1
author: workbuddy-ops
agent_created: true
visibility: private
license: MIT-0
metadata:
  openclaw:
    emoji: "⏱️"
    requires:
      bins:
        - python3
      env: []
allowed-tools: Bash,Read,Edit,Write
---

# WorkBuddy 每日自动化执行（定时任务专用）

本技能服务于**无人值守的定时任务**：跑一次 WorkBuddy 签到 + 成长中心全套 + 自动领奖，然后产出一句可核对的汇报。

它不替代 `totorosir-workbuddy-score`（那个是**用户交互式**查积分、看播报、派猫猫旅行的技能）。本技能只解决「定时任务怎么跑、跑完怎么汇报、报错怎么分诊」。

---

## 一、何时使用

命中任一即触发本技能：

- 自动化任务（automation）被定时触发，任务描述含「每4小时」「签到/补签」「成长中心」「自动领奖」。
- 用户说：跑一下签到、定时任务、跑自动化、每4小时那个签到、看看签到结果、成长中心进度。
- 需要按固定口径产出一条签到/成长进度汇报。

---

## 二、执行（唯一步骤）

用 Bash 工具**同步执行并等待命令结束**（不要 `&`、不要后台、不要提前返回），调用包装器：

```bash
python "C:/Users/Administrator/.workbuddy/skills/workbuddy-daily-automation/scripts/run_daily.py"
```

> 用哪个 Python 调包装器都行（连缺 `requests` 的托管 Python 也可以）——
> 包装器会在打印解释器那一行时告诉你它最终选了谁，并自动切到可用的那个。

或等价地直接跑主脚本（包装器只是加了保代理与结构化摘要）：

```bash
cd "D:/WorkbuddyDoc/2026-09-22-15-41-36" && "C:/ProgramData/Anaconda3/python.exe" workbuddy_daily.py
```

> **实测坑（别踩）**：托管 Python 3.13.12 **没装 `requests`**，用它跑主脚本会直接
> `ModuleNotFoundError: No module named 'requests'`。包装器会按「能 `import requests`」
> 自动挑到 Anaconda 的那个；若你绕过包装器直接指定解释器，务必用 Anaconda 那个。

**硬性约束（每次都成立）**：

1. **代理环境变量原样保留** —— 不要 `export http_proxy=`、不要 `unset`、不要清空后重设。执行前可打印确认，但绝不能改。
   > 端口每次可能不同（实测见过 `:11152`、`:12674`），这是宿主注入的本地代理，**不是异常**；
   > 判据只有一条：包装器打印的值 == 执行前 `echo $http_proxy` 的值。
2. **同步等待完成** —— 脚本含多账号串行请求与写动作间隔（默认 1.5s），全程约 1–2 分钟，务必等到退出。
3. **不要调用 `signin.py`** —— 它已被 `workbuddy_daily.py` 完全覆盖。
4. **凭据只读** —— 脚本自维护 `wb_refresh_tokens.json`；不要打印、截取、上传其中的 token。

---

## 三、汇报口径（三条，缺一不可）

只引用**脚本日志原文**，不推算、不编造：

1. **结尾进度行** —— 日志末行形如
   `🏁 <账号>: 完成X/Y 等级N 剩余: <任务列表>`
   必须原样附上这一整行。

2. **当日签到结果** —— 取 `✅签到` 那一行原话，用一句话说明。

3. **异常与人工介入** —— 逐条扫日志：
   - 命中 `登录态已失效 / 未找到登录凭据 / 网络不可达` 或退出码非 0 / stderr 非空 → 单独提醒用户处理。
   - 命中 `⚠️新任务需手动 / ⚠️未覆盖新任务` → 列出来，说明是需人工交互（如微信扫码、真实捐款），不是故障。
   - `accepted` / `accepted 0/1` 状态的成长任务（如「体验资料库」「腾讯轻量云专家」）属**常态手动项**，不算异常，简要提一句即可。

无异常时明确写「**无需处理**」，不要为了凑内容制造焦虑。

---

## 四、排障边界（关键，避免假警报）

| 现象 | 判定 | 处理 |
|---|---|---|
| `signin.py` 输出 `SKIPPED_ENCRYPTED_CRED` 且退出码 0 | **预期行为**，不是故障 | 不用管，绝不要提示用户重新登录 |
| 401 报错文案写着「登录态已失效」 | 根因是桌面端把 `accessToken` 变成 `$wbEncrypted` 信封（AES-GCM），脚本拼 header 才 401 | 登录态其实有效；让 `workbuddy_daily.py` 继续跑，它走自维护令牌链路不受影响 |
| 成长任务数分母变化（如 19 → 18） | 官方任务清单总量调整 | 不是失败，照实对比说明即可 |
| 连签天数变少、累签增加 | 跨日未续上，当日补签后显示为 1 | 不是故障 |
| 盲盒「能量不足」/ 抽奖「无次数」 | 正常资源限制 | 无需处理 |
| 任务显示 `accepted` / `accepted 0/1` 长期不掉 | 已上报未计数，需真实页面交互才落账 | 不算故障；多数下轮自动 claimed（先例：发现应用、企鹅教师助手） |
| 夜猫子 / 校园日未出现在日志 | 不在 23:00–08:00 窗口或活动未开放 | 窗口到了自动跑，无需处理 |
| 桌面端「守护进程未就绪，降级指纹上报」 | 非 Windows 或守护进程未起 | 预期降级，非故障 |

各积分任务**具体怎么完成**（上报什么事件、哪些必须人工、哪些受时间窗口限制）见
`@references/credit-tasks.md`。

**反幻觉底线**：汇报里的每个数字（完成进度、等级、连签/累签、能量、积分余额）都必须能在日志原文中找到。找不到的写「日志未体现」，绝不估算填充。

---

## 五、记忆与历史

- 每轮执行后追加一行摘要到
  `D:/WorkbuddyDoc/2026-09-22-15-41-36/.workbuddy/memory/automations/<automation-id>/memory.md`（保留历史记录，便于跨轮对比）。
- 当日工作日志追加到 `.workbuddy/memory/YYYY-MM-DD.md`（**追加，不覆盖**）。
- 判断「任务是否正常」**只看 🏁 行与退出码**，不看 signin.py。

---

## 六、参考

- `@references/credit-tasks.md` —— **积分任务怎么完成**：三条通路、逐任务 code 与完成方式
  （哪些自动、哪些需真实交互、哪些受 23:00–08:00 窗口限制）、需人工清单、脚本侧工程坑、归因速查。
- `@references/runbook.md` —— 完整执行清单、日志逐行解读、分诊决策树、历史口径样本。
- 主脚本 `D:/WorkbuddyDoc/2026-09-22-15-41-36/workbuddy_daily.py`（2540 行，勿改其业务逻辑）。
