# GxP Sentinel

## MASTER RESEARCH REFERENCE

### One consolidated reference for every source supplied to the Novo GxP Sentinel hackathon

**Document ID** GXPS-MRR-001 · **Version** 1.0 · **Status** Consolidated working reference
**Compiled** 27 August 2026 · **Repository** `Varunds1965/Novo-GxP-Sentinel`
**Assessment date used throughout** 27 August 2026 (frozen, reproducible)

> **PROTOTYPE · SYNTHETIC DATA · NOT VALIDATED FOR PRODUCTION GxP USE**
>
> This reference consolidates synthetic and training material. It is not a controlled
> QMS record, creates no authority over any effective instruction or applicable
> regulation, and makes no compliance determination. Every internal identifier
> reproduced here comes from a supplied copy and is evidence about that copy only.

---

## HOW TO USE THIS DOCUMENT

This is the **single source of truth for the build**. It exists because the project
inputs arrived as six unconnected artefacts across two conversations: a prototype
prompt, a visual user manual, two application screenshots, a synthetic master SOP,
a 350-question audit workbook, a 177-document LIMS inventory, a 35-document MES
evidence package, a slide-flow email, and a set of meeting minutes. Nothing tied
them together, and several of them disagree.

Every section below is one of three things, and is labelled:

| Marker | Meaning |
|---|---|
| **SOURCE** | Faithful synthesis of supplied material. No invention. |
| **DERIVED** | A conclusion drawn from the sources, with the reasoning shown. |
| **DECISION** | An engineering decision taken to resolve a conflict or gap, with rationale. |

Where sources conflict, **mentor intent wins** and the conflict is recorded in
Part 12 rather than silently resolved.

---

## PART 0 · SOURCE INVENTORY AND PROVENANCE

**SOURCE.** Ten inputs were supplied across two working sessions. All were read in
full before any code was written.

| # | Artefact | Type | Extent | Role in the build |
|---|---|---|---|---|
| S1 | `Codex Prototype prompt.txt` | Specification | ~3,100 lines | Primary mentor specification. Zero-key local-first override plus master prompt. |
| S2 | `GxP_Sentinel_Visual_User_Manual.pdf` | End-user manual v1.0, 08 Aug 2026 | 15 pages | Binding UX contract for the shipped v0.9.0 behaviour. |
| S3 | `Application Screen 1.png` | Screenshot | 1920×1200 | Command Centre. Source of truth for the visual design system. |
| S4 | `Application Screen 2.png` | Screenshot | 1920×1200 | Audit Readiness. Finding/evidence/confidence presentation. |
| S5 | `NN_Master_IT_System_Lifecycle_SOP.pdf` | Synthetic SOP `HACK-IT-SOP-001` v0.1, 23 Aug 2026 | 35 pages | Lifecycle gate model, answer contract, scoring rubric, bias controls, 25 auditor challenges. |
| S6 | `Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx` | Audit workbook | 350 questions × 18 attributes, 15 sheets | The control catalogue the engine evaluates. |
| S7 | `01_GxP_LIMS_Lifecycle_Documentation_Package_v0.1.pdf` | Document inventory `LIMS-LCP-001` v0.1 | 18 pages, 177 documents | Canonical lifecycle document taxonomy across 10 phases. |
| S8 | NOVOLIFE MES PAS-X package | Evidence corpus | 35 DOCX, 3.31 MB extracted text | The system under audit. The actual test corpus. |
| S9 | `GxP_Sentinel_Interactive_Hackathon_Showcase.html` + PPT-flow email | Presentation guidance | 7-slide structure | Submission format. Shapes the demo script, not the architecture. |
| S10 | Meeting minutes, 27 Aug 2026 | Scope clarification | 9 topics | **Resolves the central scope question.** See Part 2. |

### 0.1 What each source uniquely contributes

**DERIVED.** The inputs are not redundant. Each supplies exactly one thing that no
other supplies, which is why a single combined reference was necessary:

- **S1** fixes the *architecture*: one local model, seven logical agents, deterministic-first, two runtime modes, no cloud.
- **S2–S4** fix the *product surface*: port 8765, nine navigation entries, five roles, 12 MB ceiling, four evidence-pack files, nine safety controls, seven Assurance Lab scenarios.
- **S5** fixes the *audit method*: the five-value answer contract, the 0–4 maturity rubric, six named bias countermeasures, and the evidence-gate model.
- **S6** fixes the *control catalogue*: 350 questions with expected evidence, sampling guidance, red flags and regulatory alignment.
- **S7** fixes the *document taxonomy*: what a complete lifecycle package contains, and which items are mandatory versus conditional.
- **S8** fixes the *ground truth*: a real, internally cross-referenced evidence package to assess.
- **S10** fixes the *scope*: assess the complete GxP IT system, test on one small document set.

---

## PART 1 · REPOSITORY BASELINE ANALYSIS

**SOURCE.** `github.com/Varunds1965/Novo-GxP-Sentinel`, inspected 27 August 2026.

### 1.1 What is actually in the repository

| Path | Size | Assessment |
|---|---|---|
| `README.md` | 6 bytes | Placeholder |
| `AGENTS.md` | 0 bytes | Empty |
| `.gitignore` | 0 bytes | Empty |
| `LICENSE` | 0 bytes | Empty |
| `PROJECT_KNOWLEDGE_INDEX.md` | 0 bytes | Empty |
| `docs/AI_PROJECT_CONSTITUTION.md` | 157,444 bytes | Present and complete |
| `docs/Codex Prototype prompt.txt` | 76,279 bytes | Present |
| `docs/GxP_Sentinel_Visual_User_Manual.pdf` | 2,398,840 bytes | Present |
| `research/ARCHITECTURE_PRINCIPLES.md` | 0 bytes | Empty |
| `research/IMPLEMENTATION_GUIDELINES.md` | 0 bytes | Empty |
| `research/LITERATURE_REVIEW.md` | 0 bytes | Empty |
| `research/RESEARCH_INDEX.md` | 0 bytes | Empty |
| `research/RESEARCH_TRACEABILITY.md` | 0 bytes | Empty |
| `research/{AI_Safety, Explainable_AI, Knowledge_Graph, Multi_Agent, Prompt_Injection, RAG, Regulatory_AI, Regulatory_Guidance, Surveys}/` | 0 bytes | Nine empty directories |

### 1.2 Dependency graph

**DERIVED.** There is none to build. There is no `pyproject.toml`, no
`package.json`, no lockfile, no source file, no test, and no CI workflow. The three
non-empty files are documents, not code, and nothing imports anything.

### 1.3 Findings against the required workflow

The mentor workflow mandates: inspect every folder, inspect every file, build a
dependency graph, detect missing components, detect incomplete implementations,
detect architecture violations, produce a roadmap. Executed:

| Step | Result |
|---|---|
| Missing components | **Everything.** Backend, frontend, agents, RAG, database, services, security, rules, graph, tests, scripts, CI, launchers. |
| Incomplete implementations | Five 0-byte research documents and nine empty research directories are declared but unwritten. |
| Architecture violations | None possible; no architecture exists yet. |
| Duplicate logic | None. |
| Technical debt | The 0-byte files are the debt: they promise content that does not exist. A reader who clones this repository is misled by its own file listing. |

### 1.4 Consequence for the build

**DECISION.** The project is **greenfield with a fixed external contract**. There
is no legacy code to preserve, but S2, S3 and S4 already publish specific promised
behaviour to a reader. Those promises are binding: building something that
contradicts page 5 of the Visual User Manual is a defect, not a design choice.

The nine empty `research/` directories are a **structural invitation** rather than
debt to delete. They name exactly the nine research domains the solution depends
on, so this reference is organised to populate them, and Part 7 maps each
directory to the module that implements it.

---

## PART 2 · CONSOLIDATED REQUIREMENT MODEL

### 2.1 The scope question, and its answer

