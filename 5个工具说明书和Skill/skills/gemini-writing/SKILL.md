---
name: gemini-writing
description: Use Gemini for Chinese writing, research-note organization, structured thinking, drafting plans, summaries, emails, presentations, and decision comparisons. Trigger when the user needs an AI secretary to turn goals or source material into clear, editable business content.
---

# Gemini 写作与思考

将 Gemini 作为写作与思考助手使用。先确认目标、读者、已有材料、输出形式和截止时间；信息不足时先提出最少必要问题。

## 工作流程

1. 将模糊需求改写为交付目标，例如“给管理层的一页项目汇报”。
2. 区分事实、假设和待确认项；不得编造来源、数据或结论。
3. 先给结构或提纲；用户要求直接成稿时，可同时给出完整初稿。
4. 用清晰标题、短段落和行动项组织内容，保留用户原意与语气。
5. 交付前检查：是否回答了问题、逻辑是否连贯、是否含可执行下一步、事实是否需要核验。

## 常用产出

- 方案：背景、目标、范围、方案、里程碑、风险、资源与下一步。
- 资料整理：主题摘要、关键事实、分歧、引用来源、待确认事项。
- 会议纪要：结论、决策、负责人、截止时间、风险和待办。
- 决策比较：比较维度、各方案优缺点、适用条件、建议与理由。

## 提示词模板

`角色：…；目标读者：…；任务：…；材料：…；约束：…；输出格式：…；语气：…`。

示例：`把以下会议记录整理为给总经理的一页汇报。只依据材料；列出风险和负责人；中文正式、简洁。`

## 安全与工具边界

仅在已授权且实际可用的 Gemini 连接、浏览器或 API 中执行操作。没有连接时，先交付可直接粘贴到 Gemini 的提示词和工作步骤。不得输入或转发密钥、身份证号、未授权商业机密等敏感数据。
