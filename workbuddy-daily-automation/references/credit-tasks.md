# 积分任务完成机制（怎么把分拿到）

> 主脚本：`D:/WorkbuddyDoc/2026-09-22-15-41-36/workbuddy_daily.py`（2540 行，v2.1）
> 本文件只做**机制说明与归因**，供技能执行层判断「某项没完成是什么原因、要不要人介入」。
> 真正实现逻辑以脚本源码为准，行号对应脚本当前版本。
>
> 关键前提：**成长中心任务是「上报即计分」**，不是「点了才算」。
> 绝大多数任务靠构造并上报一段符合官方埋点格式的遥测事件来点亮进度；
> 只有少数几项需要真实人工动作。这意味着脚本能在无人值守下跑完绝大部分任务。

---

## 一、三条完成通路

| 通路 | 手段 | 覆盖 |
|---|---|---|
| **A · 签到链路** | `POST /v2/billing/meter/daily-checkin`（幂等） | 每日签到 |
| **B · 批量 accept + 遥测上报** | 先批量 `accept` 未接任务，再逐项 `report` 事件 | 18 项成长任务主体 |
| **C · 桌面端真实交互** | Windows 走真实桌面换血；非 Windows / 守护进程未就绪时**降级为指纹上报** | 桌面侧任务（design / skill 等） |

**通用推进逻辑（`prog()`）**：每次动作前先读任务进度
`GET /v2/activity/growth/tasks` 的 `accept_status` / 进度值；
已 `completed` 或 `claimed` 的直接跳过，**绝不重复上报**（脚本幂等安全的来源）。

---

## 二、逐任务完成方式

`code` 与日志里打印的名字一致。状态列：✅自动 / ⚠️需人工 / ❌窗口条件。

### 成长任务（通路 B 为主）

| code / 日志名 | 完成方式 | 状态 |
|---|---|---|
| `chat_5`（RichMeow_Chat） | 发 5 次真实 web 对话，逐次上报 `chat_request_events` | ✅ |
| `Model_chat_GLM5.2` | 同上，走 GLM 对话，上报请求/响应事件 | ✅ |
| `template_5`（playbook_prompt） | 批量构造 5 个场景模板事件（`agent_task_created` + `..._with_template` + `playbook_prompt_send`） | ✅ |
| `expert_5`（召唤5次专家） | 逐个 `expert_summoned` + `expert_actual_use` 事件，字段含 requestId/messageId/characterCount | ✅ |
| `Expert_team_use_3`（召唤3次专家团） | 真实团队对话 + **全字段遥测**，比普通专家要求更严 | ✅ |
| `create_canvas` / `automation_1` | 设计创意模式 + 自动化任务 + 优秀灵感三项事件 | ✅ |
| `Library_read`（体验资料库） | `report_web_event(..., "web_element_click", LIB_DOC_URL, "library_doc_intro_click", ...)`，即模拟点击「资料库介绍」，间隔 6s 后回读进度 | ⚠️ 常驻accepted |
| `Hp_Appearance` / `black_cat`（夜猫子） | 受 `within_night_window()` 约束，**仅 23:00–08:00** 窗口才上报 | ❌ 窗口 |
| `Buddy_App` / `Buddy_App_QQ` | 小程序端应用使用事件 | ✅ |
| `first_buddy` | 首次 Buddy 事件 | ✅ |
| `skill_1` | 技能调用遥测（桌面守护进程装技能触发） | ✅ |
| `Expert_lighthouse`（轻量云专家） | 点亮类遥测 | ⚠️ 常驻accepted |
| `Expert_Philanthropy`（公益专家） | **需真实捐款**，脚本无法代劳 | ⚠️ 人工 |
| `workstation_expert` / `Sequential_Tasks_1/2` / `school_season`（校园日） | 小程序侧事件（`mp_chat_event` / `mp_expert_use_events`），带 `activity_id=school_open_day_2026` | ✅ / ❌视下发 |

