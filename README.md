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
```

---

## How to run

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```
### 2. Configure Environment Variables

Add API key in .env(Groq)

### 3. Run

```bash
python main.py
```
The default domains are:
```text
postman.com
supabase.com
vapi.ai
```

### For custom Domain run:

```bash
python main.py Domain_name
```

### Results are saved to: 
```text
output/results.json
```

---

## Error Handling

The application is designed so that a failure for one domain does **not stop the entire batch**.

The following errors are handled:

- Invalid or empty domains.
- Browser and page-loading failures.
- Website scraping failures.
- Groq API request failures.
- Empty LLM responses.
- Invalid JSON returned by the LLM.
- LLM responses that fail Pydantic schema validation.

If a domain fails during enrichment, the error is logged and the pipeline returns `None` for that domain, allowing the remaining domains to continue processing.



