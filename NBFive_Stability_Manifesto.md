# NBFive 稳定性与开发规约 (稳定性 100% 达成)

> [!IMPORTANT]
> **本文件为 NBFive 工具包独立规约**。任何后续 AI 在处理 `background_remover_tool` 文件夹下的代码时，必须遵循以下准则，这与“苍穹系统”是逻辑解耦的独立工具层。

## 1. 核心成就 (Technical Baseline)
- **服务器极致稳定**: 配置 2GB Swap + Systemd 守护进程运行，彻底解决 502/OOM 宕机问题。
- **QA 自动化门禁**: `remote_verify.py` 回归测试完成，确保核心功能（登录/支付/注册）永久不可退化。
- **导出 Bug 修复**: Excel 导出 V3.0 已覆盖所有数据格式（列表+表格）。

## 2. 开发三原则 (Core Rules)
1.  **QA门禁优先**: 每次部署或改动代码后，必须强制运行 `remote_verify.py` 回归脚本。
2.  **模块化隔离**: 严禁直接在 `sk_app.py` 的登录/注册/支付核心业务路径上修改，新功能必须以独立接口形式接入。
3.  **方案先行**: 涉及核心流程的修改，必须先提交 `implementation_plan.md` 审核。

## 3. 运维参考
- **主运行文件**: `sk_app.py`
- **数据持有**: `data/` 目录（包含 `orders.json` 等关键数据，不可破坏）。
- **验证脚本**: `remote_verify.py` (全量测试), `verify_payment_flow.py` (支付闭环测试)。

---
**Status**: Stable & Verified.
**Maintainer Instruction**: Refer to this file for any tool-level modifications.
