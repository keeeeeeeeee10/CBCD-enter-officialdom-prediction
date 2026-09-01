# Phase 3.1 Data, Code, and Reproducibility Audit

## Blocking issues resolved

1. The manuscript previously compressed data, code, and reproducibility into one paragraph. They are now separated so that third-party data rights are not conflated with the MIT licence for project code.
2. The full CBDB SQLite and working database must not be redistributed. The pipeline instead records the exact official release, official source route, archive hash, SQLite hash, and verification status.
3. “All data are in the paper” would be false: the full database, 661,124-row feature master, and large intermediate artifacts are intentionally absent. The revised statement names what is and is not packaged.
4. The local deliverables do not have a repository DOI or accession. Therefore the manuscript describes accompanying submission/review artifacts and does not claim a public archival identifier that does not exist.
5. The official local CBDB release metadata does not state a redistributable data licence. The revised wording does not infer one; readers are directed to the official project and its current terms.

## Dataset inventory and access classification

The machine-readable inventory is `outputs/phase3_1/tables/data_availability_inventory.csv`. It covers the third-party SQLite release, download metadata, frozen splits, model metadata and hashes, the Phase 3.1 prediction file, figure source snapshots, large excluded intermediates, and project code.

The analysis used official release `cbdb_20260829.sqlite3`, generated on 2026-08-29. The verified SQLite SHA256 is:

`f620ca1a4c794411b81d5039adf5756df129fb9aa0f4509b4c843bb66e0caa2a`

The archive SHA256 recorded at download is:

`96895410ae6f52d2555a12700da6f25ab72f3bf74dfae3a065e883330e427c21`

The Phase 3.1 frozen-test prediction file is Parquet with zstd compression and has SHA256:

`86ee951335c09fbaf3e010ce95407304a612243ea1e18affd784db55fd526fbe`

## Ready-to-paste manuscript text

### Data Availability

This study reuses the China Biographical Database (CBDB), a third-party historical database available through the official CBDB project and its official SQLite release channel \cite{cbdb2026,fuller2024}. The analysis used `cbdb_20260829.sqlite3` (release metadata generated 29 August 2026), whose official SHA256 is `f620ca1a4c794411b81d5039adf5756df129fb9aa0f4509b4c843bb66e0caa2a`. The full raw or working SQLite database is not redistributed. The supplied download script retrieves the release identified by the official `latest.json` record and stops unless the observed SHA256 matches the official value; users remain responsible for the official CBDB access and use terms. The accompanying review artifact contains the derived frozen-test predictions needed to recompute the reported locked-model metrics, together with the final tables and the source-data snapshots underlying all figures. Large feature matrices and other regenerable intermediate files are excluded from the paper packages; they can be rebuilt from the verified official release using the supplied pipeline. No claim is made that the package contains a census of historical people or complete historical ground truth.

### Code Availability

The accompanying code package contains the download and SHA256-verification utility, preprocessing and feature-construction scripts, frozen-split logic, model and evaluation workflows, Phase 3.1 statistical and figure scripts, configuration files, environment specifications, and automated tests. Project code and documentation are provided under the MIT License; that licence does not grant rights to redistribute CBDB data. No external repository DOI or accession has been assigned to this local course-project archive, and none is claimed.

### Reproducibility Statement

All headline results refer to frozen Phase 1–2.6 artifacts. The canonical seed is 42, the primary person identifiers and split hashes are fixed, and test labels were not used for hyperparameter selection, threshold selection, early stopping, or calibration fitting. The review artifact records the Python and SQLite environments, package versions, resolved feature lists, exact CatBoost parameters, nine canonical model hashes, frozen thresholds, prediction hashes, validation-fitted calibration status, statistical correction manifest, figure-input hashes, and ZIP manifests. `bash scripts/run_phase3_1_nature_revision.sh` regenerates the Phase 3.1 tables, figures, revised papers, audits, tests, and packages from the required frozen inputs. The full feature master and large intermediates are omitted from the archives but are deterministically regenerable from the SHA256-verified official SQLite release.

## FAIR and metadata audit

| Principle | Status | Evidence and remaining boundary |
|---|---|---|
| Findable | **Partial** | Official CBDB project and release metadata provide a stable discovery route; local submission/review ZIPs have file manifests and hashes. The derived archive does not yet have a public DOI or accession. |
| Accessible | **Pass with third-party boundary** | Official CBDB download route and integrity metadata are explicit. Redistributable derived source tables are packaged; the full third-party SQLite is intentionally excluded. |
| Interoperable | **Pass** | Tables use CSV/JSON; prediction and split artifacts use Parquet; figures use PNG/PDF/SVG; schemas, paths, hashes, and environment files are included. |
| Reusable | **Pass for code; partial for data** | Project code/documentation have an MIT licence, scripts and provenance. CBDB data licensing is not inferred, and large intermediates must be regenerated under official CBDB terms. |

Recommended post-course archival action: create a versioned release in a trusted institutional or generalist repository that supplies a DOI, public README, file manifest, licence fields, and related identifiers. This is an action item, not a claimed current deposit.

## Package and rights controls

- Exclude `database/*.sqlite3`, raw/working SQLite copies, the full feature master, `.venv`, caches, and large source graph intermediates.
- Include `data/raw/latest.json`, `data/raw/download_manifest.json`, the downloader, the verified hashes, environment specifications, frozen split manifest, final source tables, figure snapshots, model metadata/hashes, and tests.
- Include `data/phase3_1/final_model_test_predictions.parquet` only in the review bundle, as required for metric verification.
- Keep `submission/LICENSE`; its final sentence expressly limits MIT coverage to project code and documentation.
- Do not apply an open data licence to the CBDB SQLite or imply that this project grants redistribution rights.

## 中文核对

- 已明确：不重新分发完整 SQLite；读者从 CBDB 官方渠道下载并用官方 SHA256 校验。
- 已明确：代码许可是 MIT，但该许可不覆盖 CBDB 数据。
- 已明确：大型中间特征矩阵不进入论文包，可由脚本从校验后的官方版本重建。
- 已明确：最终数值、图表输入、冻结 split、模型 hash、环境和预测文件在相应 submission/review 包中可复核。
- 尚未声称：不存在的 DOI、登录号、公共仓库记录或 CBDB 数据许可。
- 后续若正式投稿，应在可信仓库建立版本化记录和 DOI，并复核当时有效的 CBDB 官方使用条款。
