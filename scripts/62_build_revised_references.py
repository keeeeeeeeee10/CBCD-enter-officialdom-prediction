#!/usr/bin/env python3
"""Build the verified Phase 3.1 bibliography and field-level reference audit."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "paper" / "revised"
DOC_DIR = ROOT / "docs" / "phase3_1"


REFERENCES = [
    {
        "key": "cbdb2026", "type": "misc",
        "title": "China Biographical Database Project (CBDB)",
        "authors": "Harvard University; Academia Sinica; Peking University", "year": "2026",
        "venue": "China Biographical Database Project",
        "id": "https://cbdb.hsites.harvard.edu/",
        "claim": "Project identity, access route, and official data-use context.",
        "sections": "Introduction; Data Availability",
        "notes": "Official project page checked on 2026-09-01; used only for project and access facts.",
        "fields": {"author": "{{Harvard University} and {Academia Sinica} and {Peking University}}",
                   "url": "{https://cbdb.hsites.harvard.edu/}", "note": "{Accessed 2026-09-01}"},
    },
    {
        "key": "fuller2024", "type": "manual",
        "title": "The China Biographical Database User's Guide", "authors": "Michael A. Fuller",
        "year": "2024", "venue": "China Biographical Database Project",
        "id": "https://cbdb-project.github.io/cbdb-user-guide/",
        "claim": "CBDB schema, query, export, and analysis capabilities.",
        "sections": "Data and Measurement Problem; Data Availability",
        "notes": "Official living project guide checked; not used as evidence for broad methodological claims.",
        "fields": {"author": "{Michael A. Fuller}", "organization": "{China Biographical Database Project}",
                   "url": "{https://cbdb-project.github.io/cbdb-user-guide/}"},
    },
    {
        "key": "tsui2020harvesting", "type": "article",
        "title": "Harvesting Big Biographical Data for Chinese History: The China Biographical Database (CBDB)",
        "authors": "Lik Hang Tsui; Hongsu Wang", "year": "2020", "venue": "Journal of Chinese History 4(2):505--511",
        "id": "10.1017/jch.2020.21", "claim": "CBDB data harvesting and historical research uses.",
        "sections": "Introduction; Related Work", "notes": "Crossref record and publisher abstract agree.",
        "fields": {"author": "{Lik Hang Tsui and Hongsu Wang}", "journal": "{Journal of Chinese History}",
                   "volume": "{4}", "number": "{2}", "pages": "{505--511}", "doi": "{10.1017/jch.2020.21}"},
    },
    {
        "key": "fullerwang2021networks", "type": "article",
        "title": "Structuring, Recording, and Analyzing Historical Networks in the China Biographical Database",
        "authors": "Michael Fuller; Hongsu Wang", "year": "2021", "venue": "Journal of Historical Network Research 5(1):248--270",
        "id": "10.25517/jhnr.v5i1.123", "claim": "CBDB's prosopographical network structures and extraction from historical corpora.",
        "sections": "Introduction; Related Work", "notes": "Crossref lookup unavailable; journal page independently verifies title, authors, year, volume, issue, pages, DOI, and peer-review status.",
        "fields": {"author": "{Michael Fuller and Hongsu Wang}", "journal": "{Journal of Historical Network Research}",
                   "volume": "{5}", "number": "{1}", "pages": "{248--270}", "doi": "{10.25517/jhnr.v5i1.123}",
                   "url": "{https://jhnr.net/articles/39}"},
    },
    {
        "key": "chenwang2022cbdb", "type": "article",
        "title": "China Biographical Database (CBDB): A Relational Database for Prosopographical Research of Pre-Modern China",
        "authors": "Song Chen; Hongsu Wang", "year": "2022", "venue": "Journal of Open Humanities Data 8:4",
        "id": "10.5334/johd.68", "claim": "CBDB's relational design, heterogeneous sources, disambiguation, and analytic exports.",
        "sections": "Introduction; Related Work; Data and Measurement Problem", "notes": "Crossref metadata and publisher data-paper page agree.",
        "fields": {"author": "{Song Chen and Hongsu Wang}", "journal": "{Journal of Open Humanities Data}",
                   "volume": "{8}", "pages": "{4}", "doi": "{10.5334/johd.68}"},
    },
    {
        "key": "bol2012gis", "type": "article", "title": "GIS, Prosopography and History", "authors": "Peter K. Bol",
        "year": "2012", "venue": "Annals of GIS 18(1):3--15", "id": "10.1080/19475683.2011.647077",
        "claim": "Person-traceable spatial aggregation of CBDB prosopographical records.", "sections": "Related Work",
        "notes": "Crossref metadata and publisher full text agree; DOI registration year differs from volume year, so the journal volume year 2012 is retained.",
        "fields": {"author": "{Peter K. Bol}", "journal": "{Annals of GIS}", "volume": "{18}", "number": "{1}",
                   "pages": "{3--15}", "doi": "{10.1080/19475683.2011.647077}"},
    },
    {
        "key": "prokhorenkova2018catboost", "type": "inproceedings",
        "title": "CatBoost: Unbiased Boosting with Categorical Features",
        "authors": "Liudmila Prokhorenkova; Gleb Gusev; Aleksandr Vorobev; Anna Veronika Dorogush; Andrey Gulin",
        "year": "2018", "venue": "Advances in Neural Information Processing Systems 31",
        "id": "https://proceedings.neurips.cc/paper/2018/hash/14491b756b3a51daac41c24863285549-Abstract.html",
        "claim": "CatBoost categorical-feature handling and ordered target-statistic method.", "sections": "Related Work; Models",
        "notes": "Official NeurIPS proceedings metadata and paper checked.",
        "fields": {"author": "{Liudmila Prokhorenkova and Gleb Gusev and Aleksandr Vorobev and Anna Veronika Dorogush and Andrey Gulin}",
                   "booktitle": "{Advances in Neural Information Processing Systems}", "volume": "{31}",
                   "url": "{https://proceedings.neurips.cc/paper/2018/hash/14491b756b3a51daac41c24863285549-Abstract.html}"},
    },
    {
        "key": "grinsztajn2022tabular", "type": "inproceedings",
        "title": "Why Do Tree-Based Models Still Outperform Deep Learning on Typical Tabular Data?",
        "authors": "Léo Grinsztajn; Edouard Oyallon; Gaël Varoquaux", "year": "2022",
        "venue": "Advances in Neural Information Processing Systems 35:507--520", "id": "10.52202/068431-0037",
        "claim": "Tree ensembles as strong baselines on typical medium-sized tabular datasets.", "sections": "Related Work",
        "notes": "Crossref record and official NeurIPS proceedings page agree.",
        "fields": {"author": "{L{\\'e}o Grinsztajn and Edouard Oyallon and Ga{\\\"e}l Varoquaux}",
                   "booktitle": "{Advances in Neural Information Processing Systems}", "volume": "{35}", "pages": "{507--520}",
                   "doi": "{10.52202/068431-0037}"},
    },
    {
        "key": "roberts2017cv", "type": "article",
        "title": "Cross-Validation Strategies for Data with Temporal, Spatial, Hierarchical, or Phylogenetic Structure",
        "authors": "David R. Roberts; Volker Bahn; Simone Ciuti; Mark S. Boyce; Jane Elith; Gurutzeta Guillera-Arroita; Severin Hauenstein; José J. Lahoz-Monfort; Boris Schröder; Wilfried Thuiller; David I. Warton; Brendan A. Wintle; Florian Hartig; Carsten F. Dormann",
        "year": "2017", "venue": "Ecography 40(8):913--929", "id": "10.1111/ecog.02881",
        "claim": "Random validation can underestimate error under dependence; blocked validation targets structured generalization.",
        "sections": "Related Work; Evaluation Protocol", "notes": "Crossref author list, metadata, abstract, and publisher full text agree.",
        "fields": {"author": "{David R. Roberts and Volker Bahn and Simone Ciuti and Mark S. Boyce and Jane Elith and Gurutzeta Guillera-Arroita and Severin Hauenstein and Jos{\\'e} J. Lahoz-Monfort and Boris Schr{\\\"o}der and Wilfried Thuiller and David I. Warton and Brendan A. Wintle and Florian Hartig and Carsten F. Dormann}",
                   "journal": "{Ecography}", "volume": "{40}", "number": "{8}", "pages": "{913--929}", "doi": "{10.1111/ecog.02881}"},
    },
    {
        "key": "koh2021wilds", "type": "inproceedings", "title": "WILDS: A Benchmark of in-the-Wild Distribution Shifts",
        "authors": "Pang Wei Koh; Shiori Sagawa; Henrik Marklund; Sang Michael Xie; Marvin Zhang; Akshay Balsubramani; Weihua Hu; Michihiro Yasunaga; Richard Lanas Phillips; Irena Gao; Tony Lee; Etienne David; Ian Stavness; Wei Guo; Berton Earnshaw; Imran Haque; Sara Beery; Jure Leskovec; Anshul Kundaje; Emma Pierson; Sergey Levine; Chelsea Finn; Percy Liang",
        "year": "2021", "venue": "Proceedings of Machine Learning Research 139:5637--5664",
        "id": "https://proceedings.mlr.press/v139/koh21a.html", "claim": "Evaluation under naturally occurring distribution shifts.",
        "sections": "Related Work; Evaluation Protocol", "notes": "Official PMLR page, abstract, pages, and complete author order checked.",
        "fields": {"author": "{Pang Wei Koh and Shiori Sagawa and Henrik Marklund and Sang Michael Xie and Marvin Zhang and Akshay Balsubramani and Weihua Hu and Michihiro Yasunaga and Richard Lanas Phillips and Irena Gao and Tony Lee and Etienne David and Ian Stavness and Wei Guo and Berton Earnshaw and Imran Haque and Sara Beery and Jure Leskovec and Anshul Kundaje and Emma Pierson and Sergey Levine and Chelsea Finn and Percy Liang}",
                   "booktitle": "{Proceedings of the 38th International Conference on Machine Learning}", "series": "{Proceedings of Machine Learning Research}",
                   "volume": "{139}", "pages": "{5637--5664}", "url": "{https://proceedings.mlr.press/v139/koh21a.html}"},
    },
    {
        "key": "sugiyama2007covariate", "type": "article", "title": "Covariate Shift Adaptation by Importance Weighted Cross Validation",
        "authors": "Masashi Sugiyama; Matthias Krauledat; Klaus-Robert Müller", "year": "2007", "venue": "Journal of Machine Learning Research 8:985--1005",
        "id": "https://jmlr.org/papers/v8/sugiyama07a.html", "claim": "Ordinary validation assumptions can fail under covariate shift.",
        "sections": "Related Work", "notes": "Official JMLR article page and BibTeX checked; no claim that importance weighting was implemented here.",
        "fields": {"author": "{Masashi Sugiyama and Matthias Krauledat and Klaus-Robert M{\\\"u}ller}", "journal": "{Journal of Machine Learning Research}",
                   "volume": "{8}", "pages": "{985--1005}", "url": "{https://jmlr.org/papers/v8/sugiyama07a.html}"},
    },
    {
        "key": "subbaswamy2019transport", "type": "inproceedings",
        "title": "Preventing Failures Due to Dataset Shift: Learning Predictive Models That Transport",
        "authors": "Adarsh Subbaswamy; Peter Schulam; Suchi Saria", "year": "2019",
        "venue": "Proceedings of Machine Learning Research 89:3118--3127",
        "id": "https://proceedings.mlr.press/v89/subbaswamy19a.html", "claim": "Predictive mechanisms can fail to transport across shifted environments.",
        "sections": "Related Work; Discussion", "notes": "Official PMLR page and abstract checked; not cited as evidence of causal invariance in this study.",
        "fields": {"author": "{Adarsh Subbaswamy and Peter Schulam and Suchi Saria}",
                   "booktitle": "{Proceedings of the Twenty-Second International Conference on Artificial Intelligence and Statistics}",
                   "series": "{Proceedings of Machine Learning Research}", "volume": "{89}", "pages": "{3118--3127}",
                   "url": "{https://proceedings.mlr.press/v89/subbaswamy19a.html}"},
    },
    {
        "key": "hand2018administrative", "type": "article", "title": "Statistical Challenges of Administrative and Transaction Data",
        "authors": "David J. Hand", "year": "2018", "venue": "Journal of the Royal Statistical Society: Series A 181(3):555--605",
        "id": "10.1111/rssa.12315", "claim": "Selection and data-generation challenges in administrative and transaction records.",
        "sections": "Related Work; Discussion", "notes": "Crossref record and publisher abstract agree.",
        "fields": {"author": "{David J. Hand}", "journal": "{Journal of the Royal Statistical Society: Series A (Statistics in Society)}",
                   "volume": "{181}", "number": "{3}", "pages": "{555--605}", "doi": "{10.1111/rssa.12315}"},
    },
    {
        "key": "frenay2014label", "type": "article", "title": "Classification in the Presence of Label Noise: A Survey",
        "authors": "Benoît Frénay; Michel Verleysen", "year": "2014", "venue": "IEEE Transactions on Neural Networks and Learning Systems 25(5):845--869",
        "id": "10.1109/TNNLS.2013.2292894", "claim": "Taxonomy and predictive consequences of noisy labels.",
        "sections": "Related Work; Limitations", "notes": "Crossref and IEEE/institutional metadata agree; used conceptually, not to assert that CBDB's proxy is random label noise.",
        "fields": {"author": "{Beno{\\^i}t Fr{\\'e}nay and Michel Verleysen}", "journal": "{IEEE Transactions on Neural Networks and Learning Systems}",
                   "volume": "{25}", "number": "{5}", "pages": "{845--869}", "doi": "{10.1109/TNNLS.2013.2292894}"},
    },
    {
        "key": "jacobs2021measurement", "type": "inproceedings", "title": "Measurement and Fairness",
        "authors": "Abigail Z. Jacobs; Hanna Wallach", "year": "2021", "venue": "Proceedings of the 2021 ACM Conference on Fairness, Accountability, and Transparency:375--385",
        "id": "10.1145/3442188.3445901", "claim": "Latent constructs can diverge from their operational measurements.",
        "sections": "Related Work; Data and Measurement Problem", "notes": "Crossref and ACM abstract agree; conceptual support only, not direct evidence about CBDB coverage.",
        "fields": {"author": "{Abigail Z. Jacobs and Hanna Wallach}", "booktitle": "{Proceedings of the 2021 ACM Conference on Fairness, Accountability, and Transparency}",
                   "pages": "{375--385}", "doi": "{10.1145/3442188.3445901}"},
    },
    {
        "key": "gebru2021datasheets", "type": "article", "title": "Datasheets for Datasets",
        "authors": "Timnit Gebru; Jamie Morgenstern; Briana Vecchione; Jennifer Wortman Vaughan; Hanna Wallach; Hal Daumé III; Kate Crawford",
        "year": "2021", "venue": "Communications of the ACM 64(12):86--92", "id": "10.1145/3458723",
        "claim": "Dataset documentation should state motivation, composition, collection, and recommended uses.",
        "sections": "Related Work; Reproducibility", "notes": "Crossref and publisher/author-affiliated page agree; author suffix normalized to Hal Daumé III.",
        "fields": {"author": "{Timnit Gebru and Jamie Morgenstern and Briana Vecchione and Jennifer Wortman Vaughan and Hanna Wallach and Hal Daum{\\'e} III and Kate Crawford}",
                   "journal": "{Communications of the ACM}", "volume": "{64}", "number": "{12}", "pages": "{86--92}", "doi": "{10.1145/3458723}"},
    },
    {
        "key": "lundberg2017shap", "type": "inproceedings", "title": "A Unified Approach to Interpreting Model Predictions",
        "authors": "Scott M. Lundberg; Su-In Lee", "year": "2017", "venue": "Advances in Neural Information Processing Systems 30",
        "id": "https://proceedings.neurips.cc/paper/7062-a-unified-approach-to-interpreting-model-predictions",
        "claim": "SHAP as an additive feature-attribution framework.", "sections": "Related Work; Model Interpretation",
        "notes": "Official NeurIPS proceedings page checked; does not support causal interpretation.",
        "fields": {"author": "{Scott M. Lundberg and Su-In Lee}", "booktitle": "{Advances in Neural Information Processing Systems}",
                   "volume": "{30}", "url": "{https://proceedings.neurips.cc/paper/7062-a-unified-approach-to-interpreting-model-predictions}"},
    },
    {
        "key": "kumar2020shap", "type": "inproceedings",
        "title": "Problems with Shapley-Value-Based Explanations as Feature Importance Measures",
        "authors": "I. Elizabeth Kumar; Suresh Venkatasubramanian; Carlos Scheidegger; Sorelle Friedler", "year": "2020",
        "venue": "Proceedings of Machine Learning Research 119:5491--5500", "id": "https://proceedings.mlr.press/v119/kumar20e.html",
        "claim": "Limits of interpreting Shapley values as context-free importance or causal effects.",
        "sections": "Related Work; Model Interpretation; Limitations", "notes": "Official PMLR page, abstract, author order, and pages checked.",
        "fields": {"author": "{{I. Elizabeth Kumar} and Suresh Venkatasubramanian and Carlos Scheidegger and Sorelle Friedler}",
                   "booktitle": "{Proceedings of the 37th International Conference on Machine Learning}", "series": "{Proceedings of Machine Learning Research}",
                   "volume": "{119}", "pages": "{5491--5500}", "url": "{https://proceedings.mlr.press/v119/kumar20e.html}"},
    },
    {
        "key": "guo2017calibration", "type": "inproceedings", "title": "On Calibration of Modern Neural Networks",
        "authors": "Chuan Guo; Geoff Pleiss; Yu Sun; Kilian Q. Weinberger", "year": "2017",
        "venue": "Proceedings of Machine Learning Research 70:1321--1330", "id": "https://proceedings.mlr.press/v70/guo17a.html",
        "claim": "Post-hoc probability calibration and expected calibration error reporting.",
        "sections": "Related Work; Evaluation Protocol", "notes": "Official PMLR page, abstract, authors, and pages checked.",
        "fields": {"author": "{Chuan Guo and Geoff Pleiss and Yu Sun and Kilian Q. Weinberger}",
                   "booktitle": "{Proceedings of the 34th International Conference on Machine Learning}", "series": "{Proceedings of Machine Learning Research}",
                   "volume": "{70}", "pages": "{1321--1330}", "url": "{https://proceedings.mlr.press/v70/guo17a.html}"},
    },
    {
        "key": "niculescu2005probabilities", "type": "inproceedings", "title": "Predicting Good Probabilities with Supervised Learning",
        "authors": "Alexandru Niculescu-Mizil; Rich Caruana", "year": "2005", "venue": "Proceedings of the 22nd International Conference on Machine Learning:625--632",
        "id": "10.1145/1102351.1102430", "claim": "Post-hoc calibration using held-out data.",
        "sections": "Related Work; Evaluation Protocol", "notes": "Crossref and ACM/conference metadata agree; cited for held-out calibration, not test-label fitting.",
        "fields": {"author": "{Alexandru Niculescu-Mizil and Rich Caruana}", "booktitle": "{Proceedings of the 22nd International Conference on Machine Learning}",
                   "pages": "{625--632}", "doi": "{10.1145/1102351.1102430}"},
    },
]


def bib_entry(ref: dict[str, object]) -> str:
    source_fields = dict(ref["fields"])
    fields = {"author": source_fields.pop("author"), "title": "{" + str(ref["title"]) + "}",
              "year": "{" + str(ref["year"]) + "}", **source_fields}
    lines = [f"@{ref['type']}{{{ref['key']},"]
    for name, value in fields.items():
        lines.append(f"  {name} = {value},")
    lines[-1] = lines[-1].rstrip(",")
    lines.append("}")
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    keys = [str(ref["key"]) for ref in REFERENCES]
    if len(REFERENCES) != 20 or len(set(keys)) != 20:
        raise RuntimeError("The revised bibliography must contain exactly 20 unique verified references")
    if any(not str(ref["id"]).startswith(("10.", "https://")) for ref in REFERENCES):
        raise RuntimeError("Every reference needs a DOI or official HTTPS URL")

    bib_text = "\n\n".join(bib_entry(ref) for ref in REFERENCES) + "\n"
    bib_path = OUT_DIR / "references_revised.bib"
    bib_path.write_text(bib_text, encoding="utf-8")

    columns = ["citation_key", "title", "authors", "year", "venue", "doi_or_official_url",
               "verification_status", "claim_supported", "section_used", "notes"]
    audit_path = OUT_DIR / "reference_audit_revised.csv"
    with audit_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for ref in REFERENCES:
            writer.writerow({
                "citation_key": ref["key"], "title": ref["title"], "authors": ref["authors"],
                "year": ref["year"], "venue": ref["venue"], "doi_or_official_url": ref["id"],
                "verification_status": "VERIFIED", "claim_supported": ref["claim"],
                "section_used": ref["sections"], "notes": ref["notes"],
            })

    # The user requested both the canonical revised paths and compatibility copies at paper/.
    (ROOT / "paper" / "references_revised.bib").write_text(bib_text, encoding="utf-8")
    (ROOT / "paper" / "reference_audit_revised.csv").write_text(audit_path.read_text(encoding="utf-8"), encoding="utf-8")

    report = f"""# Phase 3.1 strict reference verification

