# 谁在数据库中留下了入仕路径记录？

[English README](README.md)

本仓库是一个 CBDB 数据挖掘课程项目的 Phase 3.1.1 冻结公开版本，研究中国历代人物传记资料库（CBDB）中记录结构、文献记录过程与分布偏移。

## 研究问题与预测目标

项目考察个人、地域、家族与文献记录特征在多大程度上能够预测：一个被 CBDB 收录的人是否至少拥有一条 `ENTRY_DATA` 记录。

预测目标是回溯性的 **ENTRY 记录存在性**（`E`），不是真实历史入仕状态（`T`），也不是任官记录存在性（`P`）。三者不可互换。模型不恢复历史真值，文中关联也不是因果效应。

## 冻结版本

Phase 3.1.1 仅进行非实验性发布修订：未训练或调参，未选择新切分，未访问 reserve/protected data，未重建缺失置信区间，也未改变冻结预测和指标。

Global D5_MAIN 的核心冻结结果保持为：ROC-AUC 0.936956、PR-AUC 0.882535、raw LogLoss 0.315106、raw Brier 0.097356、validation-calibrated ECE 0.003438。

解释边界和未完成的稳健性检验见[最新结果摘要](docs/phase3_1_1/latest_results_summary.md)、[主张—证据映射](docs/phase3_1_1/final_claim_evidence_map.md)和[可复现性审计](docs/phase3_1_1/final_reproducibility_audit.md)。

## 论文

- [作者版 PDF](paper/final/cbdb_kdd_style_author_final.pdf)
- [匿名版 PDF](paper/final/cbdb_kdd_style_anonymous_final.pdf)
- [LaTeX 源文件与参考文献](paper/final/)

两个 PDF 的冻结 SHA-256 分别为：

```text
6d010ffb2592b3e3309efb69ffcb480f841c80c90e55c918b0acc03f85adcaa2  cbdb_kdd_style_author_final.pdf
988b050c0045541209d2eb01ea0d28739ecdf6c56d6073faac2c02f71bd2f624  cbdb_kdd_style_anonymous_final.pdf
```

## 数据可用性

CBDB 是第三方研究数据库。本仓库不重新分发 CBDB SQLite，也不授予其数据的使用或再分发权。请通过官方 [CBDB SQLite 发布渠道](https://github.com/cbdb-project/cbdb_sqlite)合法取得数据并遵守提供方条款。

冻结分析使用 `cbdb_20260829.sqlite3`，其中有 661,124 条 `BIOG_MAIN` 人物记录。该数字只适用于此数据快照，不代表中国历史总体人口。

仓库明确排除了原始及派生数据库、逐行特征矩阵、完整 split、训练模型、全量预测、protected/reserve artifact、缓存、日志和重复的发布 ZIP。因此，本仓库适合审查代码、论文、配置、轻量汇总证据和发布检查，但不是私有冻结实验工作区的完整副本。

## 环境安装

推荐 Python 3.11：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

或使用 Conda：

```bash
conda env create -f environment.yml
conda activate cbdb
```

## 公开版本验证

以下检查不会训练模型，也不会修改冻结产物：

```bash
python scripts/verify_public_release.py
PYTHONPATH="$PWD/tests/import_stubs:$PWD" python -m pytest -q \
  tests/test_phase3_1_1_claims.py \
  tests/test_phase3_1_1_methods.py
```

完整归档 runner [`scripts/run_phase3_1_1_final_polish.sh`](scripts/run_phase3_1_1_final_polish.sh) 依赖未公开的冻结模型、切分、预测、编译中间件和可选图件审计工具。公开仓库缺少这些输入时，它会按设计停止；该脚本仅供方法透明性和授权完整工作区使用，不是公开仓库的 smoke test。

## 目录结构

```text
configs/                  冻结的特征、模型、报告与地理配置
docs/phase3_1_1/          范围、审计、主张—证据和可复现性记录
outputs/                  轻量汇总表、manifest 与方法规范
paper/final/              最终 PDF、LaTeX/BibTeX、表格和图件
scripts/                  非实验性发布及审计脚本
src/                      特征、地理和通用模块
tests/                    完整工作区测试与可公开运行的聚焦测试
```

基线 SHA-256 清单同时记录公开汇总文件和明确排除的私有 artifact。清单中出现某个哈希，不表示对应数据库、模型、split 或预测文件已在仓库中分发。

## 复现边界

- 公开检查验证 PDF 身份、仓库卫生、冻结主张和 `local_target_prior` 行为。
- 完整端到端复现需要合法 CBDB 访问和私有冻结实验 artifact。
- 当前公开内容不足以从逐行数据重新训练或独立重算全部论文指标。
- Whole-family 证据仅适用于 Global 和 Ming 的冻结 F2 comparator，未直接检验 D5_MAIN。
- 结果不能解释为人口入仕率、历史真值或因果估计。

## 引用与许可

引用信息见 [`CITATION.cff`](CITATION.cff)。项目代码和文档使用 [MIT License](LICENSE)；该许可不覆盖第三方 CBDB 数据，也不授予数据再分发权。