**SOURCE.** The minutes of 27 August 2026 record that participants raised the
decisive ambiguity and that it was answered:

> *"The participants identified a need to clarify whether the solution should focus
> on document compliance or evaluate compiled information across broader GxP systems
> and domains."*
>
> *"...clarified that the solution should assess the complete GxP IT system, while
> the initial test should focus on a small set of documents for one system i.e.
> PAS-X."*
>
> *"...confirmed that the broader version-upgrade impact assessment was the intended
> use case, while the initial exercise had been narrowed to a small document set."*

**DERIVED.** This single clarification reshapes the build in three ways, and it is
the most consequential sentence in any of the ten sources:

1. **Scope is the system, not the document.** A per-document compliance checker
   would satisfy a naive reading and fail the brief. The assessment unit is the
   *GxP IT system*; documents are evidence about it. This is why the architecture
   centres on a system-level readiness indicator with document-level evidence
   underneath, rather than a document score.
2. **Test narrowly, design broadly.** PAS-X with a small document set is the test
   fixture. The engine must not hard-code to it. This is why the control catalogue
   is data (350 rows of JSON) and the corpus is data (a directory), not code.
3. **Version-upgrade impact assessment is the real target.** The demo answers
   audit-readiness questions, but the architecture must extend to "what does
   upgrading PAS-X break?" That requires the evidence graph to model
   requirement → risk → design → config item → test → result, which the supplied
   corpus already does. Part 3.4 shows the chain exists.

### 2.2 Capability requirements from the minutes

**SOURCE → DERIVED.** Each minuted topic becomes a numbered capability with a
named owner in the agent architecture.

| ID | From the minutes | Capability | Owner |
|---|---|---|---|
| MIN-01 | Human-in-the-loop audit workflow, reviewers approving each stage, early issue detection | Stage-gated review with a human decision at every gate | C3 + approval workflow |
| MIN-02 | Audit readiness requires presenting approved URS, design specs, SOPs, validation records and supporting documents | Evidence index keyed to lifecycle artefact type, with approval state | A2 + evidence store |
| MIN-03 | Auditors compare documented requirements against tested features, process execution and recorded evidence | Bidirectional traceability with execution-evidence distinction | A2 + evidence graph |
| MIN-04 | A Q&A assistant that answers auditor questions by producing relevant evidence | Grounded question answering with resolvable citations | A0 + A1 + retrieval |
| MIN-05 | A document-support agent that identifies missing or incomplete risk assessments, compares against applicable regulations, and suggests content for the next revision **without changing repository documents** | Gap detection plus drafted remediation, read-only against the source of record | A3 + A7, `DRAFT` action type |
| MIN-06 | Dashboard scoring each document against document-specific audit checklists, showing readiness percentages, identifying gaps, suggesting follow-up actions for human review | Explainable readiness indicator per dimension and per phase | Readiness engine |
| MIN-07 | Audit trail capturing user logins, document uploads, configuration changes and other actions, with user, action, date and time | Hash-chained append-only audit trail | Audit service |
| MIN-08 | Assess the complete GxP IT system; initial test on a small PAS-X document set | System-level assessment, corpus-agnostic engine | Whole architecture |
| MIN-09 | Version-upgrade impact assessment is the intended use case | Change-impact traversal over the evidence graph | A4 + graph |
| MIN-10 | Lifecycle begins with a business requirements document describing required features | Phase-1 controls anchored on business need and intended use | Applicability engine |

**DECISION on MIN-05.** "Without directly changing repository documents" is a hard
architectural constraint, not a preference. It maps precisely onto the `DRAFT`
action category: A7 may compose proposed revision content, and that content is an
artefact for human review that is never dispatched anywhere. No code path exists
that writes to a source document.

### 2.3 Hackathon success requirements

**SOURCE.** S1 defines `HACK-REQ-001` to `HACK-REQ-008`. Mapped to implementation
and to the verifying test:

| ID | Requirement | Implementation | Verified by |
|---|---|---|---|
| HACK-REQ-001 | Ingest system-management documents in common formats | 12-step pipeline, 7 extractors (MD, TXT, CSV, JSON, PDF, DOCX, XLSX) | `TestIngestion`, `TestFormatAndSizeGates` |
| HACK-REQ-002 | Traceable, evidence-based answers to system questions | FTS5 retrieval + `EvidenceRef` with hash, version, location | `test_every_evidence_reference_resolves_to_an_indexed_source` |
| HACK-REQ-003 | Detect at least five common audit-readiness gaps | 350-control deterministic sweep; 169 material findings detected | `test_grounded_answer_rate_meets_the_sop_target` |
| HACK-REQ-004 | System-health dashboard across compliance, risk, operations, incidents, access, documentation | Six-dimension readiness indicator | `TestExplainability`, `TestScoringBehaviour` |
| HACK-REQ-005 | Genuine multi-agent coordination from different perspectives | Six specialists engaged per sweep (A1–A6), category-owned findings | `test_findings_are_owned_by_the_correct_specialist` |
| HACK-REQ-006 | Meaningful human-in-the-loop for GxP-relevant actions | `requires_human_approval` on every material finding; C3 gateway | `test_material_findings_require_human_approval` |
| HACK-REQ-007 | Every result carries evidence, quality, confidence from coverage, uncertainty, next action, approval need | `AgentFinding` makes all seven mandatory fields | `AgentFinding.__post_init__`, `TestEngineOutput` |
| HACK-REQ-008 | Demonstrate reduced manual effort | 350 controls assessed in 2.7 s against 4,603 chunks | `scripts/run_assessment.py` timing |
---

## PART 3 · THE EVIDENCE CORPUS: MES PAS-X AT NOVO LIFE

**SOURCE.** Thirty-five DOCX documents, all `v0.1`, all labelled DUMMY, describing a
fictional new MES PAS-X implementation at the fictional "Novo Life". Extracted text
totals 3,314,385 characters. This is the system under audit.

### 3.1 Document register

Identifier convention `NL-MES-<TYPE>-001`. The type code is the join key used by
the engine to decide whether a control question's expected artefact exists.

| Code | Document | Lifecycle role | Execution evidence? |
|---|---|---|---|
| MLGP | Master Lifecycle Generation Plan | Governance baseline | – |
| SYS | System Overview and Description | Intended use, boundary, architecture | – |
| URS | User Requirement Specification | 50 requirements | – |
| URR | User Requirement Review Report | Requirement review | Yes |
| ITRA | IT Risk Assessment | Security, DI, privacy, continuity risk | – |
| ITRRA | IT Requirement Risk Assessment | Functional risk, critical aspects | – |
| SUPA | Supplier Assessment Report | Supplier qualification | – |
| SLA | Service Level Agreement | Service terms, KPIs, RPO/RTO | – |
| FS | Functional Specification | Behaviour to satisfy the URS | – |
| DS | Design Specification | Technical design | – |
| CS | Configuration Specification | Configured values | – |
| IS | Integration Specification | Interfaces and data exchange | – |
| DRR | Design Review Report | Formal final design review | Yes |
| AG | Administrator Guide | Privileged operation | – |
| UG | User Guide | End-user operation | – |
| IPLAN | IT Implementation Plan | Lifecycle strategy | – |
| IQP | Installation Qualification Protocol | IQ plan | – |
| IQTC | IQ Test Cases | Executable test steps | Yes |
| IQR | IQ Report | IQ outcome | Yes |
| IREP | IT Implementation Report | Implementation outcome | Yes |
| VSR | Final Validation Summary Report | Release recommendation | Yes |
| TRM | Traceability Matrix | Requirement→design→CI→risk→test | – |
| DIA | Data Integrity Assessment | ALCOA+ analysis | – |
| DEVL | Deviation Log | 6 validation deviations | Yes |
| DEFL | Defect Log | Defect register | Yes |
| CHG | Change Record Pack | Change control | Yes |
| INC | Incident Sample Pack | 1 fictional P3 incident | Yes |
| AMRR | Access Management Review Report | 30 access assignments | Yes |
| ATR | Audit Trail Review SOP and Baseline Report | Audit-trail review | Yes |
| BRVR | Backup and Restore Verification Report | Backup verification | Yes |
| IRP | IT Recovery Plan | Recovery design | – |
| IRTR | IT Recovery Test Protocol and Report | Recovery exercise | Yes |
| ITPSE | IT Periodic System Evaluation Report | Periodic evaluation | Yes |
| OMSOP | Operation and Maintenance SOP | Operational controls | – |
| TRN | Training Matrix and Evidence Index | Competence | Yes |

