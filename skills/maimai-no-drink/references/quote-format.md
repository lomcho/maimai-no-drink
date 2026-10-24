# 内部报价格式

由执行 Skill 的助手在读取真实工具结构后转换；不是官方接口参数。

请求：context 为本批次不含个人信息的门店/配送场景标识；required 为核实份量后的餐品标识与数量，不限食品种类。drink_mode 默认 exclude（不含任何饮料），仅用户明确允许时设 indifferent。allow_extra_food 默认 false，只有用户同意多带食物时设 true；否则每种食物必须精确满足数量，不能额外增加其他食物。allow_resources 为用户明确同意使用的资源名列表。

每条报价：id 唯一；context 与请求一致；foods 为核验后的 SKU 数量；drinks 为不可取消的饮料数量；resources 为消耗或新购资源（例如 points、new_membership）；confirmed 和 fees_complete 必须为 true；payable_fen 为包括所有必付费用的非负整数分；quoted_at 为带时区的时间；source 为 live 或 simulation。

只有真实 calculate-price 成功且核验费用完整才可标记 live/confirmed。所有报价必须在本次批次获取，10 分钟有效窗仅为本工具保守默认，不是官方价格保证。例子可运行但明确为 simulation；实时与模拟数据不可混合。SKU 对齐、份量、券条件和资源成本由上游核验，排序脚本不代替平台试算。