### 玩法类（积分来源是「互动」而非「任务」）

| 玩法 | 完成方式 | 状态 |
|---|---|---|
| 签到 | `daily-checkin`，幂等，重复跑安全 | ✅ |
| 补签卡 | `t_makeup()`，仅当检测到漏签且持有补签卡才触发 | ✅ |
| 抽奖 | `t_lottery()`，余额/次数为 0 时跳过 | ✅ |
| 盲盒 | `t_blindbox()`，**需能量达标（10）**，不足则跳过 | ❌ 资源 |
| Buddy 名片 | `t_buddy_info()` | ✅ |
| 派猫猫旅行 | `t_travel()` 幂等状态机：`arrived`→`claim` 领礼物；`traveling`→只报剩余分钟；`idle` 且未达 `daily_limit_reached`→**主动 `depart` 出发**（取 `locations[0]`）；无 Buddy 直接跳过 | ✅ 自动派+领 |
| 连签兑换 | `t_redeem()`，按连签天数兑换档位 | ✅ |
| 礼包补偿 | `t_gift_compensation()`，补领历史漏发 | ✅ |
| 徽章 | `t_badges()`，展示 7 枚 | ✅ |

---

## 三、需人工介入的（脚本完成不了，别当故障报）

1. **微信扫码关注公众号** —— 日志 `⚠️新任务需手动: …需微信扫码关注公众号`。
2. **真实捐款（公益专家）** —— `⚠️…涉及真实捐款`。
3. **`accepted` / `accepted 0/1` 常驻态** —— 脚本报过 accept 但服务端未计数，
   典型是「体验资料库」「腾讯轻量云专家」，需要打开对应页面产生真实交互才落账。
   **逐轮重试即可，很多会在后续某轮自动 claimed**（09-28 轮「发现应用」「企鹅教师助手」就是这么从 accepted 变成 claimed 的）。

---

## 四、脚本侧的工程坑（影响完成率）

1. **accept 是逐任务返回状态**：`POST /v2/activity/growth/tasks/accept` 顶层 `code=0`
   只代表请求送达；实际逐项在 `data.results[]` 里返回 `accepted`/`error`。
2. **存在 200+OK 但未落账**：所以 `t_accept_all()` 会**回读验证 + 逐个重试**
   （`_accept_with_verify`），仍失败的才升级为 `⚠️仍无法登记`。
3. **夜猫子窗口**：`black_cat` 在非 23:00–08:00 运行时直接跳过，这是设计如此。
4. **桌面端守护进程**：未就绪时自动降级为指纹上报，日志会出现
   `⚠️ 桌面端守护进程未就绪，降级为指纹上报...`，属预期。
5. **新任务检测**：`t_unknown_tasks()` 比对 `known` 集合（22 个 code），
   未命中的按关键词猜类型；猜不出就打 `⚠️未覆盖新任务: …请反馈更新脚本`——
   **这是需要更新脚本任务模板的信号**，不是用户操作问题。

---

## 五、归因速查

日志里「没完成」时，按此表定位：

| 日志表现 | 原因 | 动作 |
|---|---|---|
| `completed` / `claimed` | 已完成领奖 | 无 |
| `accepted` / `accepted 0/1` | 已上报未计数，需真实交互 | 下轮重试；多为长期手动项 |
| `能量不足 (5/10)` | 盲盒资源不够 | 攒能量，无动作 |
| `无次数` | 抽奖额度用尽 | 无动作 |
| 夜猫子/校园日未出现 | 不在时间窗口 | 无动作 |
| `⚠️仍无法登记 N 项` | accept 不落账 | 收集日志反馈脚本作者 |
| `⚠️未覆盖新任务` | 官方新增任务，脚本模板缺 | 记录 code + 标题，更新脚本 |
| `⚠️新任务需手动` | 需扫码/捐款 | 提醒用户人工做 |
