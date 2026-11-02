# tryness-dissertation

Study: *The impact of social media advertising on buying decisions for mobile phone bundles among MUBAS students.*

## Contents

| File | What it is |
| --- | --- |
| `The Impact of Social Media Advertising ... Questionnaire.csv` | Quantitative data: 119 Google Forms responses to 39 closed questions (demographics, social media use, 20 Likert items, purchase behaviour). |
| `Isaiah and Tryness Interview Guide.docx` | Qualitative instrument: semi-structured guide, 18 questions in six sections, with probes. |
| `MUBAS_Mobile_Bundle_Interview_Database.xlsx` | Interview transcript database: the same 119 respondents, each with a filled 18-question transcript that follows their own survey answers. Nine working sheets plus a read-me. |
| `scripts/` | The generator that builds the workbook from the CSV (reproducible). |

## The Excel database

`MUBAS_Mobile_Bundle_Interview_Database.xlsx`

| Sheet | Contents |
| --- | --- |
| `00 Read Me` | Purpose, sources, method, sheet guide, coding frame, data-status notice. |
| `01 Interview Guide` | The 18 questions, sections and probes as a reusable instrument. |
| `02 Respondent Register` | 119 rows: fieldwork log, demographics, full survey profile, completeness, words, codes applied. |
| `03 Transcripts (Wide)` | 119 rows × 18 answer columns — the reading copy. |
| `04 Transcripts (Long)` | 2,142 rows (respondent × question) for NVivo / ATLAS.ti / MAXQDA / R. |
| `05 Coding Matrix` | Binary code presence per respondent with theme totals. |
| `06 Codebook` | 45 codes in 11 themes: definition, frequency, illustrative extract. |
| `07 Theme Frequency` | Code frequencies overall and by gender, purchase behaviour, influence rating. |
| `08 Flow Validation` | Survey marginal vs matching qualitative code share, with the gap in points. |
| `09 Survey Source Data` | The original 119 × 39 responses, keyed to Resp ID. |

**Important:** the transcripts are *synthesised* from the closed-ended survey file
so that the qualitative strand carries the same respondents, proportions and
story as the quantitative strand. They are not recordings of real people. Do not
present them as primary fieldwork or quote them as authentic participants. They
are intended for instrument testing, codebook development, analysis-pipeline
rehearsal, teaching, or as a template that real transcripts can replace
respondent-for-respondent once fieldwork is complete.

## Rebuilding the workbook

```bash
python -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt
.venv/bin/python scripts/build_interview_database.py
```

The generator is deterministic: the same CSV always produces the same workbook.

## Quality assurance

```bash
.venv/bin/python scripts/qa_interview_database.py
```

The harness re-reads the generated workbook and fails (exit code 1) on any
blocking issue: blank or over-short answers, missing facts that the respondent's
survey row asserts (age, network, platform, channel, factor, rating), answers that
contradict that row, duplicate answers, and code distributions that drift more
than 10 points from the survey marginal. It also reports repeated 10-word runs per
question as an editorial signal. Current status: **PASS — 0 blocking, 0 major,
0 minor** across 2,142 answers, 45 codes and 11 themes.