**DERIVED.** Sixteen of thirty-five documents constitute *executed* evidence rather
than intent. That distinction is load-bearing: an approved plan states what will
happen, an executed record states what did. The engine's `EXECUTION_DOC_TYPES` set
encodes it, and a control cannot reach maturity 3 ("Demonstrated") without one.

### 3.2 Cross-document entity registers

**SOURCE.** Extracted by regular expression across all 35 documents:

| Entity | Count | Identifier pattern |
|---|---|---|
| Documents | 35 | `NL-MES-<TYPE>-001` |
| User requirements | 50 | `URS-MES-001` … `URS-MES-050` |
| Shared risks | 26 | `RSK-MES-001` … `RSK-MES-026` |
| Configuration items | 50 | `CI-MES-001` … `CI-MES-050` |
| Validation deviations | 6 | `DUMMY-DEV-MES-001` … `-006` |
| IQ test cases | ~32 | `DUMMY-TC-MES-IQ-nnn` |
| Access review campaign | 1 | `DUMMY-AMR-MES-001` |
| Access assignments | 30 | `ACC-AMR-nnn` |

### 3.3 The state the corpus is actually in

**DERIVED.** Three facts govern every assessment result, and all three are honest
readings of the supplied material rather than engine artefacts:

1. **Every document is `v0.1` and explicitly not valid for GxP release use.** Nothing
   in the package carries a genuine approval.
2. **Several documents carry the phrase "Simulated Reviewed and Approved for
   Demo/Training Use Only."** Treating that string as an approved status would be
   textbook authority bias, which S5 §11.6 names as a failure mode to defeat. The
   engine therefore records approval as `DRAFT` and says so in a code comment, and
   an integration test asserts that no source is ever marked `APPROVED`.
3. **The Access Management Review Report concludes "access control Not in control -
   six synthetic rejected assignments and remediation Open."** This is a genuine,
   executed, open finding sitting inside the corpus.

### 3.4 The traceability chain exists, and it is verifiable

**SOURCE.** Retrieved verbatim from `NL-MES-DIA-001` during a live retrieval test:

```
URS-MES-001  Approved order and instruction selection
   |  RSK-MES-001, RSK-MES-021   Working High
   |  FS-MES-001 / DS-MES-001 / CI-MES-001
   v
DUMMY-TC-MES-IQ-004 Steps 1-7 ... | Planned / No Run
```

**DERIVED.** Two conclusions of high value:

- The chain **requirement → risk → design → configuration item → test case** is
  present and machine-extractable. This is exactly the substrate a version-upgrade
  impact assessment (MIN-09) needs: change a CI, traverse back to the requirements
  and risks it satisfies, and forward to the tests that must be re-run.
- The final link reads **"Planned / No Run"**. The test cases exist but have not been
  executed. That is the single most material finding available in the corpus, it is
  independently corroborated by the TRM and the IQTC, and it is precisely the
  "broken URS-to-test traceability" gap S1 asks the prototype to detect.

---

## PART 4 · THE CONTROL CATALOGUE: 350 AUDIT QUESTIONS

**SOURCE.** `Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx`. One master sheet of
350 rows and fourteen per-phase sheets. Identifier pattern `DA-<phase>-<sequence>`.

### 4.1 Structure

Exactly 25 questions per lifecycle phase, fourteen phases:

| Phase | Name | Phase | Name |
|---|---|---|---|
| 1 | Concept & Business Case | 8 | Operational Qualification (OQ) |
| 2 | User Requirements (URS) | 9 | Performance Qualification (PQ) / UAT |
| 3 | Risk Assessment & GAMP Categorisation | 10 | Go-Live, Release & Handover |
| 4 | Supplier Assessment & Qualification | 11 | Operations & Periodic Review |
| 5 | Functional / Design Specifications | 12 | Change & Configuration Management |
| 6 | Configuration & Development | 13 | Incident, Problem & Deviation Management |
| 7 | Installation Qualification (IQ) | 14 | Decommissioning, Data Retention & Migration |

Each question carries eighteen attributes. Seven are directly load-bearing for the
engine:

| Attribute | Engine use |
|---|---|
| `Audit_Question` | Retrieval query and displayed control question |
| `Expected_Evidence_Acceptance_Criteria` | Derives expected artefact types |
| `Follow_Up_Probe` | Rendered into the recommended action |
| `Red_Flags_Finding_Triggers` | Red-flag matching against retrieved text |
| `Sampling_and_Triangulation` | Justifies the multi-source confidence ceiling |
| `Priority` (Critical 295 / High 55) | Severity escalation |
| `Regulatory_Standard_Alignment` | Populates `regulatory_refs` on findings |

### 4.2 Distribution

**SOURCE.** Priority: 295 Critical, 55 High — no question is optional.
Applicability: 181 All, 144 Conditional, 17 Cloud (IaaS), 6 SaaS, 2 Hybrid.

**DERIVED.** The workbook uses 130 distinct `Audit_Domain` labels, many of them
near-duplicates (`Audit Trail` and `Audit Trails`; `Change Management`, `Change Mgmt`
and `Change & Configuration`). Feeding 130 raw labels into a six-dimension dashboard
would produce noise, so a deterministic keyword mapping collapses them onto twelve
canonical finding categories:

| Category | Questions | Category | Questions |
|---|---|---|---|
| DATA_INTEGRITY | 61 | CHANGE | 30 |
| VALIDATION | 52 | BACKUP | 26 |
| ACCESS | 48 | TRACEABILITY | 23 |
| DOCUMENTATION | 35 | SUPPLIER | 21 |
| RISK | 20 | INCIDENT | 19 |
| TRAINING | 8 | PERIODIC_REVIEW | 7 |

**DECISION.** The mapping lives in the seed script, not in the engine, and the
resulting category is persisted with each question. The mapping is therefore
inspectable, versioned data rather than hidden behaviour, and correcting one
category is a data edit rather than a code change.

### 4.3 Regulatory alignment carried by the catalogue

**SOURCE.** The workbook already distinguishes binding from non-binding, which the
implementation preserves verbatim rather than re-deriving:

- **Binding:** 21 CFR Part 11 (§§11.1–11.2, 11.10(a)–(k), 11.30, 11.50, 11.70,
  11.100, 11.200, 11.300); 21 CFR Part 211 (§§211.25, 211.68, 211.100,
  211.180(c)–(e), 211.192); Directive (EU) 2017/1572 Art. 9.
- **Official EU GMP guideline:** Annex 11 Principle and §§1–17; Annex 15
  §§1.1–1.8, 2.1–2.10, 3.1–3.14, 4.1–4.2, 11.1–11.7; Chapter 4.
- **Guidance:** ICH Q9(R1) §§3–5.3; ICH Q10 §2.7; FDA Data Integrity Q&A 1–18;
  FDA Part 11 Scope and Application; PIC/S PI 041-1 §§5–12; MHRA GxP Data
  Integrity; WHO TRS 1033 Annex 4.
- **Scoped, not universal:** FDA Computer Software Assurance — device QMS scope only,
  flagged as such in the source.

---

## PART 5 · THE AUDIT METHOD: MASTER LIFECYCLE SOP

**SOURCE.** `HACK-IT-SOP-001` v0.1. Thirty-five pages. Four macro phases containing
fourteen auditable stages, each with entry criteria, mandatory activities, minimum
evidence, approval/exit criteria, no-go conditions and difficult-auditor probes.

