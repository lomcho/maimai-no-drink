# MCP 实际接入

2026-10-24已完成首次真实询价。服务 https://mcp.mcd.cn，Streamable HTTP，Bearer Token。实测服务mcd-mcp/1.0.0，协商协议2024-11-05。

实际链路：initialize → tools/list → delivery-query-addresses → 用户选地点 → delivery-query-stores → query-meals / query-store-coupons → query-meal-detail → calculate-price。

上述工具均已成功调用。4种组合正式试算成功，包含餐品、配送、打包和应付金额。套餐默认项与替换项来自实时详情。

当前会话未自动显示新增工具，首次通过Python标准库执行MCP HTTP，复用本地客户端已配置凭证。一次性探测脚本、凭证与地址不随发布包提供。交付的Skill由使用者自己的MCP客户端执行，不依赖作者账号。

业务价值：将“家里有饮料”转为无需为饮料额外付费的偏好，清楚给出单点/套餐的实付差额和多余物品。

参数处理见 skills/maimai-no-drink/references/live-integration.md。菜单现价为元、试算金额为分；price_guard.py 检查成功状态、整数金额和费用合计。费用不完整、结构变化时不直接排名。原型v0.1尚未实调，此版本更新该状态，历史原型仍保留。

真实询价记录-20261024.md 为人工整理的脱敏记录；examples/live-snapshot.json 是成功试算提取的历史金额快照，不是完整原始响应；scripts/replay.py 以原时间重放验证，不产生当前报价。

未验证：全面穷举、跨店最低价、所有优惠叠加、真实成交。未使用WorkBuddy、未创建订单。真实参数仍以tools/list为准。

mcp-config.example.json 仅含环境变量占位符；codex-config.example.toml 限定只读工具。变量值通过本机设置提供，不写入仓库。用户客户端本地静态Authorization配置也不应导出或截图公开。

官方文档：https://github.com/M-China/mcd-mcp-server
