# BPE Tokenizer Experimentation

## Overview
This repository contains my personal experiments in building a **Byte Pair Encoding (BPE)** tokenizer from scratch. The goal of this project was to move beyond the theory and understand exactly how modern LLM tokenizers process text, handle different languages, and manage vocabulary efficiency.

Experiments were conducted using Wikipedia datasets in four languages: **English, Hindi, Spanish, and Telugu.**

---

## Experiment 1: The Raw Corpus Approach
In this baseline experiment, I trained the BPE algorithm directly on the raw text corpus without pre-tokenization.

### Results
* **English:** 0.892 (Fertility)
* **Hindi:** 1.188 (Fertility)
* **Spanish:** 1.448 (Fertility)
* **Telugu:** 2.395 (Fertility)

### Why this approach was suboptimal
When inspecting the resulting vocabulary, I encountered entries like:
* `8497`: "Congress emerged "
* `8498`: "Congress emerged as the "
* `8499`: "Congress emerged as the largest "
* `8500`: "Congress emerged as the largest single "
* `8501`: "Congress emerged as the largest single part"

**Why is this bad?**
This is a classic case of **over-memorization**. Because the BPE algorithm saw these sequences repeated frequently in the specific training corpus, it treated them as distinct tokens. This is highly inefficient for two reasons:
1.  **Poor Generalization:** These long tokens are unlikely to appear in the exact same sequence in new data. They become "dead" weight in the vocabulary.
2.  **Vocabulary Bloat:** The model is wasting its limited vocabulary space on long, specific phrases rather than breaking words down into reusable sub-word units (like morphemes). A good tokenizer should decompose "Congress" and "emerged" rather than stitching them together into a singular, brittle token.

---

## Experiment 2: The GPT-Style Regex Approach
To improve the quality, I implemented a pre-tokenization step using a GPT-style regex pattern to enforce logical word boundaries and structure the data before running BPE.

**Key Changes:**
* **Pre-tokenization:** Used a standard regex pattern to segment text before training.
* **Space Handling:** Forced a space before words, not at the end.
* **Isolation:** Treated words as separate units during the initial processing phase, preventing the BPE algorithm from merging across word boundaries arbitrarily.

### Results
| Language | Experiment 1 (Raw) | Experiment 2 (Regex) |
| :--- | :--- | :--- |
| **English** | 0.892 | 1.270 |
| **Hindi** | 1.188 | 1.549 |
| **Spanish** | 1.448 | 1.350 |
| **Telugu** | 2.395 | 1.933 |

---

## Conclusion
This experiment proved that the "intelligence" of a tokenizer is not solely derived from the BPE merge algorithm itself, but from the **pre-tokenization strategy** that precedes it. 

By applying Regex-based boundaries, I prevented the BPE algorithm from "hallucinating" phrases and forced it to learn a more robust, composition-based representation of the languages. This transition from blindly merging characters to logically segmenting text is the fundamental "secret sauce" behind modern LLM tokenizers. While these results were derived from a small sample size, the exercise effectively demystified the transition from raw text to a meaningful, efficient vocabulary.

---

## Disclaimer
*This project is a personal educational experiment. The vocabulary and fertility scores are based solely on four Wikipedia pages and are not representative of production-grade tokenizers. The goal was to build the logic from scratch to gain an intuitive understanding of the underlying mechanics.*