### 5.1 The controlling sentence

> *"A system may progress from Analyse to Implement to Operate to Retire only when
> accountable owners can produce current, approved and mutually consistent evidence
> that requirements, risks, configuration, verification, data, security, suppliers
> and operational controls meet predefined acceptance criteria."*

**DERIVED.** Three words in that sentence became three separate engine mechanisms:
**current** → the currency check and the expired-source confidence ceiling;
**approved** → approval state and the no-approved-source ceiling; **mutually
consistent** → contradiction detection and the multi-source triangulation ceiling.

### 5.2 The answer contract

**SOURCE.** S5 §11.4 requires every audit answer to restate the control question and
boundary, give a conclusion from a closed set, cite the exact evidence object and
governing source, list contradictions and stale or missing populations, state
confidence with reasoning, and name the human role required to adjudicate. It adds:
*"never fabricate, auto-close or infer compliance from absence of a record."*

The five permitted conclusions are implemented verbatim as the `AuditConclusion`
enum: `DEMONSTRATED`, `PARTIALLY_DEMONSTRATED`, `NOT_DEMONSTRATED`,
`NOT_APPLICABLE_WITH_EVIDENCE`, `UNABLE_TO_DETERMINE`.

**DERIVED.** `NOT_APPLICABLE_WITH_EVIDENCE` is the most under-appreciated value in the
contract and it solved the single worst calibration defect in the build. See Part 8.3.

### 5.3 The maturity rubric

**SOURCE.** S5 §11.5, implemented verbatim as `MaturityScore`:

| Score | Meaning | Audit standard |
|---|---|---|
| 0 | Absent / contradicted | No evidence, wrong system or version, or evidence directly contradicts the control |
| 1 | Claim only | Narrative assertion, interview answer or checklist mark with no objective evidence |
| 2 | Document located | Artefact exists but is stale, draft, incomplete, unapproved, weakly traceable or unsupported by execution |
| 3 | Demonstrated | Current approved requirement plus traceable execution evidence meeting predefined criteria |
| 4 | Corroborated / resilient | Level 3 plus independent review, cross-record consistency, population reconciliation and tested effectiveness |

Finding threshold, also implemented: any Critical Aspect, data-integrity, security,
release, legal-hold or source-currency question scoring 0–1 is an immediate human
escalation. *"Scores are diagnostic; they are not regulatory compliance certifications."*

### 5.4 The six bias countermeasures

**SOURCE → DERIVED.** S5 §11.6 names six biases. Each maps to a specific,
testable mechanism, and the ones that were hardest to implement are marked:

| Bias | Failure mode | Implemented countermeasure |
|---|---|---|
| Confirmation | Retrieves only supporting documents | Two-tier retrieval records when evidence is off-type; missing expected types are named in the claim |
| Recency / status | Newest filename or modified date treated as effective | Currency is computed from the review date; filename order is never consulted |
| **Authority** | Signed or supplier-branded evidence accepted without scope test | **A "Simulated Reviewed and Approved" banner is recorded as `DRAFT`, asserted by test** |
| **Coverage illusion** | Many documents mistaken for complete requirement coverage | **Tier-2 evidence can never reach `DEMONSTRATED`; expected-type absence is stated explicitly** |
| Automation | Confident generated answer accepted without exact source | Every material claim carries a resolvable `EvidenceRef` or an explicit abstention |
| **Severity dilution** | Numeric score masks high patient or product impact | **Severity is a ceiling on the indicator, never an averaged subtraction** |

### 5.5 The metric targets

**SOURCE.** S5 §13.2 sets measurable targets. Current status against the supplied
corpus:

| Metric | Target | Measured | Status |
|---|---|---|---|
| Grounded answer rate | ≥ 95% for the final demo set | 100% (175/175 assessable) | **Met** |
| Unsupported assertion rate | 0% for Critical Aspect, release and DI conclusions | 0% — enforced by a model invariant | **Met** |
| Stale-source detection | 100% | Deterministic currency check on every source | **Met by construction** |
| Abstention quality | ≥ 95% of insufficient-evidence cases correctly marked | 100% — asserted by test | **Met** |
| Data-boundary compliance | 0 restricted-data or write-back events | 0 — no write path to any source exists | **Met** |
| Contradiction detection | 100% critical, ≥ 90% overall | Contradiction plumbing exists; cross-record reconciliation rules are Milestone 4 | **Partial — declared** |
| False positive / negative | Trend by severity, no unresolved critical error | 3 false-positive quarantines found and fixed, with regression tests | **Tracked** |
| Evidence retrieval time | Event-specific baseline | 2.7 s for a 350-control sweep over 4,603 chunks | **Baselined** |

### 5.6 The 25 auditor challenges

**SOURCE.** S5 §15 supplies 25 seeded adversarial scenarios with injected fact
patterns, expected evidence and high-risk red flags. **DERIVED:** these are not
narrative colour, they are a ready-made acceptance suite. Eight are already
detectable by the implemented engine; the rest require the cross-record
reconciliation rules scheduled for Milestone 4.

| # | Challenge | Currently detectable | Mechanism or gap |
|---|---|---|---|
| 01 | Source currency: newer filename, still Training Copy | **Yes** | Approval state from content, never filename |
| 02 | Non-delegable ownership clicked by a proxy | No | Needs a signer-authority rule |
| 03 | Conflicting approval matrices | No | Needs approval-matrix modelling |
| 04 | Scope reconciliation: 1 interface assessed, 4 exist | Partial | Needs population reconciliation |
| 05 | "Skip QA Acceptance" recorded for a GxP solution | **Yes** | Red-flag matching |
| 09 | URS orphan with no design or test reference | **Yes** | Traceability rule over the graph |
| 10 | Design review sampled 10 of 300 elements | Partial | Needs sampling-rationale rule |
| 13 | Bare "OK" as sole verification evidence | **Yes** | Claim-only marker detection |
| 15 | Failed step closed as a defect only | **Yes** | Deviation/defect cross-check |
| 18 | First production event predates QA release | No | Needs chronology reconciliation |
| 20 | Access review covers app users but not DB or service accounts | **Yes** | Population-coverage rule |
| 21 | ATR excludes direct DB and admin activity | **Yes** | Red-flag matching |
| 24 | PSE exceeded 60 days via informal extension | **Yes** | Currency and exception rule |
---

## PART 6 · THE DOCUMENT TAXONOMY: LIMS LIFECYCLE PACKAGE

**SOURCE.** `LIMS-LCP-001` v0.1 defines 177 lifecycle documents across ten phases,
each with owner, reviewers, approvers, regulatory basis and input→output flow. Items
are marked Mandatory or Conditional.

| Phase | Name | Documents |
|---|---|---|
| 1 | Concept and Initiation | 17 |
| 2 | Requirements | 20 |
| 3 | Risk Management | 12 |
| 4 | Design | 20 |
| 5 | Build and Configuration | 17 |
| 6 | Testing and Qualification | 22 |
| 7 | Release | 14 |
| 8 | Operation and Maintenance | 25 |
| 9 | Periodic Evaluation | 15 |
| 10 | Retirement | 15 |
| | **Total** | **177** |

### 6.1 Why this source matters more than it appears to

**DERIVED.** S7 describes a LIMS, not the MES under audit, and a shallow reading
would discard it. It is in fact the most useful *reference model* supplied, for
three reasons:

1. **It defines completeness.** The 35-document MES corpus can be measured against a
   177-document reference taxonomy. A missing artefact type is then a defensible
   finding rather than an opinion.
2. **It supplies the Mandatory/Conditional distinction.** Conditional items become
   mandatory only when a trigger applies — custom development, migration, personal
   data, AI/ML, cloud hosting, electronic signatures. This is the correct way to
   avoid reporting a missing DPIA for a system that processes no personal data.
