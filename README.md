<div align="center">

# WorkBuddy AutoCredits

**WorkBuddy 自动化技能包合集**

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Skill](https://img.shields.io/badge/Skill-workbuddy--daily--automation-green.svg)](./workbuddy-daily-automation)

中文 · [English](#english)

</div>

---

## 📖 这是什么

本仓库集中存放、版本管理与分发自用的 **[WorkBuddy](https://www.workbuddy.cn) 自动化技能包**。

每个技能以独立子目录存在，遵循 `SKILL.md + scripts/ + references/` 的标准结构，
可直接复制到 `~/.workbuddy/skills/<skill-name>/` 下安装使用，也可被 WorkBuddy
的自动化（automation）任务直接调度。

> 设计原则：**只读凭据、不改代理、汇报只引用日志原文** —— 宁可少做，绝不臆造。

---

## 📦 技能一览

| 技能 | 定位 | 一句话说明 | 版本 |
|:---|:---|:---|:---:|
| [`workbuddy-daily-automation`](./workbuddy-daily-automation) | ⏱️ 定时任务 · 无人值守 | 跑完 WorkBuddy 每日签到 / 成长中心全套任务 / 自动领奖，并输出可核对的固定口径汇报 | `v1.0.1` |

---

## ⏱️ workbuddy-daily-automation

面向 **定时任务 / 无人值守** 场景的 WorkBuddy 每日自动化执行器。

它与交互式查询类技能分工明确：本技能负责「**定时跑 + 跑完怎么汇报 + 报错怎么分诊**」，
不负责「人机对话式的积分查询与播报」。

### ✨ 功能覆盖

| 模块 | 内容 |
|:---|:---|
| 🎯 **每日签到** | 签到（幂等，可重复运行）+ 补签卡自动补漏 |
| 🌱 **成长中心任务** | 18 项云端 / 桌面任务全覆盖（批量 accept + 遥测上报 + 回读验证） |
| 📱 **小程序任务** | 校园日、小程序对话、小程序专家对话（共 +400c +15e） |
| 🏫 **开学季活动** | 分享 / 对话 / 桌面对话 / 专家 + 幸运大转盘 |
| 🎮 **互动玩法** | 抽奖、盲盒、Buddy 信息、派猫猫旅行、连签兑换、补签卡、礼包补偿、徽章 |
| 🎁 **自动领奖** | 扫描全部已完成任务自动领取；`completed` 未领的自动补领 |
| 📢 **双渠道推送** | PushPlus（微信）+ Bark（iOS），可选、互不影响 |
| 🔐 **凭据永续** | 只配一个刷新令牌，脚本自动续期（90 天滚动），令牌轮换即时回写 |

> ❌ **不做**：公益专家（需真实捐款）、微信扫码关注（需真人操作）、学生认证（需微信实名）。
> 这些是**人工环节而非故障**，脚本会识别并提示。

### 🧩 三件套职责

技能由三个文件分工协作，各司其职：

| 文件 | 角色 | 职责 |
|:---|:---|:---|
| `scripts/run_daily.py` | 🎛️ **执行包装器** | 挑解释器 · 保代理 · 同步等待 · 抽取汇报三要素 |
| `scripts/workbuddy_daily.py` | ⚙️ **主脚本**（2540 行） | 全部业务逻辑：签到 / 任务 / 玩法 / 领奖 |
| `SKILL.md` + `references/` | 📚 **技能契约** | 触发条件、执行口径、汇报口径、排障边界 |

**包装器**（`run_daily.py`）只做四件事，绝不碰业务逻辑：

1. **挑解释器** —— 自动选「真的能 `import requests`」的 Python（Anaconda 优先），选不出就明确报错，不静默降级；
2. **保代理** —— 原样保留 `http_proxy` / `https_proxy` 并透传子进程，**绝不清空**；
3. **同步等待** —— 等主脚本跑完，原样回放 stdout / stderr 与退出码（不后台化、不截断）；
4. **抽要素** —— 从日志稳定抽取 **汇报三要素**：`🏁` 进度行 / `✅签到` 行 / `⚠️` 人工介入行。

### 🚀 安装

```bash
# 1. 克隆仓库
git clone https://github.com/ZacK-BOX/WorkBuddy-AutoCredits.git

# 2. 复制技能到本地技能目录（Windows 默认路径）
cp -r WorkBuddy-AutoCredits/workbuddy-daily-automation \
      ~/.workbuddy/skills/
```

### ▶️ 使用

**方式一：调包装器（推荐，含保代理与结构化摘要）**

```bash
python ~/.workbuddy/skills/workbuddy-daily-automation/scripts/run_daily.py
```

**方式二：直接跑主脚本**

```bash
python <技能目录>/scripts/workbuddy_daily.py
```

**主脚本命令行参数**

| 参数 | 说明 |
|:---|:---|
| *(无)* | 全流程：续期 → 查询 → 任务 → 开学季 → 领奖 |
| `--refresh` | 仅刷新所有账号 Token |
| `--query` | 仅查询积分 / 用量 / 成长 |
| `--no-desktop` | 跳过桌面任务（非 Windows 默认走指纹上报） |
| `--no-school` | 跳过开学季活动 |
| `--school-only` | 只跑开学季活动 |
| `--only N` | 只跑第 N 个账号 |
| `--gap SEC` | 写动作间隔秒数（默认 1.5，最低 1.0） |

### 🔑 环境变量

| 变量 | 必填 | 说明 |
|:---|:---:|:---|
| `WORKBUDDY_REFRESH_TOKEN` | ✅ | 多账号刷新令牌，每行 `手机号:AT:RT`，换行分隔（首次运行据此自举令牌库） |
| `PUSHPLUS_TOKEN` | ⬜ | PushPlus 推送（微信） |
| `BARK_URL` | ⬜ | Bark 推送（iOS），如 `https://api.day.app/xxxxxxxx` |
| `WBDAILY_WORKSPACE` | ⬜ | 包装器用：主脚本所在工作区目录 |
| `WBDAILY_PYTHON` | ⬜ | 包装器用：显式指定 Python 解释器绝对路径 |
| `WBDAILY_SCRIPT` | ⬜ | 包装器用：主脚本文件名（默认 `workbuddy_daily.py`） |

### 📋 依赖与前提

- 本仓库**已自带主脚本** `scripts/workbuddy_daily.py`（2540 行），**开箱即用、无需额外下载**；
- 需要一份本机明文令牌库 `wb_refresh_tokens.json` —— 首次运行可从 `WORKBUDDY_REFRESH_TOKEN` 自举生成，
  之后脚本自动续期、自动回写；
- Python 3.x，且已安装 `requests`。

> 💡 **解释器小坑**：WorkBuddy 托管的 Python 3.13.12 **只装标准库、没有 `requests`**。
> 直接用它会 `ModuleNotFoundError`。包装器会按「能否 `import requests`」自动挑可用解释器，
> 所以**尽量走包装器**；若要绕过，请显式指定装了 `requests` 的解释器。

### 📂 目录结构

```
workbuddy-daily-automation/
├── SKILL.md                    # 🎯 技能主入口：触发条件、执行口径、汇报口径、排障边界
├── scripts/
│   ├── run_daily.py            # 🎛️ 执行包装器：保代理 + 同步等待 + 结构化摘要
│   └── workbuddy_daily.py      # ⚙️ 主脚本：签到 + 18 项成长任务 + 8 项玩法 + 自动领奖
└── references/
    ├── credit-tasks.md         # 📊 积分任务完成机制：三条通路、逐任务 code、需人工清单
    └── runbook.md              # 🩺 执行手册：日志逐行解读、分诊决策树、汇报模板
```

### 🛡️ 安全说明

- ⚠️ `wb_refresh_tokens.json` 与 `WORKBUDDY_ACCESS_TOKEN.txt` 含**明文 access / refresh token**，
  属敏感凭据；本仓库 `.gitignore` 已将其排除，**请勿手动提交**。
- ✅ 脚本本身**不含任何账号、手机号、Token 或设备信息** —— 所有凭据均由环境变量注入或运行时生成。
- ✅ 所有个人路径均通过 `os.path.expanduser("~")` 或环境变量解析，无硬编码目录。

### 🩺 排障速查

| 现象 | 判定 | 处理 |
|:---|:---|:---|
| `登录态已失效` / HTTP 401 | 桌面端把 `accessToken` 改为 AES-GCM 加密信封（`$wbEncrypted`），`signin.py` 拼 header 才 401 | **误报非故障**，登录态有效，**勿让用户重新登录** |
| `⚠️新任务需手动` | 需扫码关注 / 真实捐款 | 列出提示人工处理，不算故障 |
| `accepted` / `accepted 0/1` 长挂 | 已上报未计数，需真实页面交互 | 常态手动项，下轮可能自动 claimed |
| 任务总数分母变化（如 19 → 18） | 官方清单调整 | 照实对比，非失败 |
| `能量不足` / `无次数` | 资源限制 | 无需处理 |
| 夜猫子 / 校园日未出现 | 不在 23:00–08:00 窗口或活动未开放 | 窗口到了自动跑 |

> 详细口径见 [`references/runbook.md`](./workbuddy-daily-automation/references/runbook.md)。

**反幻觉底线**：汇报里的每个数字（进度、等级、连签/累签、能量、积分余额）都必须能在日志原文中找到；
找不到就写「日志未体现」，**绝不估算填充**。

---

## 📄 许可 License

[MIT](./LICENSE) © ZacK-BOX

---

<div align="center">

## English

**A collection of automation skills for [WorkBuddy](https://www.workbuddy.cn).**

Each skill lives in its own subdirectory following the standard
`SKILL.md + scripts/ + references/` layout, and can be dropped into
`~/.workbuddy/skills/<skill-name>/` to install.

| Skill | Description | Version |
|:---|:---|:---:|
| [`workbuddy-daily-automation`](./workbuddy-daily-automation) | Unattended daily automation: check-in / makeup check-in, all growth-center tasks, and auto reward claim — with a fixed, verifiable reporting protocol | `v1.0.1` |

**Core principles: read-only credentials, never touch the proxy, quote only raw log lines.**

> ⚠️ `wb_refresh_tokens.json` and `WORKBUDDY_ACCESS_TOKEN.txt` hold plaintext tokens and are
> excluded via `.gitignore`. The scripts themselves contain no account, phone number, token,
> or device info — all credentials are injected via environment variables at runtime.

Licensed under [MIT](./LICENSE).

</div>