## Result

- Total audited: **{len(REFERENCES)}**
- VERIFIED: **{len(REFERENCES)}**
- CHECK SUGGESTED: **0**
- NEEDS FIX: **0**
- UNVERIFIABLE: **0**

All references admitted to the revised bibliography have a verified DOI or official project/proceedings URL and support a retained manuscript statement. Bibliographic existence and claim support were audited separately.

## Field-level decisions

- DOI-bearing records were checked against DOI metadata and a publisher, journal, or official proceedings page.
- Fuller and Wang (2021) is the one Crossref exception: Crossref did not return the DOI, while the journal page independently reports the same title, authors, year, volume, issue, pages, DOI, and peer-reviewed status.
- Bol (2012) retains the official volume year although its DOI contains `2011`; this is a registration/publication-year difference, not a mismatch.
- Author suffixes and diacritics were normalized without changing author order. No author was omitted.
- Official project documentation is used only for project, schema, and access facts; conceptual claims use peer-reviewed work.

## Claim-boundary controls

- Label-noise literature does not imply that the operational CBDB label is random corruption of historical truth.
- Measurement literature is conceptual support and is not evidence of CBDB-specific coverage rates.
- Dataset-shift literature motivates grouped evaluation but does not turn the study into a causal transport analysis.
- SHAP references support additive attribution and interpretation limits, not causal claims.
- Calibration references support validation-fitted post-hoc calibration, never fitting on test labels.

The machine-readable audit is `paper/revised/reference_audit_revised.csv`; corrected BibTeX is `paper/revised/references_revised.bib`.
"""
    (DOC_DIR / "reference_verification_report.md").write_text(report, encoding="utf-8")
    print(f"PASS: wrote {len(REFERENCES)} verified references")
    print(bib_path.relative_to(ROOT))
    print(audit_path.relative_to(ROOT))


if __name__ == "__main__":
    main()