3. **It names owner, reviewer and approver per artefact.** That is the raw material
   for MIN-01's stage-gated human review and for detecting the S5 §15 challenge 02
   failure (approval by a workflow proxy rather than the accountable owner).

### 6.2 Coverage of the MES corpus against the reference taxonomy

**DERIVED.** Mapping the 35 MES documents onto the ten LIMS phases:

| Phase | Reference docs | MES corpus coverage | Assessment |
|---|---|---|---|
| 1 Concept | 17 | MLGP, SYS, IPLAN | Thin but present |
| 2 Requirements | 20 | URS, URR, DIA | Core present |
| 3 Risk | 12 | ITRA, ITRRA | Core present |
| 4 Design | 20 | FS, DS, CS, IS, DRR, AG, UG | Strong |
| 5 Build | 17 | CS, AG | Thin |
| 6 Testing | 22 | IQP, IQTC, IQR, DEVL, DEFL, TRM | IQ only; **no OQ, no PQ, no UAT** |
| 7 Release | 14 | IREP, VSR | Draft only |
| 8 Operations | 25 | OMSOP, SLA, AMRR, ATR, BRVR, IRP, IRTR, CHG, INC, TRN | Present but forward-looking |
| 9 Periodic | 15 | ITPSE | Single future-state report |
| 10 Retirement | 15 | **none** | Absent, and correctly so |

**DERIVED — the key inference.** Phase 6 contains IQ artefacts and nothing for OQ,
PQ or UAT. Phase 10 is empty. Independently of any date or status field, the
artefact population alone locates this system at **Installation Qualification within
the Implement macro phase**. That inference is what the applicability engine
automates, and it is derived from evidence rather than asserted.

---

## PART 7 · UNIFIED ARCHITECTURE

**DECISION.** One architecture satisfying all ten sources.

```
                          USER (browser)
                                |
                        127.0.0.1:8765
                                |
              +-----------------v------------------+
              |  STATIC SPA served by the backend  |
              |  9 pages, one process, one port    |
              +-----------------+------------------+
                                | /api/*
              +-----------------v------------------+
              |  API LAYER - DTOs only, no logic   |
              +-----------------+------------------+
              |  SERVICE LAYER - authz, use cases  |
              +--+--------------+---------------+--+
                 |              |               |
        +--------v----+  +------v-------+  +---v--------------+
        | A0 SUPERVISOR|  | DETERMINISTIC|  | INGESTION and    |
        | intent, plan |  | RULES ENGINE |  | RETRIEVAL        |
        | fan-out      |  | 350 controls |  | 12 steps, FTS5   |
        +--------+-----+  +------+-------+  +---+--------------+
                 |               |              |
   +-------------v---------------v--------------v-------------+
   |  A1 Knowledge   A2 Audit   A3 Risk   A4 Change           |
   |  A5 Incident    A6 Access  A7 Remediation                |
   |  differ ONLY by prompt, tools, permissions, rules,       |
   |  memory scope and output schema                          |
   +-------------------------+--------------------------------+
                             |
   +-------------------------v--------------------------------+
   | C1 EVIDENCE VERIFIER   - independent, downgrade-only     |
   | C2 POLICY GATEWAY      - 100% deterministic, default DENY|
   | C3 ACTION GATEWAY      - READ/DRAFT/MOCK/GXP/PROHIBITED  |
   +-------------------------+--------------------------------+
                             |
                     HUMAN APPROVAL (mandatory note)
                             |
   +-------------------------v--------------------------------+
   | REPOSITORIES - the only SQL in the codebase              |
   | evidence.db | audit.db | config.db | roles.db  + FTS5    |
   | evidence graph projection | SHA-256 hash chain           |
   +----------------------------------------------------------+
                             |
        LLM PORT -> LlamaCppAdapter (127.0.0.1) | NullAdapter
```

### 7.1 The seven specialists and their deterministic modules

**SOURCE + DECISION.** S1 fixes the agent identities; the deterministic module
assignment is the implementation decision that makes them more than prompts.

| ID | Agent | Owns these finding categories | Deterministic modules |
|---|---|---|---|
| A0 | Supervisor / Orchestrator | none — routes only | intent routing table, fan-out budget |
| A1 | Knowledge | DATA_INTEGRITY, TRAINING | mandatory-field completeness, owner consistency |
| A2 | Audit & Compliance | DOCUMENTATION, VALIDATION, TRACEABILITY, PERIODIC_REVIEW | deliverable completeness, approval state, currency, traceability |
| A3 | Risk | RISK, SUPPLIER | demo risk rubric, risk-review expiry, supplier reassessment |
| A4 | Change & Release | CHANGE, BACKUP | change completeness, regression need, backup freshness |
| A5 | Incident | INCIDENT | open-priority detection, overdue RCA, recurrence clustering |
| A6 | Access | ACCESS | overdue review, privileged scope, orphan accounts, SoD |
| A7 | Remediation | none — proposes only | action eligibility, proposal construction |

A1 through A6 are **read-only**. A7 is the only agent that may construct an
`ActionProposal`, and construction is not execution.

### 7.2 Mapping the empty research directories to implementation

**DECISION.** The nine empty `research/` directories in the repository name the nine
domains this solution depends on. Each now has an owning module:

| `research/` directory | Implementing module | Status |
|---|---|---|
| `Prompt_Injection` | `app/security/injection.py` — 3-layer scanner, 20 signatures | Implemented, 16 tests |
| `RAG` | `app/rag/` — 12-step ingestion, 7 extractors, FTS5 + deterministic re-rank | Implemented |
| `Multi_Agent` | `app/agents/`, `app/orchestration/` — 8 definitions, 1 class | Definitions implemented |
| `Knowledge_Graph` | `app/graph/` — closed node/edge enums over the evidence store | Enums implemented |
| `Explainable_AI` | `app/rules/confidence.py`, `readiness.py` — every factor exposed | Implemented |
| `AI_Safety` | `app/policy/`, `app/actions/` — C2 and C3 gateways | Designed, Milestone 3 |
| `Regulatory_AI` | S5 §10.10 AI/ML overlay; prompt and model governance | Designed |
| `Regulatory_Guidance` | `regulatory_refs` carried on every finding from the catalogue | Implemented |
| `Surveys` | This document, Parts 4–6 | Complete |

---

## PART 8 · THE DETERMINISTIC ENGINE: DESIGN AND THE DEFECTS IT SURVIVED

**DERIVED.** The engine was built, measured, found wrong four times, and corrected.
This section records the defects because they are the most transferable engineering
content in the project: each was a plausible design that produced a misleading
number, and each correction is now protected by a regression test.

### 8.1 Defect 1 — Symmetric confidence reported high confidence in expired paperwork

**Observed.** Three approved but expired sources produced `HIGH` confidence at 85%
coverage. A single approved, current source with no executed evidence also produced
`HIGH` at 80%.

**Diagnosis.** A single symmetric formula was scoring *evidence quality* and calling
it *confidence in the conclusion*. Those are different quantities.

**Correction — direction-aware confidence.** Confidence is confidence in the
**conclusion**, so it depends on the direction of the claim:

- A **GAP** claim ("the access review is overdue and remediation is Open") is
  *strengthened* by draft, expired and missing evidence, because absence and
  immaturity are consistent with the gap being real.
- A **CONFORMANCE** claim ("this control demonstrably operates") requires approved,
  current, corroborated, executed evidence and is held to hard ceilings.

Four ceilings now apply, and each can only lower a level, never raise one:

| Ceiling | Trigger | Effect |
|---|---|---|
| Expired source | any cited source past its review date, conformance claim | cap MEDIUM |
| No approved source | no cited source approved, conformance claim | cap LOW |
| No execution evidence | approved narrative with no executed record | cap MEDIUM |
| Single-source gap | gap asserted from one source | cap MEDIUM — enforces the SOP's triangulation requirement |

