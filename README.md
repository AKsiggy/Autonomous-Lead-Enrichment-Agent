# Autonomous Company Lead Enrichment Agent

An automated **B2B lead enrichment agent** that crawls public company websites, extracts relevant business information, and uses an LLM to generate structured company intelligence.

The project uses **Selenium**, **BeautifulSoup**, **Groq**, and **Pydantic** to provide an end-to-end enrichment pipeline.

---

## Overview

The application follows this workflow:

```text
Company Domain
      ↓
Selenium Web Crawler
      ↓
Internal Page Discovery
      ↓
Text + Email + LinkedIn Extraction
      ↓
Context Builder
      ↓
Groq LLM
      ↓
Pydantic Validation
      ↓
JSON Output
