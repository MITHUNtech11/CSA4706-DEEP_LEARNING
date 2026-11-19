# Course Outcome 1 — Assessment 1 (CO1-AT1)
## AgriVision: Empirical Deep Learning Suite on PlantVillage Tomato Leaf Dataset

---

### Executive Overview
This module contains the finalized submission deliverables for **CO1-AT1** in **CSA4706 - Deep Learning**. The assignment investigates computer vision diagnostics for precision agriculture using the PlantVillage dataset across three target foliar disease states:
1. `Tomato___healthy` (Healthy foliage)
2. `Tomato___Early_blight` (Alternaria solani infection)
3. `Tomato___Late_blight` (Phytophthora infestans infection)

---

### Submission Deliverables
- **Completed Submission Document (Word)**: [`AgriVision_Deep_Learning_Assignment_Answers_Completed.docx`](./AgriVision_Deep_Learning_Assignment_Answers_Completed.docx)
- **Compiled PDF Submission Deliverable**: [`AgriVision_Deep_Learning_Assignment_Answers_Completed.pdf`](./AgriVision_Deep_Learning_Assignment_Answers_Completed.pdf)

---

### Empirical Highlights & Benchmark Summary
- **PCA Elbow Selection**: $k = 128$ components preserves **88.88%** of the empirical variance while achieving $32\times$ dimensionality reduction ($4,096 \to 128$) and peak validation Macro-F1 of **0.6721**.
- **Model Comparison**:
  - Raw Pixel Random Forest achieved the highest classical baseline accuracy (**86.22%**, Macro-F1: 0.8499).
  - PCA-reduced Logistic Regression provided ultra-fast training (**0.026s**, $0.002$ ms latency, $2$ KB binary).
- **Optimization Dynamics**: Mini-Batch SGD ($\eta=0.01$, batch size 64) outperformed full-batch GD variants, reaching minimum validation loss (**0.7816**) in just 52 epochs.
- **Mobile Design Challenge**: A compact quantized 3-layer CNN achieved **0.7661 Macro-F1** with **0.80 ms latency** and a **160 KB binary**, easily meeting all edge deployment constraints.
