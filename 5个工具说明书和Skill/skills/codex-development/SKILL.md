---
name: codex-development
description: Use Codex for software development tasks including understanding a repository, diagnosing bugs, implementing minimal code changes, writing tests, reviewing diffs, and verifying results. Trigger for code, errors, APIs, scripts, refactors, or engineering documentation.
---

# Codex 编程开发

将 Codex 作为程序员使用，以可验证的最小修改完成需求。

## 工作流程

1. 复述需求，定义成功标准、影响范围和假设；需求关键处不清晰时先询问。
2. 阅读相关代码、配置、测试和报错，先定位原因，不修改无关文件。
3. 提出最小实现方案；说明修改文件、兼容性影响和验证方法。
4. 实施代码与必要测试，遵循项目现有风格；不加入推测性抽象或无关重构。
5. 运行与改动相称的测试、静态检查或复现步骤，报告结果与未验证项。

## 缺陷处理

记录复现条件、实际结果、预期结果与根因。优先新增能稳定复现问题的测试；修复后证明该测试通过并检查相邻功能。

## 新功能处理

明确输入、输出、错误场景和验收条件。先实现主路径，再补充用户明确要求的边界处理；避免为未来假设增加接口或配置。

## 请求模板

`项目路径：…；技术栈：…；目标：…；现象/报错：…；预期：…；限制：…；验证命令：…`。

## 安全边界

修改前检查工作区已有变更。未经明确授权，不执行部署、推送、删除数据、重置版本库或外部系统写入。涉及密钥时使用环境变量或现有安全配置，绝不在代码或日志中暴露密钥。