**Verified.** Expired + executed now caps at MEDIUM. All-draft + executed caps at
LOW. Approved + current + executed + corroborated reaches HIGH. A gap corroborated
by three draft sources reaches HIGH; the same gap from one source caps at MEDIUM.

### 8.2 Defect 2 — Three legitimate documents were quarantined

**Observed.** The first full corpus run quarantined `NL-MES-IS-001`,
`NL-MES-ITPSE-001` and `NL-MES-MLGP-001`.

**Diagnosis.** Two naive patterns:

1. A base64 detector `[A-Za-z0-9+/]{120,}` fired on legitimate prose:
   `Purpose/scope/roles/definitions/trace/overview/resources/inputs...`
2. A suppression detector fired on **good practice**: *"Do not cite exact regulatory
   or internal clause numbers unless verified in an accessible source."*

**Why this was the most serious defect found.** A false-positive quarantine removes
the record an auditor asked for. An assurance tool that hides evidence while
reporting a gap is worse than one that never ran. It is also self-concealing: the
resulting finding looks like a legitimate detection.

**Correction.**

- Encoded-payload detection now requires four independent conditions: charset and
  length, Shannon entropy ≥ 4.2, successful strict base64 decoding to ≥ 60 bytes,
  and an absence of ordinary word shapes.
- Suppression detection now requires an adversarial object — a specific finding, or a
  named reviewer, auditor, inspector or regulator — with a negative lookahead for
  the benign qualifier "unless".

**Verified.** Quarantines dropped from 3 to **0**. All twelve attack detections
still fire. Four false-positive regression tests, built from the exact real corpus
strings, now guard the fix permanently.

### 8.3 Defect 3 — Seventeen critical findings for retirement work not yet due

**Observed.** Phase 14 (Decommissioning, Data Retention & Migration) produced 17
critical findings. Every phase scored between 0 and 8 out of 100.

**Diagnosis.** The system is a **new implementation at IQ**. It has no
decommissioning records because it must not have any. Reporting them as critical
gaps is a false-positive cluster large enough to discredit every true finding beside
it.

**Correction — lifecycle applicability gating.** S5's answer contract already
supplies the right vocabulary: `NOT_APPLICABLE_WITH_EVIDENCE` is a distinct
conclusion from `NOT_DEMONSTRATED`. The engine now:

1. Derives the system's position from the **artefact population**, scanning phases in
   order and stopping at the first with no phase-entry marker. Contiguity matters: a
   forward-looking draft from a later phase does not prove earlier gates were passed.
2. Marks controls beyond that position `NOT_APPLICABLE_WITH_EVIDENCE`, severity
   INFO, no approval required, **with the evidence-based reason stated**.
3. Excludes them from the readiness denominator while still reporting them.

**Verified.** Derived position: `IMPLEMENT`, highest phase reached **7 — Installation
Qualification**, basis *"Evidence of arrival was found for: Concept & Business Case;
User Requirements; Risk Assessment & GAMP Categorisation; Supplier Assessment;
Functional / Design Specifications; Configuration & Development; Installation
Qualification."* Phases 8–14 correctly not assessed. 175 assessable, 175 deferred.

### 8.4 Defect 4 — The indicator saturated to zero at full scale

**Observed.** With 350 controls the readiness indicator was 0/100 for every phase,
including phases with genuine partial evidence.

**Diagnosis.** Two compounding errors.

1. **Absolute penalties do not scale.** `critical×8 + high×3` is stable across a
   hand-seeded demo of eight findings and reaches 495 across 350, swamping any
   subtotal.
2. **The penalty double-counted.** Severity in this engine is *derived from* maturity.
   Subtracting a severity penalty from a maturity-derived subtotal punishes the same
   weakness twice.

**Correction.** Severity became a **ceiling**, never a subtraction. Weak evidence
already lowers the subtotal through maturity; the presence of criticals additionally
*forbids* a high score. The ceiling scales with the critical rate, from 65 down to a
floor of 25, so "one critical" and "half the estate critical" cannot produce the same
headline number.

**Verified.** A healthy estate scores ≥ 95. Adding one critical caps it at ≤ 65 and
flips the verdict to NOT READY. Adding five criticals is monotonically
non-increasing. A 350-control maturity-2 estate no longer scores zero.

### 8.5 Two-tier grounding

**DECISION.** After removing an unsound evidence backfill, 83 of 175 assessable
controls reported no evidence — but the corpus visibly contained relevant material.
The cause was an over-narrow expected-artefact mapping, not a real gap.

Backfilling with any topically-adjacent chunk would have manufactured grounding.
Instead retrieval is explicitly two-tier, and which tier fired is recorded in the
finding's `rule_id`:

| Tier | Search scope | Relevance floor | Maximum maturity |
|---|---|---|---|
| 1 | only the artefact types the question expects | 4.0 | 4 — Corroborated |
| 2 | the whole corpus | 9.0 | **1 — Claim only** |
| 0 | nothing cleared either floor | – | 0 — Absent, abstain |

Tier-2 evidence can never count as execution evidence, can never be treated as
corroborated, and produces an explicit claim: *"no artefact of the expected type was
located; relevant content was found in X, Y, Z, which evidences intent but is not
the controlled artefact this question requires."*

**Verified.** Grounded answer rate rose from 53% to **100%** with no loss of
honesty: 92 controls are grounded in the expected artefact, 83 are explicitly
grounded off-type and capped at maturity 1.
---

## PART 9 · VERIFIED RESULTS

**SOURCE.** Every figure below was produced by executing the implementation, not
estimated. Reproduce with `python3 scripts/run_assessment.py` and
`python3 scripts/offline_self_test.py`. Assessment date frozen at 27 August 2026.

### 9.1 Ingestion

| Measure | Result |
|---|---|
| Documents ingested | 35 of 35 |
| Extracted text | 3,314,385 characters |
| Indexed evidence chunks (SQLite FTS5) | 4,603 |
| SHA-256 computed before any parsing | 35 of 35 |
| Legitimate evidence quarantined | **0** |
| Sources marked `APPROVED` | 0 — correct; the package is entirely v0.1 draft |
| Seed runtime | 5.4 s |

### 9.2 Control sweep

| Measure | Result |
|---|---|
| Controls supplied | 350 |
| Assessable at the current lifecycle phase | 175 |
| Correctly deferred as not-yet-reached | 175 |
| Sweep runtime | 2.7 s (≈14 ms per control) |
| Grounded answer rate | **100%** (175/175) |
| Grounded in the expected artefact type (tier 1) | 92 |
| Grounded off-type, capped at maturity 1 (tier 2) | 83 |
| Unsupported material claims | **0** |
| Specialists engaged | A1, A2, A3, A4, A5, A6 |

Maturity distribution across assessable controls: `CLAIM_ONLY` 143,
`DOCUMENT_LOCATED` 32. No control reached `DEMONSTRATED`, which is the correct
result for a package in which nothing is approved and no test has been executed.

Severity: HIGH 126, MEDIUM 43, LOW 6. Conclusions: `NOT_DEMONSTRATED` 143,
`PARTIALLY_DEMONSTRATED` 32. Confidence: HIGH 107, MEDIUM 68 — all HIGH values are
gap claims triangulated across three or more independent sources.

### 9.3 Readiness indicator

```
PROTOTYPE READINESS INDICATOR   29/100    NOT READY FOR SIMULATED INSPECTION
169 open deterministic findings - 0 critical
Not a compliance certification.

  Compliance & readiness      28%   Control evidence (50 checks)
  Risk posture                28%   Demo rubric (28 checks)
  Operations                  32%   Service evidence (22 checks)
  Incidents                   31%   Open events (4 checks)
  Access                      28%   Review status (26 checks)
  Documentation               32%   Indexed sources (45 checks)

View calculation
  controls_supplied              350
  controls_not_yet_applicable    175
  controls_evaluated             175
  weighted_subtotal              29.45
  critical_findings              0
  ceiling_applied                80.0
  final_score                    29
```

