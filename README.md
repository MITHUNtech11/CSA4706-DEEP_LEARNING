# CSA4706 — Deep Learning
### Academic Coursework, Empirical Benchmarks & Capstone Project Repository
**Department of Computer Science & Engineering | Saveetha School of Engineering (SIMATS)**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2+-EE4C2C?style=flat&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![Status](https://img.shields.io/badge/Status-Fully%20Audited%20%26%20Verified-brightgreen?style=flat)]()
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Institution](https://img.shields.io/badge/Institution-SIMATS%20Engineering-orange)](https://saveetha.com/)

---

## Executive Overview
This repository contains the complete, production-ready codebase, empirical experimental results, mathematical derivations, and publication-ready academic deliverables for **CSA4706 — Deep Learning**. 

The repository is structured into three comprehensive modules spanning agricultural computer vision diagnostics, theoretical mathematical foundations in clinical screening, and zero-trust generative AI system security:

1. **Course Outcome 1 — Assessment 1 (`CO1-AT1`)**:  
   *AgriVision: Empirical Deep Learning Suite on PlantVillage Tomato Leaf Dataset.*  
   Features linear dimensionality reduction (PCA), baseline classifiers (Logistic Regression, $k$-NN, Random Forest), empirical bias-variance estimation, first-order optimizer dynamics, dataset scaling trajectories, and edge-constrained neural network quantization.

2. **Course Outcome 1 — Assessment 2 (`CO1-AT2`)**:  
   *Mathematical Foundations of Clinical Deep Learning: Diabetic Retinopathy Screening Model Audit.*  
   Features rigorous analytical proofs and derivations across 11 tasks covering Singular Value Decomposition (SVD), multivariate convex optimization via Hessian eigen-decomposition, Shannon information theory & KL divergence, Bayesian base-rate paradoxes, gradient descent contraction dynamics, classical momentum stability bounds, and health economic policy redesign under asymmetric misclassification costs ($10:1$ penalty).

3. **Capstone Research Project (`Capstone`)**:  
   *Secure Role-Based Access Control for a Retrieval-Augmented Generation (RAG) System in a Hospital.*  
   Features a multi-tiered zero-trust security architecture enforcing deterministic retrieval-layer metadata filtering, server-side system prompt rendering, output grounding gates, and append-only cryptographic hash-chained audit trails ($\mathbf{h}_n = \text{SHA-256}(\text{entry}_n \,\|\, \mathbf{h}_{n-1})$).

---

## Deliverables & Artifacts Index

| Module | Core Deliverable (Word) | Compiled Document (PDF) | Topic / Domain |
|:---|:---|:---|:---|
| **CO1-AT1** | [`AgriVision_Deep_Learning_Answers_Completed.docx`](./CO1-AT1/AgriVision_Deep_Learning_Assignment_Answers_Completed.docx) | [`AgriVision_Deep_Learning_Answers_Completed.pdf`](./CO1-AT1/AgriVision_Deep_Learning_Assignment_Answers_Completed.pdf) | Agricultural Foliar Vision Diagnostics (PlantVillage) |
| **CO1-AT2** | [`CSA47_CO1_Assessment2_Completed.docx`](./CO1-AT2/CSA47_CO1_Assessment2_Completed.docx) | [`CSA47_CO1_Assessment2_Completed.pdf`](./CO1-AT2/CSA47_CO1_Assessment2_Completed.pdf) | Mathematical Foundations in Clinical Screening (RetinaCare) |
| **Capstone** | — | [`Secure_RAG_RBAC_Hospital.pdf`](./Capstone/Secure_RAG_RBAC_Hospital.pdf) | Hospital RAG Zero-Trust Access Control & Auditing (Full Implementation) |

---

## Key Findings & Benchmark Summaries

### 1. CO1-AT1: PlantVillage Empirical Diagnostics
- **Selected PCA Dimensionality**: $k = 128$ components captures **88.88%** cumulative variance with reconstruction MSE of **0.003328** and peak validation Macro-F1 of **0.6721**.
- **Classical vs. Linear**: Random Forest on raw pixels achieved peak classical accuracy of **86.22%**, while PCA-reduced Logistic Regression provided maximum computational efficiency (**0.026s fit time**, **0.002 ms latency**, **2 KB binary**).
- **Optimization Best Performer**: Mini-Batch SGD ($\eta=0.01$, batch size 64) achieved the lowest validation loss (**0.7816**) in 52 epochs.
- **Edge Deployment**: Compact 3-layer quantized CNN achieved **0.7661 Macro-F1** with **0.80 ms latency** and a **160 KB binary**, outperforming linear baselines under 20% sensor noise ($0.644$ vs. $0.620$).

### 2. CO1-AT2: Diabetic Retinopathy Screening Audit
- **SVD Energy vs. Pathology**: Truncating singular value $\sigma_2 = 2.2361$ retains $90.0\%$ energy but discards subtle microaneurysm pathology responsible for early detection.
- **Optimization Geometry**: Loss Hessian $H = \begin{pmatrix} 4 & 1 \\ 1 & 4 \end{pmatrix}$ has eigenvalues $\lambda \in \{5.0, 3.0\}$ with condition number $\kappa(H) = 1.6667$, ensuring fast convergence for $\eta < 0.4000$.
- **Base-Rate Dilemma**: A 5-fold decrease in prevalence ($10\% \to 2\%$) collapses positive predictive value (PPV) from **66.67% to 26.87%**, resulting in 73.13% false alarms.
- **Operational Policy Optimization**: Under a 10:1 false negative cost penalty, adopting a **Hybrid Tri-State Triage system** reduces operational costs from 69.00 down to **34.20 units per 1,000 patients (-50.43%)**.

### 3. Capstone: Hospital RAG Zero-Trust Security
- **Enforced Retrieval Layer**: Access boundaries are enforced at the database metadata indexing layer prior to vector search, preventing unauthorized patient data from ever reaching the LLM prompt.
- **Administrative Isolation**: System administrators are restricted strictly to control panel orchestration with **zero patient record access**.
- **Cryptographic Auditability**: Continuous SHA-256 hash chaining ensures that all query attempts, filtered document IDs, and access decisions are tamper-evident.

---

## Repository Structure

```
CSA4706 - DEEP LEARNING/
├── .gitignore                             # Git ignore rules
├── README.md                              # Main repository documentation & guide
│
├── CO1-AT1/                               # Course Outcome 1 - Assessment 1
│   ├── README.md                          # Module summary & benchmark notes
│   ├── AgriVision_..._Completed.docx      # Final Word submission deliverable
│   └── AgriVision_..._Completed.pdf       # Compiled submission PDF
│
├── CO1-AT2/                               # Course Outcome 1 - Assessment 2
│   ├── README.md                          # Module summary & mathematical breakdown
│   ├── CSA47_CO1_Assessment2.docx         # Original assessment template
│   ├── CSA47_CO1_..._Completed.docx       # Final Word submission deliverable (31 pages)
│   └── CSA47_CO1_..._Completed.pdf        # Verified PDF export
│
└── Capstone/                              # Capstone Research & Implementation Project
    ├── README.md                          # Architecture & setup documentation
    ├── Secure_RAG_RBAC_Hospital.pdf       # Presentation slide deck
    ├── requirements.txt                   # Capstone service dependencies
    ├── pytest.ini                         # Test runner configuration
    ├── data/                              # Synthetic patient database & generator
    ├── policies/                          # Granular JSON access control policies
    ├── scripts/                           # Security evaluation & interactive CLI
    ├── src/                               # 3-tier security architecture implementation
    │   ├── api/                           # FastAPI service & REST endpoints
    │   ├── module1_identity_policy/       # IdP authentication & policy engine
    │   ├── module2_enforced_retrieval/    # Pre-retrieval SQL/vector filtering
    │   └── module3_generation_audit/      # Output guards & hash-chained audit
    ├── templates/                         # Server-side Jinja2 prompt templates
    ├── tests/                             # Comprehensive end-to-end & security tests
    └── web/                               # Interactive hospital control panel UI
```

---

## Academic Guidance & Team Credits

### Institution
- **University**: Saveetha Institute of Medical and Technical Sciences (SIMATS)
- **School**: Saveetha School of Engineering (SSE)
- **Course**: CSA4706 — Deep Learning

### Capstone Project Team
- **Joseph Asborn Daniel J** (Reg No: 192324009) — *Module 1: Identity & Policy*
- **Prajith K** (Reg No: 192324013) — *Module 2: Enforced Retrieval*
- **Mithunsenthil S** (Reg No: 192324009) — *Module 3: Controlled Generation & Audit*

### Faculty Guide
- **Dr. Vasantharaj K**, Department of Computer Science & Engineering, SIMATS Engineering

---

## License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
