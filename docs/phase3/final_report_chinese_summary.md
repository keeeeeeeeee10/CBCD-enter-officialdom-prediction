# 谁会留下入仕记录？——CBDB 最终科研摘要

## 任务与数据

本项目在冻结的 `cbdb_20260829.sqlite3` 上分析 661,124 个 CBDB 人物记录。主标签 **E** 是人物是否至少一次出现在 `ENTRY_DATA`；辅助标签 **P** 是是否存在有效任官记录；**T** 是不可直接观测的历史真实入仕状态。始终有 `E != T`、`P != T`、`E != P`，模型估计的是 `Pr(E=1|X)`，不是历史真实入仕概率。

## 方法与主要结果

项目比较冻结的 Logistic baseline、H_STRUCT、D5_MAIN 与 D6_UPPER，并使用分组消融、family holdout、matched-support spatial shift、五随机种子、校准和 grouped SHAP。主模型 D5_MAIN 的 Global ROC-AUC 为 0.936956，PR-AUC 为 0.882535，LogLoss 为 0.315106，Brier 为 0.097356，验证集拟合校准后的 ECE 为 0.003438。

主要预测信息来自性别、时代、地址与亲属记录可观测性、历史行政区、家族拓扑和 documentation process。经纬度、首都距离与 local prior 在已有地域变量之后的条件增量很小。亲属政治资本在控制可观测性和拓扑之后只有很小的独立增量，不能解释为家族政治资本具有大的历史效应。

## 稳健性与来源审计

匹配支持集上的未见地区测试显示 Global、Song、Ming 均有迁移性能下降；family-group holdout 的下降较小。SAFE temporal 只有冻结切分而没有 Phase 2.6 锁定模型性能产物；Qing 也没有预先冻结的 holdout，因此 Phase 3 没有事后补建结果。

来源层面实际审计了 `BIOG_SOURCE_DATA.c_main_source`。452,035 名合格人物形成 145 个主来源连通组，但最大组含 448,632 人，占 99.25%，超过 20% 预设门槛。因此状态为 `SOURCE_GROUP_CONFIRMATION_NOT_FEASIBLE`，未训练任何来源 confirmation 模型。

## 局限

CBDB 不是古代人口随机样本；史料保存、编辑选择和数据库编码共同影响标签与特征。D5_MAIN 是回顾性数据库记录分类器，不是严格前瞻预测。部分家族结构是数据库内部或 transductive，亲属 lifetime outcome 存在时间歧义，安全出生年覆盖低，primary test 曾在多阶段被查看。SHAP 不是独立消融增量，更不是因果效应；bootstrap 也不覆盖标签定义、收录与史料不确定性。
