# Course Outcome 1 — Assessment 2 (CO1-AT2)
## Mathematical Foundations of Deep Learning: Diabetic Retinopathy Screening Model Audit

---

### Executive Overview
This module contains the complete analytical solutions, mathematical proofs, and finalized submission deliverables for **CO1-AT2** in **CSA4706 - Deep Learning** (Bloom's Level K4 — Analyse, 50 Marks). 

The assessment rigorously investigates the mathematical foundations of the *RetinaCare* tele-ophthalmology screening system across 11 structured tasks, addressing feature compression, loss formulation, optimization landscapes, Bayesian probability, gradient dynamics, and health policy optimization under asymmetric misclassification costs.

---

### Submission Deliverables
- **Completed Submission Document (Word)**: [`CSA47_CO1_Assessment2_Completed.docx`](./CSA47_CO1_Assessment2_Completed.docx) (31 pages, 17 styled tables, embedded high-DPI figures, callout styling)
- **Verified PDF Deliverable**: [`CSA47_CO1_Assessment2_Completed.pdf`](./CSA47_CO1_Assessment2_Completed.pdf) (Exported via MS Word COM)
- **Original Assessment Template**: [`CSA47_CO1_Assessment2.docx`](./CSA47_CO1_Assessment2.docx)

---

### Key Mathematical Findings Across All 11 Tasks
- **Task 1 (Audit Breakdown)**: 6-stage clinical pipeline with 5 critical inter-stage mathematical couplings.
- **Task 2 (SVD & Low-Rank)**: Singular values $\sigma_1 = 3\sqrt{5} \approx 6.7082, \sigma_2 = \sqrt{5} \approx 2.2361$ ($\sigma_1/\sigma_2 = 3.0$). Rank-1 matrix $A_1$ preserves $90.0\%$ energy, but discarding the $10.0\%$ residual eliminates crucial microaneurysm pathology.
- **Task 3 (Convex Optimization & Hessian)**: Hessian $H = \begin{pmatrix} 4 & 1 \\ 1 & 4 \end{pmatrix} \succ 0$ with $\lambda \in \{5.0, 3.0\}$. Condition number $\kappa(H) = 1.6667$. Unique minimizer $w^* = [1, 1]^T$ ($J(w^*) = -5.0$). Maximum stable learning rate $\eta < 0.4000$.
- **Task 4 (Information Theory & KL Divergence)**: Ground-truth entropy $H(p) = 1.7500$ bits. Cross-entropy $H(p, q_1) = 2.0000$ bits. Relative entropy $D_{KL}(p \parallel q_1) = 0.2500$ bits. Splitting identity verified: $1.7500 + 0.2500 = 2.0000$. Trained model achieves $79.72\%$ divergence reduction ($D_{KL}(p \parallel q_2) = 0.0507$ bits).
- **Task 5 (Bayesian Base-Rate Paradox)**: Under 10% prevalence, sensitivity 90% and specificity 95% yield $\text{PPV} = 66.67\%$. 1 in 3 positive flags is a false alarm, requiring mandatory secondary clinical review.
- **Task 6 (Gradient Descent Contraction)**: Contraction ratio $\rho = |1 - \eta \lambda_1| = |1 - 0.5| = 0.5000$. Parameter error halves each iteration ($\|e_k\| = 1.4142 \times 0.5^k$).
- **Task 7 (Momentum Acceleration & Stability)**: Physical velocity formulation ($v_t = \beta v_{t-1} - \eta \nabla J, w_t = w_{t-1} + v_t$) results in momentum overshoot ($w_2 = [1.2, 1.2]^T$) while reaching closer to $w^*$ than GD. Step size $\eta = 0.50$ exceeds stability limit $\eta < 0.40$, producing explosive oscillation ($(-1.5)^k \to \infty$).
- **Task 8 (Bias-Variance Tradeoff)**: Model P (underfitting, $\text{MSE} = 3.50$) outperforms Model Q (overfitting, $\text{MSE} = 5.50$) due to superior clinical stability across rural validation sites.
- **Task 9 (Confusion Matrix & Cost Asymmetry)**: Diagnostic accuracy: $85.0\%$, Macro-$F_1$: $84.21\%$. The $2:1$ error asymmetry ($FN:FP = 10:5$) violates ophthalmological safety.
- **Task 10 (Clinical Synthesis)**: Comprehensive audit matrix mapping mathematical properties to patient safety risks.
- **Task 11 (Rural Policy Optimization)**:
  - Under 2% rural prevalence, PPV collapses to **26.87%** ($73.13\%$ false alarms).
  - Minimum specificity for $\text{PPV} \ge 50\%$ is derived as **$Sp \ge 98.1633\%$**.
  - Cost analysis (10:1 $FN:FP$ penalty) demonstrates that redesigning into a **Hybrid Tri-State Triage System** cuts overall operational cost by **50.43%** ($69.00 \to 34.20$ cost units / 1,000 patients).
