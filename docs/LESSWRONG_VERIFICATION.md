# LessWrong Post Verification Notes

**Post:** "Why RAG Hallucinations Start Before Retrieval"  
**Author:** Francesco Marinoni Moretto  
**Last Updated:** January 2026

This document provides source verification for claims made in the accompanying LessWrong post. Each externally verifiable claim is mapped to exact page numbers, sections, and quotes where possible.

---

## Collins, Augenstein & Riedel (2017)

**Citation:** Collins, E., Augenstein, I., & Riedel, S. (2017). "A Supervised Approach to Extractive Summarisation of Scientific Papers." CoNLL 2017.

**Source:** https://aclanthology.org/K17-1021.pdf

**Claim:** "In a manual analysis of 100 misclassified sentences, they found 37 were mislabeled training examples."

**Verification (Page 6, Section 5.2):**
> "We manually analyse 100 misclassified sentences, 50 false positives and 50 false negatives."
> "37 are mislabelled examples"

**Claim:** "Among false positives, common causes were lack of context... and long-range dependencies like references to figures described elsewhere."

**Verification (Page 6):**
> "The most common forms of false positive error we find in the corpus are due to sentences that require some form of context to be understood... This context might be in the form of the preceding sentence or in the case of the second example, information regarding the content of Figure 1 which is described elsewhere in the paper."

---

## DYNAMICQA (2024)

**Citation:** Marjanović, S.V., Yu, P., Atanasova, P., Maistro, M., Lioma, C., & Augenstein, I. (2024). "DYNAMICQA: Tracing Internal Knowledge Conflicts in Language Models." arXiv:2407.17023

**Source:** https://arxiv.org/abs/2407.17023

**Claim:** "Models were stubborn (refusing to update despite correct context) 6.16% of the time for static facts, but 9.38% for temporal and 9.36% for disputable facts."

**Verification (Table 1, Page 5):**

| Fact Type | Stubborn % |
|-----------|------------|
| Static | 6.16% |
| Temporal | 9.38% |
| Disputable | 9.36% |

**Definition (Section 3.2):**
> "Stubborn: The model sticks to the old answer despite the context containing evidence for the new answer"

**Claim:** "other approaches to update model knowledge than retrieval-augmentation should be explored for domains with low certainty of facts."

**Verification (Section 7, Page 9 - exact quote):**
> "This suggests that other approaches to update model knowledge than retrieval-augmentation should be explored for domains with low certainty of facts"

---

## Sufficient Context (2025)

**Citation:** Joren, H., et al. (2025). "Sufficient Context: A New Lens on Retrieval Augmented Generation Systems." ICLR 2025. arXiv:2411.06037

**Source:** https://arxiv.org/abs/2411.06037

**Claim:** "Without RAG, Gemini 1.5 Pro abstained on 100% of uncertain questions; with RAG, that dropped to 18.6%."

**Verification (Section 4.2, Pages 6-7):**
The paper measures abstention rate - how often models refuse to answer when context is insufficient. Key finding:
- Without any context: Gemini 1.5 Pro abstains on ~100% of unanswerable questions
- With insufficient context provided: Abstention drops to 18.6%

---

## RefusalBench (2025)

**Citation:** Muhamed, A., et al. (2025). "RefusalBench: Measuring Selective Refusal in RAG." arXiv:2510.10390

**Source:** https://arxiv.org/abs/2510.10390

**Claim:** "Even with frontier models, refusal accuracy drops below 50% on multi-document tasks."

**Verification (Abstract):**
> "Our large-scale study reveals that even frontier models struggle in this setting, with refusal accuracy dropping below 50% on multi-document tasks"

**Verification (Section 4.2):**
> "Even the best model on RefusalBench-GaRAGe (DeepSeek-R1) achieves only 47.4% refusal accuracy"

---

## Ritchie & Kempes (2024)

**Citation:** Ritchie, M.E. & Kempes, C.P. (2024). "Metabolic scaling in small life forms." arXiv:2403.00001

**Source:** https://arxiv.org/abs/2403.00001

**Claim:** "The parameter β for prokaryotes appears as 0.33, 0.73, and 1.68 - all correct, but for different scaling regimes. Some explanations are nearby, others are fourteen pages away in supplementary material."

**Verification:**

**β = 1.68 (Page 5):**
> "For cell sizes up to about the volume of E. coli (≈ 10⁻¹⁸ m³) the power law approximation is superlinear (SI Figure 4) with an approximate exponent of 1.68"

**β = 0.73 (Page 5):**
> "For larger bacteria, the scaling of B converges on the sublinear scaling of 11/15 = 0.73"

**β = 0.33 (Page 5 figure + Page 19 derivation):**
- Figure 2 (Page 5): Shows β = 1/3 as dashed red curve label
- Page 19 (Supplementary): "Here enzyme concentration will scale like Z ∝ V⁻²/³ and B ∝ V^(1/3)"

**Distance:** Page 5 to Page 19 = 14 pages

---

## Tools Referenced

| Tool | Category | Source |
|------|----------|--------|
| UnScientify | Uncertainty detection | arXiv:2307.14236 |
| RAGAS | Post-retrieval RAG evaluation | ragas.io |
| TruLens | Post-retrieval RAG evaluation | trulens.org |
| Protecto.ai | Privacy/Security | protecto.ai |
| Adlib | Document accuracy | adlibsoftware.com |
| Self-RAG | Runtime reflection | arXiv:2310.11511 |

---

## "Why Language Models Hallucinate" (2025)

**Citation:** Kalai, A.T., Nachum, O., Vempala, S.S., & Zhang, E. (2025). "Why Language Models Hallucinate." arXiv:2509.04664

**Source:** https://arxiv.org/abs/2509.04664

**Authors:** OpenAI (Kalai, Nachum, Zhang) + Georgia Tech (Vempala)

**Relevance:** Theoretical analysis of why hallucinations persist through post-training. Complements Clarity Gate's focus on document quality as an upstream cause.

**Key findings:**

1. **Evaluation incentives cause hallucinations to persist:**
> "Language models hallucinate because the training and evaluation procedures reward guessing over acknowledging uncertainty"

2. **Binary grading penalizes abstention (Table 2):**
Analysis of 10 major benchmarks (GPQA, MMLU-Pro, SWE-bench, etc.) shows virtually all use binary scoring where IDK receives zero credit.

3. **Mathematical relationship:**
> "(generative error rate) ≳ 2 × (IIV misclassification rate)"

4. **Proposed solution:** Explicit confidence thresholds in evaluation prompts:
> "Answer only if you are >t confident, since mistakes are penalized t/(1-t) points, while correct answers receive 1 point, and an answer of 'I don't know' receives 0 points."

**Connection to Clarity Gate:**
- Their work: Evaluations reward guessing → models don't abstain
- Our work: Documents hide uncertainty → models can't tell when to abstain
- Both address upstream factors before retrieval/generation

**Inline citation in post:** "Confident plausible falsehoods" is what I started calling them (related to what Kalai et al. term "plausible falsehoods"[^6])...

**Footnote [^6]:** Kalai, Nachum, Vempala & Zhang (2025), "Why Language Models Hallucinate," arXiv:2509.04664. They define hallucinations as "plausible falsehoods" and prove mathematically that calibrated language models will inevitably produce them.

---

## Methodology

This verification document was created by:
1. Retrieving each cited paper
2. Locating exact page/section/table for each claim
3. Extracting direct quotes where possible
4. Cross-checking numerical values against source tables

For questions or corrections: [open an issue](https://github.com/frmoretto/clarity-gate/issues)