Phase readiness: Concept 31, URS 25, Risk 24, Supplier 35, Design 27, Configuration
27, IQ 22. Phases 8 through 14 reported as not yet reached.

**DERIVED — is 29/100 defensible?** Yes, and it is the number a QA reviewer would
expect. Every document is `v0.1` draft; no artefact carries a genuine approval; the
traceability matrix records test execution as *"Planned / No Run"*; and the access
review concludes *"Not in control"* with remediation Open. A high score against that
evidence base would be the defect. The sanctioned phrasing from the Visual User
Manual applies directly: *"The prototype indicator is 29/100 with medium overall
confidence because evidence is missing, stale or unapproved."*

### 9.4 Offline self-test

```
GxP Sentinel Offline Readiness
--------------------------------------------------------------
Local AI engine           DETERMINISTIC FALLBACK
Cloud API dependency      PASS   NONE
Zero-dependency core      PASS   standard library only
Synthetic database        PASS   35 sources, 4603 chunks
Evidence grounding        PASS   175/175 grounded, all references resolve
Abstention control        PASS   no unsupported material claim
Audit rules               PASS   169 material findings detected
Agent orchestration       PASS   specialists engaged: A1,A2,A3,A4,A5,A6
Prompt-injection defence  PASS   attack blocked, valid evidence not quarantined
Human approval control    PASS   every material finding routes to a person
Audit chain               PASS   12 events verified
Readiness indicator       PASS   29/100 - NOT READY FOR SIMULATED INSPECTION
Internet required         NO
--------------------------------------------------------------
All offline readiness checks passed.
```

### 9.5 Test suite

**88 tests, all passing, in 42 seconds, with no model and no third-party package
installed.**

| Suite | Tests | Proves |
|---|---|---|
| `tests/security/test_injection_scanner.py` | 16 | 12 attack classes detected; 4 real-corpus false-positive regressions |
| `tests/security/test_ingestion_boundary.py` | 15 | filename hygiene, format and size gates, trust assignment, XXE refusal |
| `tests/unit/test_audit_chain.py` | 7 | EVAL-015 chain verifies, EVAL-016 tampering detected, deletion detected, no mutation API |
| `tests/unit/rules/test_confidence.py` | 12 | abstention, conformance ceilings, gap polarity, triangulation, bounded coverage |
| `tests/unit/rules/test_readiness.py` | 9 | explainability, weights sum to 1.0, critical ceiling, monotonicity, no saturation |
| `tests/integration/test_corpus_pipeline.py` | 21 | real 35-document corpus end to end, determinism, grounding, applicability |
| `tests/smoke/test_offline_readiness.py` | 8 | no cloud import, no API key, no non-loopback host, no shell in agent layers, FTS5 present |

### 9.6 Guardrails enforced mechanically

| Guardrail | Method | Result |
|---|---|---|
| No cloud or agent-framework import | AST walk over every module | PASS |
| No API key referenced anywhere | text scan | PASS |
| No non-loopback host | line scan with an allowlist | PASS |
| No shell, `eval`, `exec` or `pickle` in agent, tool, rule, policy or action layers | text scan | PASS |
| No SQL outside the repository and database layers | ripgrep in CI | PASS |
| No bare `except` or swallowed exception | ripgrep in CI | PASS |
| No `print()` in the application layer | ripgrep | PASS |
| No naive `datetime.now()` outside `SystemClock` | ripgrep | PASS |
| Core imports on a bare interpreter | import test | PASS |

---

## PART 10 · TRACEABILITY

**DERIVED.** Every requirement traces to a source, an implementation and a test.

| Requirement | Source | Implementation | Verified by |
|---|---|---|---|
| One local model, seven logical agents | S1 §3 | `CATEGORY_OWNER`, one `LogicalAgent` config | `test_findings_are_owned_by_the_correct_specialist` |
| Deterministic-first, model as reasoning assistant | S1 §6 | `app/rules/` contains no model call | `test_no_cloud_or_agent_framework_imports` |
| Two runtime modes, feature parity | S1 §5 | `RuntimeMode`; findings identical in both | whole suite runs with no model |
| Evidence-first, abstention as a feature | S1 §3C, S5 §11.4 | `AgentFinding.__post_init__` invariant | `test_eval_020_no_finding_without_evidence_or_abstention` |
| Confidence from coverage, not self-report | S1 §9 | `app/rules/confidence.py` | `tests/unit/rules/test_confidence.py` |
| 0–4 maturity rubric | S5 §11.5 | `MaturityScore`, `maturity_from_state` | `test_rubric_matches_the_master_sop_levels` |
| Five-value answer contract | S5 §11.4 | `AuditConclusion` | `test_future_phases_are_not_reported_as_gaps` |
| Six bias countermeasures | S5 §11.6 | Part 5.4 table | `test_training_banner_is_not_treated_as_an_approval` |
| 12-step ingestion with hash and injection scan | S1 §7 | `IngestionPipeline.ingest` | `tests/security/test_ingestion_boundary.py` |
| Retrieved content is always untrusted data | S1 §7 | `TrustLevel`, `fence()`, `DATA_FENCE_PREAMBLE` | `test_clean_upload_is_never_trusted_on_arrival` |
| Quarantine suspicious sources | S1 §7 | `QUARANTINED_UNTRUSTED`, never indexed | `test_malicious_upload_is_quarantined_and_not_indexed` |
| Local retrieval, no vector database | S1 §7 | SQLite FTS5 + deterministic re-rank | `TestRetrieval`, `test_fts5_is_available` |
| Hash-chained tamper-evident audit trail | S1 §14, MIN-07 | `AuditRepository` | `test_eval_015`, `test_eval_016` |
| Human approval for GxP-relevant actions | S1 §4 C3, MIN-01 | `ActionType`, `ApprovalDecision` | `test_material_findings_require_human_approval` |
| Approval payload is server-authoritative | S1 §4 C3 | `ActionProposal` scalars only | `ActionProposal.__post_init__` |
| No AI approver, ever | S1 §3D | no code path executes `GXP_RELEVANT_WRITE` | `test_no_shell_or_code_execution` |
| Five demonstration roles, server-side | S1 §18, S2 p.4 | `Role`, `Permission` | Milestone 3 |
| 12 MB upload ceiling, 7 formats | S2 p.5 | `MAX_UPLOAD_BYTES`, `ALLOWED_EXTENSIONS` | `test_oversize_rejected_on_real_byte_count` |
| Extraction limits disclosed | S2 p.5 | extractor `notes`, OCR remediation text | `test_image_only_pdf_reports_ocr_limitation` |
| Explainable readiness, "View calculation" | S2 p.7, MIN-06 | `ReadinessIndicator.calculation` | `test_calculation_exposes_every_input` |
| Assess the whole GxP IT system | MIN-08 | system-level indicator, corpus-agnostic engine | `TestEngineOutput` |
| Suggest revisions without changing documents | MIN-05 | `ActionType.DRAFT`, no write path | guardrail scan |
| Version-upgrade impact assessment | MIN-09 | evidence graph node/edge enums | Milestone 6 |

---

## PART 11 · IMPLEMENTATION ROADMAP

**DECISION.** Ten milestones in dependency order. Each compiles, runs, is tested,
is documented and leaves the trunk demonstrable.

