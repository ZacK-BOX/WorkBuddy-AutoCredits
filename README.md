# WorkBuddy AutoCredits

> 一组面向 [WorkBuddy](https://www.workbuddy.cn) 的自动化技能（Skills）合集。
> A collection of automation skills for WorkBuddy.

本仓库用于集中存放、版本管理与分发我自用的 WorkBuddy 技能包。每个技能以独立子目录形式存在，遵循
`SKILL.md + scripts/ + references/` 的标准结构，可直接复制到
`~/.workbuddy/skills/<skill-name>/` 下安装使用。

---

## 目录 Contents

| 技能 | 说明 | 版本 |
|---|---|---|
| [`workbuddy-daily-automation`](./workbuddy-daily-automation) | 无人值守执行 WorkBuddy 每日自动化（签到/补签 + 成长中心全套任务 + 自动领奖），并输出固定口径汇报 | v1.0.1 |

---

## workbuddy-daily-automation

面向**定时任务 / 无人值守**场景的 WorkBuddy 每日自动化执行器。

### 它能做什么

- **一键跑完每日流程**：签到 / 补签 → 成长中心全部任务（批量 accept + 遥测上报）→ 自动领奖。
- **执行包装器**（`scripts/run_daily.py`）负责四件事：
  1. 自动挑选**真的能 `import requests`** 的 Python 解释器（Anaconda 优先），选不出就明确报错；
  2. 原样保留 `http_proxy` / `https_proxy` 环境变量并透传子进程，绝不清空；
  3. 同步等待主脚本跑完，原样回放 stdout / stderr 与退出码；
  4. 从日志中稳定抽取**汇报三要素**（🏁 进度行 / ✅签到 行 / ⚠️ 人工介入行）。
- **反幻觉排障规则**：桌面端把 `accessToken` 改为 AES-GCM 加密信封（`$wbEncrypted`）后，
  `signin.py` 报的「登录态已失效」是**误报而非故障** —— 技能明确规定不得让用户重新登录。

### 安装

```bash
# 1. 克隆仓库
git clone https://github.com/ZacK-BOX/WorkBuddy-AutoCredits.git

# 2. 复制技能到本地技能目录（Windows 默认路径）
cp -r WorkBuddy-AutoCredits/workbuddy-daily-automation \
      ~/.workbuddy/skills/
```

### 使用

```bash
python ~/.workbuddy/skills/workbuddy-daily-automation/scripts/run_daily.py
```

可选环境变量：

| 变量 | 说明 |
|---|---|
| `WBDAILY_WORKSPACE` | 主脚本 `workbuddy_daily.py` 所在的工作区目录 |
| `WBDAILY_PYTHON` | 显式指定 Python 解释器绝对路径 |
| `WBDAILY_SCRIPT` | 主脚本文件名（默认 `workbuddy_daily.py`） |

### 依赖与前提

- **主脚本** `workbuddy_daily.py` 需另行放置于工作区（本仓库不包含其源码，业务逻辑较重且与本机环境强耦合）。
- 需要一份**本机明文令牌库** `wb_refresh_tokens.json`（脚本自续期、自动回写；请勿提交到版本库）。
- Python 3.x 且已安装 `requests`。

> ⚠️ **安全提醒**：`wb_refresh_tokens.json` 含有明文 access token / refresh token，
> 属于敏感凭据。本仓库的 `.gitignore` 已将其排除，请勿手动提交。

### 文档结构

```
workbuddy-daily-automation/
├── SKILL.md                    # 技能主入口：触发条件、执行口径、汇报口径、排障边界
├── scripts/
│   └── run_daily.py            # 执行包装器：保代理 + 同步等待 + 结构化摘要
└── references/
    ├── credit-tasks.md         # 积分任务完成机制：三条通路、逐任务 code、需人工清单
    └── runbook.md              # 执行手册：日志逐行解读、分诊决策树、汇报模板
```

---

## 许可 License

[MIT](./LICENSE) © ZacK-BOX
