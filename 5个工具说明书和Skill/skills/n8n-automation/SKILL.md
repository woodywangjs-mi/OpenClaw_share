---
name: n8n-automation
description: Use n8n to design, build, review, or troubleshoot reliable workflow automations that connect triggers, AI tools, APIs, databases, spreadsheets, messaging, and notifications. Trigger for recurring processes, webhooks, scheduled jobs, node configuration, workflow JSON, or automation failures.
---

# n8n 自动化

将 n8n 用于规则明确、重复发生的工作。先画清数据流，再搭建节点，最后用测试数据验证。

## 工作流程

1. 定义触发器、输入数据、处理规则、输出系统、成功条件和负责人。
2. 画出最小流程：触发 → 读取/校验 → 处理 → 写入/通知 → 错误处理。
3. 配置凭证时使用 n8n Credentials；不得把密钥写入节点文本、代码或导出文件。
4. 先使用测试数据和手动执行；确认数据映射、去重和失败分支后再启用。
5. 为生产流程设置日志、错误通知、重试策略与人工兜底；记录工作流所有权。

## 设计原则

- 保持单一职责：一个工作流完成一个明确业务目标。
- 在写入外部系统前校验必填字段和幂等键，避免重复创建记录。
- 将 AI 输出视为待校验数据；对金额、审批、删除和发送外部消息设置人工确认。
- 使用 Webhook 时验证签名或令牌，并限制输入字段。

## 请求模板

`触发条件：…；来源：…；处理规则：…；目标系统：…；失败时：…；频率/量级：…；是否允许自动执行外部写入：…`。

## 工具边界

仅在已授权的 n8n 实例、凭证和目标系统中操作。没有连接时，提供节点清单、字段映射和测试用例，不声称工作流已经创建或启用。