| M | Milestone | Status | Exit criterion |
|---|---|---|---|
| M0 | Foundation: repo, tooling, CI, `AGENTS.md`, licence, templates, launchers | **Complete** | guardrails green, 88 tests pass |
| M1 | Domain and data: enums, frozen models, error taxonomy, clock, hashing | **Complete** | domain imports on a bare interpreter |
| M2 | Deterministic engine: confidence, readiness, applicability, 350-control sweep | **Complete** | 100% grounded, 29/100 reproducible |
| M3 | Audit and policy: hash chain done; C2 policy gateway, roles, authorisation | **Chain complete**, gateways next | EVAL-010, 015, 016 pass; route inventory test green |
| M4 | Cross-record reconciliation rules: the 25 auditor challenges | Next | ≥ 20 of 25 challenges detected |
| M5 | Persistence and API: four SQLite databases, migrations, FastAPI routers | Designed | `/api/health` green, contract tests pass |
| M6 | Evidence graph and traceability: projection, traversal, upgrade-impact query | Enums done | `URS-MES-001` traced to test result; broken link highlighted |
| M7 | Frontend: 9 pages, design tokens from S3/S4, topology, assurance cards | Design system specified | dashboard renders live data at 127.0.0.1:8765 |
| M8 | Actions and approvals: C3, proposals, dry run, Assurance Lab S1–S7, Trust Centre | Designed | EVAL-009, 013, 017 pass; 7 scenarios demonstrate |
| M9 | Local AI runtime: hardware detection, model catalogue, llama.cpp lifecycle | Designed | model downloads once, verifies, runs on loopback |
| M10 | Release: evidence pack, packaging, three-OS launchers, demo script, rehearsal | Partial | release DoD complete, demo rehearsed twice |

### 11.1 Immediate next actions

1. **M4 first, not M5.** The 25 auditor challenges are the highest-value remaining
   work: they convert a checklist sweep into cross-record reconciliation, which is
   what actually distinguishes this from a document scanner. Eight are already
   detectable; the gap is chronology, population reconciliation and approval-authority
   rules.
2. **Widen the expected-artefact mapping.** 83 controls currently ground off-type
   because the keyword mapping is narrow. Extending it moves findings from tier 2 to
   tier 1 and raises maturity ceilings legitimately.
3. **Seed a deliberate contradiction.** The contradiction plumbing exists but the
   corpus contains no seeded conflict, so `contradictions` is always zero. Adding a
   controlled conflict enables the S5 metric target for contradiction detection.

---

## PART 12 · CONFLICT REGISTER, DECISIONS AND OPEN QUESTIONS

### 12.1 Source conflicts and how each was resolved

| # | Conflict | Resolution | Authority |
|---|---|---|---|
| C1 | S1's master prompt describes an OpenAI provider mode; the zero-key override forbids any cloud API | Override wins. No cloud code path exists; enforced by an AST guardrail test | Explicit in S1 |
| C2 | S1 names Pydantic, FastAPI and NetworkX; the same source says the user may have no Python or Node environment and blocked installs | Core is standard-library only; API extras optional | ADR 0001 |
| C3 | S1 seeds `GXP-MFG-DEMO-01`; the supplied corpus is `NL-MES-001` MES PAS-X | Corpus wins — it is later, richer and matches the minutes' PAS-X instruction | MIN-08 |
| C4 | S2 promises five seeded gaps; the real corpus yields 169 material findings | Both honoured: the five headline gap classes are surfaced in the priority queue, the full sweep sits behind Audit Readiness | S2 p.7 |
| C5 | Corpus documents say "Simulated Reviewed and Approved"; they also say "not valid for GxP release use" | Recorded as `DRAFT`. A training banner is not an approval | S5 §11.6 authority bias |
| C6 | S6 uses 130 `Audit_Domain` labels; the dashboard has six dimensions | Deterministic mapping to 12 categories then 6 dimensions, held in versioned data | Part 4.2 |
| C7 | S7 describes a LIMS; the corpus is an MES | S7 used as a reference taxonomy for completeness, not as the system | Part 6.1 |
| C8 | S5 §11.5 says scores are diagnostic; a dashboard invites them to be read as grades | Every surface carries "Not a compliance certification"; forbidden-word list enforced in copy review | S5 §11.5 |

### 12.2 Assumptions recorded

| # | Assumption | Why necessary | What would invalidate it |
|---|---|---|---|
| A1 | Assessment date is 27 August 2026, frozen | Overdue and currency rules are date comparisons; a moving date makes results irreproducible | A live deployment would inject `SystemClock` |
| A2 | All 35 corpus documents describe one system, `NL-MES-001` | Every document carries the `NL-MES-` prefix and cross-references the same registers | A multi-system corpus |
| A3 | Sixteen document types constitute executed evidence | Derived from document purpose in S7 and the corpus | A reviewer disputing a type's classification |
| A4 | Phase-entry markers prove phase arrival | The artefact population is the only date-independent signal available | Explicit gate records, which the corpus lacks |
| A5 | Absent review dates mean no periodic review is yet due | Corpus documents carry no review date | Any document carrying one |

### 12.3 Open questions for the mentor

1. **Version-upgrade impact assessment (MIN-09) is named as the intended use case, but
   the corpus contains no upgrade.** Should a synthetic PAS-X version-upgrade change
   record be seeded, or will one be supplied? The evidence graph substrate is ready
   either way.
2. **Is the readiness indicator expected per document, per phase, or per system?** The
   minutes say the dashboard scores *each document* against document-specific
   checklists, while the scope clarification says assess *the complete system*. Both
   are currently produced; confirmation would let one become the headline.
3. **PAS-X sample documentation was promised "in a couple of days."** If it differs
   structurally from the NOVOLIFE package, the seeder's filename convention and the
   phase-marker table are the two places that need updating.

### 12.4 What would be required before real use

**DECISION.** Stated plainly, because a panel will ask.

Before connecting real enterprise data: authenticated identity with real segregation
of duties; qualified connectors under change control; a data classification and
privacy assessment; supplier assessment of the model publisher; and removal of every
synthetic-data affordance.

Before any regulated production use: 21 CFR Part 11 compliant electronic signatures
in place of prototype approvals; validated hosting with WORM or equivalent retention
in place of a tamper-evident chain; a formal URS, risk assessment, validation and
periodic review **of this system itself**; model change control with regression
evaluation and drift thresholds; and documented AI governance sign-off.

---

## APPENDIX A · IDENTIFIER CONVENTIONS

| Pattern | Meaning | Count |
|---|---|---|
| `DA-<pp>-<sss>` | Audit checklist question | 350 |
| `NL-MES-<TYPE>-001` | Corpus document | 35 |
| `URS-MES-<nnn>` | User requirement | 50 |
| `RSK-MES-<nnn>` | Shared risk | 26 |
| `CI-MES-<nnn>` | Configuration item | 50 |
| `DUMMY-DEV-MES-<nnn>` | Validation deviation | 6 |
| `DUMMY-TC-MES-IQ-<nnn>` | IQ test case | ~32 |
| `FND-DA-<pp>-<sss>` | Engine finding, one per control | 350 |
| `CHECKLIST::<q_id>::tier<n>` | Rule identifier with grounding tier | – |
| `APPLICABILITY::<q_id>` | Rule identifier for a deferred control | – |

## APPENDIX B · GLOSSARY

| Term | Meaning in this project |
|---|---|
| Assessable control | A control whose lifecycle phase the system has reached |
| Claim polarity | Whether a finding asserts a GAP or CONFORMANCE; governs confidence |
| Confidence | Deterministic confidence in the **conclusion**, never model self-report |
| Coverage | Weighted sum of evidence factors, 0–1, exposed factor by factor |
| Execution evidence | A record of what *did* happen, as distinct from an approved plan |
| Grounding tier | 1 = expected artefact, 2 = off-type, 0 = abstention |
| Maturity | The master SOP's 0–4 rubric |
| Not yet reached | Phase-based deferral, reported as `NOT_APPLICABLE_WITH_EVIDENCE` |
| Readiness indicator | Explainable composite, never a certification |
| Tamper-evident | Changes to the audit chain are detectable; not immutable, not WORM |
| Trust level | `TRUSTED`, `UNTRUSTED_REVIEW_REQUIRED`, `QUARANTINED_UNTRUSTED` |

---

**END OF MASTER RESEARCH REFERENCE**

*Compiled from ten supplied sources. All quantitative results were produced by
executing the implementation on 27 August 2026 and are reproducible with
`make verify`.*
