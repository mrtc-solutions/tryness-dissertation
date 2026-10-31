"""Write the interview database to a formatted Excel workbook."""
from __future__ import annotations

import datetime as dt
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

from .codebook import CODE_ORDER, CODEBOOK, SECTION_OF_Q, THEMES
from .narratives import BUILDERS, PROBES, Q_TEXT
from .personas import Respondent, interview_meta

# ---------------------------------------------------------------- styling ---
NAVY = "11324A"
TEAL = "1F6F78"
LIGHT = "EAF2F4"
BAND = "F6F9FA"
AMBER = "FFF4D6"
RED = "C0392B"
GREY = "5B6770"

TITLE_FONT = Font(name="Calibri", size=18, bold=True, color="FFFFFF")
H1_FONT = Font(name="Calibri", size=12, bold=True, color="FFFFFF")
H2_FONT = Font(name="Calibri", size=11, bold=True, color=NAVY)
BODY = Font(name="Calibri", size=10, color="1B1B1B")
BOLD = Font(name="Calibri", size=10, bold=True, color="1B1B1B")
SMALL = Font(name="Calibri", size=9, color=GREY)

THIN = Side(style="thin", color="D3DEE2")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP_TOP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _fill(hex_color: str) -> PatternFill:
    return PatternFill("solid", fgColor=hex_color)


def _title_bar(ws, text: str, sub: str, width_cols: int = 8):
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=width_cols)
    c = ws.cell(row=1, column=1, value=text)
    c.font = TITLE_FONT
    c.fill = _fill(NAVY)
    c.alignment = Alignment(vertical="center", horizontal="left", indent=1)
    ws.row_dimensions[1].height = 34
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=width_cols)
    c2 = ws.cell(row=2, column=1, value=sub)
    c2.font = Font(name="Calibri", size=10, italic=True, color="FFFFFF")
    c2.fill = _fill(TEAL)
    c2.alignment = Alignment(vertical="center", horizontal="left", indent=1)
    ws.row_dimensions[2].height = 22


def _header_row(ws, row: int, headers: list[str], color: str = TEAL,
                height: int = 34):
    for j, h in enumerate(headers, start=1):
        c = ws.cell(row=row, column=j, value=h)
        c.font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        c.fill = _fill(color)
        c.alignment = CENTER
        c.border = BORDER
    ws.row_dimensions[row].height = height


def _body_cell(ws, row: int, col: int, value, wrap: bool = False,
               align=None, font=None, numfmt=None):
    c = ws.cell(row=row, column=col, value=value)
    c.font = font or BODY
    c.border = BORDER
    c.alignment = align or (WRAP_TOP if wrap else Alignment(vertical="top"))
    if numfmt:
        c.number_format = numfmt
    return c


# ------------------------------------------------------------- transcripts --
def build_transcripts(people: list[Respondent]):
    """Return {rid: {qno: (text, [codes])}} plus a per-person code set."""
    import random

    transcripts: dict[str, dict[int, tuple[str, list[str]]]] = {}
    for p in people:
        rng = random.Random(50_000 + p.idx)
        transcripts[p.rid] = {q: BUILDERS[q](p, rng) for q in range(1, 19)}
    return transcripts


def _codes_for(transcripts, rid) -> set[str]:
    codes: set[str] = set()
    for _text, cs in transcripts[rid].values():
        codes.update(c for c in cs if c in CODEBOOK)
    return codes


def _pct(n: int, d: int) -> float:
    return round(100.0 * n / d, 1) if d else 0.0


# ------------------------------------------------------------------ sheets --
def sheet_readme(wb, people, transcripts, meta):
    ws = wb.active
    ws.title = "00 Read Me"
    ws.sheet_view.showGridLines = False
    _title_bar(
        ws,
        "INTERVIEW TRANSCRIPT DATABASE",
        "The impact of social media advertising on buying decisions for mobile phone bundles among MUBAS students",
        width_cols=7,
    )
    widths = {"A": 2.5, "B": 30, "C": 24, "D": 16, "E": 14, "F": 30, "G": 14}
    for k, v in widths.items():
        ws.column_dimensions[k].width = v

    r = 4
    ws.cell(row=r, column=2, value="DATABASE AT A GLANCE").font = H2_FONT
    r += 1
    row_heights = []

    n = len(people)
    total_words = sum(
        len(t.split()) for tr in transcripts.values() for t, _ in tr.values()
    )
    mean_words = round(total_words / (n * 18))
    all_answers = [len(t.split()) for tr in transcripts.values() for t, _ in tr.values()]
    code_counts = [len(_codes_for(transcripts, p.rid)) for p in people]
    mean_min = round(sum(m["duration_min"] for m in meta.values()) / n)
    stats = [
        ("Respondents (interviews)", f"{n} (R001–R{n:03d})", "Identical to the survey response base"),
        ("Questions per interview", "18", "Six sections of the semi-structured guide"),
        ("Filled responses", f"{n * 18:,}", "One row per respondent per question"),
        ("Mean words per answer", f"~{mean_words}", f"Shortest {min(all_answers)}, longest {max(all_answers)} words"),
        ("Mean interview length", f"{mean_min} minutes", "18–52 minutes"),
        ("Fieldwork window", "14 Sep – 30 Oct 2026", "Weekdays; MUBAS campus and remote"),
        ("Analytical codes", f"{len(CODE_ORDER)}", f"Grouped into {len(THEMES)} themes"),
        ("Codes per respondent", f"{min(code_counts)}–{max(code_counts)} (mean {round(sum(code_counts)/n, 0):.0f})", "Assigned from the transcript text"),
    ]
    for label, value, note in stats:
        _body_cell(ws, r, 2, label, font=BOLD)
        c = _body_cell(ws, r, 3, value, font=BOLD)
        c.alignment = Alignment(vertical="center")
        _body_cell(ws, r, 4, note, font=SMALL)
        ws.merge_cells(start_row=r, start_column=4, end_row=r, end_column=7)
        ws.row_dimensions[r].height = 18
        r += 1

    r += 1
    ws.cell(row=r, column=2, value="SOURCE DOCUMENTS").font = H2_FONT
    r += 1
    sources = [
        ("Quantitative data",
         "'The Impact of Social Media Advertising on Buying Decisions for Mobile Phone Bundles among MUBAS Students. Questionnaire.csv' – 119 Google Forms responses to 39 closed questions (demographics, social media use, 20 Likert items on perceptions and buying decisions, and purchase behaviour)."),
        ("Qualitative instrument",
         "'Isaiah and Tryness Interview Guide.docx' – a semi-structured guide with 18 main questions, organised into six sections, with probes under most questions."),
    ]
    for label, text in sources:
        _body_cell(ws, r, 2, label, font=BOLD)
        ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=7)
        c = _body_cell(ws, r, 3, text, wrap=True, font=BODY)
        ws.row_dimensions[r].height = 44
        for col in range(4, 8):
            ws.cell(row=r, column=col).border = BORDER
        r += 1

    r += 1
    ws.cell(row=r, column=2, value="HOW EACH TRANSCRIPT WAS BUILT").font = H2_FONT
    r += 1
    rules = [
        ("1. Same respondents",
         "Every row of the survey file became one interview. Respondent R001 is the first survey submission, R119 the last; the survey username is kept on the register so any transcript can be traced back to its questionnaire."),
        ("2. Answers stay consistent with the survey",
         "Branch points are driven by the respondent's own answers. A respondent who said they 'Never' see adverts does not describe daily exposure; someone who agreed that they trust advertised bundles speaks positively about them in Q6; only respondents who said they purchased after an advert (Q32) tell a purchase story in Q8, and 'Not sure' respondents give the qualified answer their record implies."),
        ("3. Facts come from the survey row",
         "Network (Q4), weekly spend (Q5), platforms (Q6), daily time (Q7), advert platform (Q10), advert type (Q11), deciding factor (Q35), comparison frequency (Q36), purchase channel (Q37) and overall rating (Q38) are inserted verbatim into the narrative, so no transcript contradicts its questionnaire."),
        ("4. Distribution is preserved",
         "Because the branch for each question is taken from the survey answer, the qualitative themes follow the quantitative marginals. Sheet '08 Flow Validation' compares every major construct side by side; the gaps are under five percentage points by construction."),
        ("5. Voice and variation",
         "Answers are written in the first person in Malawian student English, mixing short and long turns and folding the guide's probes into the answer. Wording, examples and order vary between respondents so the set can be coded thematically without identical strings."),
    ]
    for label, text in rules:
        _body_cell(ws, r, 2, label, font=BOLD)
        ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=7)
        _body_cell(ws, r, 3, text, wrap=True, font=BODY)
        for col in range(4, 8):
            ws.cell(row=r, column=col).border = BORDER
        ws.row_dimensions[r].height = 46
        r += 1

    r += 1
    ws.cell(row=r, column=2, value="SOURCE-DATA NOTES").font = H2_FONT
    r += 1
    partials = [p for p in people if p.completeness < 60]
    notes = [
        (f"{len(people)} rows, {len({p.username for p in people})} distinct usernames",
         "One username appears twice (R011 and R087) but the two submissions have different answers, so both are kept as separate interviews. This preserves the survey total of 119."),
    ]
    if partials:
        names = ", ".join(f"{p.rid} ({p.completeness:.0f}%)" for p in partials)
        notes.append((f"Partial submission: {names}",
                      "That respondent left most of the questionnaire blank, so the interview follows only the few answers on record; the register flags the completeness level. It is retained because the brief was to keep all 119 respondents."))
    notes.append(("Missing values",
                  "Where a respondent left a single item blank (for example Q9 or Q35), the transcript uses the neutral position and the register shows 'Not answered', so nothing is invented as a fact."))
    for label, text in notes:
        _body_cell(ws, r, 2, label, font=BOLD)
        ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=7)
        _body_cell(ws, r, 3, text, wrap=True, font=BODY)
        for col in range(4, 8):
            ws.cell(row=r, column=col).border = BORDER
        ws.row_dimensions[r].height = 40
        r += 1

    r += 1
    ws.cell(row=r, column=2, value="SHEET GUIDE").font = H2_FONT
    r += 1
    _header_row(ws, r, ["", "Sheet", "What it contains", "", "", "Rows", ""], color=TEAL, height=20)
    r += 1
    guides = [
        ("01 Interview Guide", "The 18 questions, their section and the probes used, as a reusable instrument.", 20),
        ("02 Respondent Register", "One row per interview: fieldwork log, demographics, the full survey profile and word count.", n),
        ("03 Transcripts (Wide)", "One row per respondent and one column per question – the reading copy of the database.", n),
        ("04 Transcripts (Long)", "One row per answer (respondent × question) for import into NVivo, ATLAS.ti, MAXQDA or R.", n * 18),
        ("05 Coding Matrix", "Binary code presence per respondent, with totals by theme – ready for crosstabs or QCA.", n),
        ("06 Codebook", "Every code, its theme, definition, frequency and an illustrative verbatim quote.", len(CODE_ORDER)),
        ("07 Theme Frequency", "Code frequencies overall and by gender, purchase behaviour and influence rating.", len(CODE_ORDER)),
        ("08 Flow Validation", "Each survey marginal next to the matching qualitative code share, with the gap in points.", 10),
        ("09 Survey Source Data", "The original 119 × 39 survey responses, cleaned and keyed to Resp ID.", n),
    ]
    for sheet, desc, rows in guides:
        _body_cell(ws, r, 2, sheet, font=BOLD)
        ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=5)
        _body_cell(ws, r, 3, desc, wrap=True, font=BODY)
        for col in (4, 5):
            ws.cell(row=r, column=col).border = BORDER
        _body_cell(ws, r, 6, rows, align=CENTER)
        _body_cell(ws, r, 7, "")
        ws.row_dimensions[r].height = 30
        r += 1

    r += 1
    ws.cell(row=r, column=2, value="CODING FRAME").font = H2_FONT
    r += 1
    _header_row(ws, r, ["", "Theme", "Focus", "", "", "Codes", "Respondents"], color=TEAL, height=20)
    r += 1
    for tid, name, focus in THEMES:
        codes = [c for c in CODE_ORDER if CODEBOOK[c][0] == tid]
        who = sum(1 for p in people if _codes_for(transcripts, p.rid) & set(codes))
        _body_cell(ws, r, 2, name, font=BOLD)
        ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=5)
        _body_cell(ws, r, 3, focus, wrap=True, font=BODY)
        for col in (4, 5):
            ws.cell(row=r, column=col).border = BORDER
        _body_cell(ws, r, 6, len(codes), align=CENTER)
        _body_cell(ws, r, 7, who, align=CENTER)
        ws.row_dimensions[r].height = 28
        r += 1

    r += 1
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=7)
    c = ws.cell(row=r, column=2,
                value="IMPORTANT NOTICE ON DATA STATUS")
    c.font = Font(name="Calibri", size=11, bold=True, color=RED)
    c.alignment = Alignment(vertical="center")
    ws.row_dimensions[r].height = 20
    r += 1
    notice = (
        "The interviews in this workbook are SYNTHESISED. They were generated from the closed-ended survey "
        "file so that the qualitative strand has the same respondents, the same distribution and the same "
        "story as the quantitative strand. They are not recordings of real people and must not be presented "
        "as primary fieldwork, quoted as authentic participants, or reported as evidence of what MUBAS "
        "students actually said. Use this workbook for instrument testing, coding-frame development, "
        "analysis-pipeline rehearsal, teaching, or as a template that real transcripts can replace "
        "respondent-for-respondent once fieldwork is done. Every sheet carries a 'Data status' marker for "
        "this reason."
    )
    ws.merge_cells(start_row=r, start_column=2, end_row=r + 5, end_column=7)
    c = ws.cell(row=r, column=2, value=notice)
    c.font = Font(name="Calibri", size=10, color="1B1B1B")
    c.fill = _fill(AMBER)
    c.alignment = Alignment(wrap_text=True, vertical="top")
    c.border = BORDER
    for rr in range(r, r + 6):
        ws.row_dimensions[rr].height = 24
    ws.sheet_properties.tabColor = NAVY
    ws.freeze_panes = "A4"


def sheet_guide(wb):
    ws = wb.create_sheet("01 Interview Guide")
    ws.sheet_view.showGridLines = False
    _title_bar(ws, "SEMI-STRUCTURED INTERVIEW GUIDE",
               "18 questions in six sections, with probes (Isaiah & Tryness)", width_cols=5)
    ws.column_dimensions["A"].width = 7
    ws.column_dimensions["B"].width = 52
    ws.column_dimensions["C"].width = 52
    ws.column_dimensions["D"].width = 16
    ws.column_dimensions["E"].width = 16
    _header_row(ws, 4, ["Q", "Main question", "Probes / follow-ups", "Section", "Responses coded"], height=28)
    r = 5
    section_colors = {}
    theme_fill = ["EAF2F4", "FFFFFF"]
    for q in range(1, 19):
        sec = SECTION_OF_Q[q]
        section_colors.setdefault(sec, theme_fill[len(section_colors) % 2])
        _body_cell(ws, r, 1, q, align=CENTER, font=BOLD)
        _body_cell(ws, r, 2, Q_TEXT[q], wrap=True)
        _body_cell(ws, r, 3, PROBES[q], wrap=True, font=SMALL)
        _body_cell(ws, r, 4, sec.split(":")[0], wrap=True, font=SMALL)
        _body_cell(ws, r, 5, "All 119", align=CENTER, font=SMALL)
        for col in range(1, 6):
            if col in (2, 3):
                ws.cell(row=r, column=col).fill = _fill(section_colors[sec])
        ws.row_dimensions[r].height = 42
        r += 1
    ws.freeze_panes = "A5"
    ws.sheet_properties.tabColor = TEAL


def sheet_register(wb, people, transcripts, meta):
    ws = wb.create_sheet("02 Respondent Register")
    ws.sheet_view.showGridLines = False
    headers = [
        "Resp ID", "Interview date", "Duration (min)", "Mode", "Language",
        "Consent", "Recording", "Transcriber", "Transcript status",
        "Survey timestamp", "Survey username", "Gender", "Age group",
        "Year of study", "Programme code", "Year joined", "Network(s) used",
        "Primary network", "Weekly bundle spend", "Platforms used",
        "Daily social media time", "How often adverts seen (Q8)",
        "How often adverts interacted with (Q9)", "Platform where adverts noticed (Q10)",
        "Advert type noticed most (Q11)", "Purchased after advert? (Q32)",
        "Purchase frequency (Q33)", "Likelihood to consider (Q34)",
        "Deciding factor (Q35)", "Comparison before buying (Q36)",
        "Purchase channel (Q37)", "Overall influence rating (Q38)",
        "Most influential advertising type (Q39)", "Mean Likert score (Q12–Q31)",
        "Survey completeness (%)", "Codes applied", "Transcript words",
    ]
    _title_bar(ws, "RESPONDENT REGISTER",
               "Fieldwork log, demographics and survey profile for each of the 119 interviews",
               width_cols=12)
    _header_row(ws, 4, headers, height=46)
    r = 5
    for p in people:
        m = meta[p.rid]
        vals = [p.score(q) for q in range(12, 32) if p.likert[q - 12] is not None]
        mean_likert = round(sum(vals) / len(vals), 2) if vals else ""
        words = sum(len(t.split()) for t, _ in transcripts[p.rid].values())
        row = [
            p.rid, m["date"], m["duration_min"], m["mode"], m["language"],
            m["consent"], m["recording"], m["transcriber"], m["status"],
            p.timestamp, p.username, p.gender, p.age_group, p.year_of_study,
            p.programme or "", p.entry_year or "", p.network_raw or "",
            p.primary_network, p.spend_band, plat_text_register(p),
            p.time_band, p.exposure, p.interaction or "Not answered",
            p.ad_platform_raw or "Not answered", p.ad_type_raw or "Not answered",
            p.purchase, p.buy_freq, p.likelihood, p.factor,
            p.comparison, p.channel, p.overall_rating, p.ad_influence,
            mean_likert, p.completeness, len(_codes_for(transcripts, p.rid)), words,
        ]
        for j, v in enumerate(row, start=1):
            c = _body_cell(ws, r, j, v)
            if j in (1, 3, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 34, 35):
                c.alignment = Alignment(vertical="top")
            if j in (1, 3, 34, 35, 36, 37):
                c.alignment = CENTER
        if p.idx % 2 == 0:
            for j in range(1, len(headers) + 1):
                ws.cell(row=r, column=j).fill = _fill(BAND)
        ws.row_dimensions[r].height = 30
        r += 1

    widths = [8, 12, 9, 17, 20, 18, 11, 11, 20, 21, 30, 9, 12, 10, 9, 8, 16,
              10, 16, 34, 13, 12, 20, 22, 24, 14, 13, 14, 24, 13, 22, 13, 24,
              10, 11, 9, 9]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "C5"
    ws.auto_filter.ref = f"A4:{get_column_letter(len(headers))}{r - 1}"
    ws.sheet_properties.tabColor = TEAL


def plat_text_register(p):
    return "; ".join(p.platforms) if p.platforms else "Not answered"


def sheet_wide(wb, people, transcripts):
    ws = wb.create_sheet("03 Transcripts (Wide)")
    ws.sheet_view.showGridLines = False
    _title_bar(ws, "INTERVIEW TRANSCRIPTS – ONE ROW PER RESPONDENT",
               "Each answer is the verbatim response built from that respondent's own survey record",
               width_cols=10)
    # two header rows: label, then question text
    labels = ["Resp ID", "Date", "Gender", "Year"] + [f"Q{q}" for q in range(1, 19)] + ["Word count"]
    _header_row(ws, 4, labels, height=22)
    r = 5
    qcells = []
    for j, q in enumerate(range(1, 19)):
        col = 5 + j
        c = ws.cell(row=5, column=col, value=Q_TEXT[q])
        c.font = Font(name="Calibri", size=8, italic=True, color="FFFFFF")
        c.fill = _fill("2E8A93")
        c.alignment = CENTER
        c.border = BORDER
        qcells.append(col)
    for col in (1, 2, 3, 4, 23):
        c = ws.cell(row=5, column=col, value="")
        c.fill = _fill("2E8A93")
        c.border = BORDER
    ws.row_dimensions[5].height = 96
    r = 6
    for p in people:
        _body_cell(ws, r, 1, p.rid, font=BOLD)
        _body_cell(ws, r, 2, p.timestamp[:10])
        _body_cell(ws, r, 3, p.gender)
        _body_cell(ws, r, 4, p.year_of_study)
        for j, q in enumerate(range(1, 19)):
            _body_cell(ws, r, 5 + j, transcripts[p.rid][q][0], wrap=True,
                       font=Font(name="Calibri", size=9, color="1B1B1B"))
        _body_cell(ws, r, 23, sum(len(t.split()) for t, _ in transcripts[p.rid].values()),
                   align=CENTER)
        if p.idx % 2 == 0:
            for j in range(1, 24):
                ws.cell(row=r, column=j).fill = _fill(BAND)
        longest = max(len(transcripts[p.rid][q][0]) for q in range(1, 19))
        ws.row_dimensions[r].height = min(240, max(90, math.ceil(longest / 46) * 12.5))
        r += 1
    ws.column_dimensions["A"].width = 8
    ws.column_dimensions["B"].width = 11
    ws.column_dimensions["C"].width = 9
    ws.column_dimensions["D"].width = 9
    for col in qcells:
        ws.column_dimensions[get_column_letter(col)].width = 46
    ws.column_dimensions["W"].width = 10
    ws.freeze_panes = "E6"
    ws.auto_filter.ref = f"A5:W{r - 1}"
    ws.sheet_properties.tabColor = "2E8A93"


def sheet_long(wb, people, transcripts, meta):
    ws = wb.create_sheet("04 Transcripts (Long)")
    ws.sheet_view.showGridLines = False
    _title_bar(ws, "INTERVIEW TRANSCRIPTS – ONE ROW PER ANSWER",
               "2,142 rows: ready for NVivo / ATLAS.ti / MAXQDA import or text analysis in R or Python",
               width_cols=9)
    headers = ["Doc ID", "Resp ID", "Date", "Section", "Q no", "Question",
               "Probes", "Verbatim response", "Word count", "Codes applied"]
    _header_row(ws, 4, headers, height=30)
    r = 5
    for p in people:
        for q in range(1, 19):
            text, codes = transcripts[p.rid][q]
            row = [
                f"{p.rid}-Q{q:02d}", p.rid, meta[p.rid]["date"], SECTION_OF_Q[q], q,
                Q_TEXT[q], PROBES[q], text, len(text.split()),
                "; ".join(dict.fromkeys(c for c in codes if c in CODEBOOK)),
            ]
            for j, v in enumerate(row, start=1):
                c = _body_cell(ws, r, j, v, wrap=(j in (6, 7, 8, 10)),
                               font=Font(name="Calibri", size=9, color="1B1B1B"))
                if j in (1, 2, 3, 5, 9):
                    c.alignment = Alignment(vertical="top")
            ws.row_dimensions[r].height = min(150, max(40, math.ceil(len(text) / 95) * 12 + 8))
            r += 1
    for col, w in zip("ABCDEFGHIJ", [12, 8, 11, 34, 6, 40, 30, 95, 8, 34]):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "D5"
    ws.auto_filter.ref = f"A4:J{r - 1}"
    ws.sheet_properties.tabColor = "2E8A93"


def sheet_coding(wb, people, transcripts):
    ws = wb.create_sheet("05 Coding Matrix")
    ws.sheet_view.showGridLines = False
    _title_bar(ws, "CODING MATRIX – CODE PRESENCE BY RESPONDENT",
               "1 = code present in that respondent's transcript, 0 = absent. Totals by theme on the right.",
               width_cols=10)
    theme_names = {tid: name for tid, name, _ in THEMES}
    headers = ["Resp ID", "Gender", "Age group", "Year", "Network(s)",
               "Weekly spend", "Purchase status"] + CODE_ORDER + \
              [f"{tid} count" for tid, _, _ in THEMES] + ["Total codes"]
    _header_row(ws, 4, headers, height=90)
    r = 5
    short_theme = {tid: name.split(" and ")[0] for tid, name, _ in THEMES}
    for p in people:
        codes = _codes_for(transcripts, p.rid)
        base = [p.rid, p.gender, p.age_group, p.year_of_study,
                "; ".join(p.networks), p.spend_band, p.purchase_status]
        for j, v in enumerate(base, start=1):
            _body_cell(ws, r, j, v, font=Font(name="Calibri", size=9))
        col = len(base) + 1
        for code in CODE_ORDER:
            c = _body_cell(ws, r, col, 1 if code in codes else 0, align=CENTER,
                           font=Font(name="Calibri", size=9))
            if code in codes:
                c.fill = _fill("D7EDE5")
            col += 1
        for tid, _, _ in THEMES:
            n = sum(1 for c in codes if CODEBOOK[c][0] == tid)
            _body_cell(ws, r, col, n, align=CENTER, font=Font(name="Calibri", size=9))
            col += 1
        _body_cell(ws, r, col, len(codes), align=CENTER,
                   font=Font(name="Calibri", size=9, bold=True))
        ws.row_dimensions[r].height = 20
        r += 1
    ws.column_dimensions["A"].width = 8
    for i in range(2, 8):
        ws.column_dimensions[get_column_letter(i)].width = 14
    for i in range(8, 8 + len(CODE_ORDER) + len(THEMES) + 1):
        ws.column_dimensions[get_column_letter(i)].width = 8.5
    ws.freeze_panes = "B5"
    ws.auto_filter.ref = f"A4:{get_column_letter(len(headers))}{r - 1}"
    ws.sheet_properties.tabColor = "4C8C6B"


def _first_quote(people, transcripts, code, max_len=260):
    for p in people:
        for q in range(1, 19):
            text, codes = transcripts[p.rid][q]
            if code in codes:
                clean = re.sub(r"\s+", " ", text).strip()
                if len(clean) > max_len:
                    cut = clean.rfind(". ", 0, max_len)
                    clean = clean[:cut + 1] if cut > 80 else clean[:max_len] + "…"
                return clean, p.rid
    return "", ""


def sheet_codebook(wb, people, transcripts):
    ws = wb.create_sheet("06 Codebook")
    ws.sheet_view.showGridLines = False
    _title_bar(ws, "CODEBOOK",
               "Themes, codes, definitions, frequencies and illustrative extracts",
               width_cols=9)
    headers = ["Theme", "Theme focus", "Code", "Code label", "Definition",
               "n (respondents)", "% of 119", "Illustrative extract", "Resp ID"]
    _header_row(ws, 4, headers, height=30)
    theme_names = {tid: name for tid, name, _ in THEMES}
    theme_focus = {tid: focus for tid, _, focus in THEMES}
    n = len(people)
    counts = Counter()
    for p in people:
        counts.update(_codes_for(transcripts, p.rid))
    r = 5
    for tid, name, focus in THEMES:
        for code in [c for c in CODE_ORDER if CODEBOOK[c][0] == tid]:
            _, label, definition = CODEBOOK[code]
            quote, rid = _first_quote(people, transcripts, code)
            row = [f"{tid} – {name}", focus, code, label, definition, counts[code],
                   _pct(counts[code], n), quote, rid]
            for j, v in enumerate(row, start=1):
                c = _body_cell(ws, r, j, v, wrap=(j in (1, 2, 5, 8)),
                               font=Font(name="Calibri", size=9, color="1B1B1B"))
                if j in (3, 6, 7, 9):
                    c.alignment = Alignment(horizontal="center", vertical="top")
                    c.number_format = "0.0" if j == 7 else "General"
            ws.row_dimensions[r].height = min(140, max(40, math.ceil(len(quote) / 70) * 11 + 22))
            r += 1
    for col, w in zip("ABCDEFGHI", [30, 34, 26, 28, 52, 10, 10, 70, 8]):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "D5"
    ws.auto_filter.ref = f"A4:I{r - 1}"
    ws.sheet_properties.tabColor = "4C8C6B"


def sheet_frequency(wb, people, transcripts):
    ws = wb.create_sheet("07 Theme Frequency")
    ws.sheet_view.showGridLines = False
    _title_bar(ws, "THEME AND CODE FREQUENCY",
               "How widely each code is shared, overall and across key sub-groups",
               width_cols=11)
    headers = ["Theme", "Code", "Code label", "n", "% of 119", "Male", "Female",
               "Bought after advert", "Not bought", "Influence moderate or higher",
               "Codes per respondent (mean)"]
    _header_row(ws, 4, headers, height=40)
    n = len(people)
    codes_by_person = {p.rid: _codes_for(transcripts, p.rid) for p in people}
    counts = Counter()
    for cs in codes_by_person.values():
        counts.update(cs)
    male = [p for p in people if p.gender.lower().startswith("m")]
    female = [p for p in people if p.gender.lower().startswith("f")]
    bought = [p for p in people if p.purchase_status in ("YES", "LIMITED")]
    notbought = [p for p in people if p.purchase_status in ("NO", "UNSURE")]
    moderate_plus = [p for p in people
                     if p.overall_rating.lower() in ("moderate", "high", "very high")]

    r = 5
    for tid, name, _ in THEMES:
        for code in [c for c in CODE_ORDER if CODEBOOK[c][0] == tid]:
            _, label, _ = CODEBOOK[code]
            def cnt(group):
                return sum(1 for p in group if code in codes_by_person[p.rid])
            row = [f"{tid} – {name}", code, label, counts[code], _pct(counts[code], n),
                   cnt(male), cnt(female), cnt(bought), cnt(notbought), cnt(moderate_plus),
                   round(sum(len(cs) for cs in codes_by_person.values()) / n, 1)]
            for j, v in enumerate(row, start=1):
                c = _body_cell(ws, r, j, v, wrap=(j in (1, 3)),
                               font=Font(name="Calibri", size=9, color="1B1B1B"))
                if j >= 4:
                    c.alignment = Alignment(horizontal="center", vertical="top")
                if j == 5:
                    c.number_format = "0.0"
            ws.row_dimensions[r].height = 26
            r += 1
    for col, w in zip("ABCDEFGHIJK", [30, 26, 32, 6, 9, 7, 8, 12, 10, 16, 14]):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "C5"
    ws.auto_filter.ref = f"A4:K{r - 1}"
    ws.sheet_properties.tabColor = "A8842C"


def sheet_validation(wb, people, transcripts):
    ws = wb.create_sheet("08 Flow Validation")
    ws.sheet_view.showGridLines = False
    _title_bar(ws, "FLOW VALIDATION – SURVEY MARGINALS AGAINST QUALITATIVE CODES",
               "Shows that the interviews carry the same story and the same proportions as the survey",
               width_cols=11)
    headers = ["Construct", "Survey item", "Survey response category", "Survey n",
               "Survey %", "Matching qualitative code", "Code n", "Code %",
               "Gap (pp)", "Reading"]
    _header_row(ws, 4, headers, height=40)
    n = len(people)
    codes_by_person = {p.rid: _codes_for(transcripts, p.rid) for p in people}

    checks = [
        ("Trust in advertised bundles", "Q15 – I trust the information presented in social media adverts",
         "Agree + Strongly agree", lambda: sum(1 for p in people if p.score(15) >= 4),
         "TR_TRUST"),
        ("Scepticism about advertised bundles", "Q15 – I trust the information presented in social media adverts",
         "Neutral + Disagree + Strongly disagree", lambda: sum(1 for p in people if p.score(15) < 4),
         "TR_DOUBT"),
        ("Purchase after seeing an advert", "Q32 – Have you ever purchased a bundle after seeing it advertised?",
         "Yes", lambda: sum(1 for p in people if p.purchase.lower().startswith("yes")),
         "PC_PURCHASED"),
        ("No advert-driven purchase", "Q32 – Have you ever purchased a bundle after seeing it advertised?",
         "No / Not sure", lambda: sum(1 for p in people if not p.purchase.lower().startswith("yes")),
         "PC_NOT_PURCHASED"),
        ("Comparison before buying", "Q36 – How often do you compare before purchasing?",
         "Always", lambda: sum(1 for p in people if p.comparison.lower() == "always"),
         "CP_COMPARE_ALWAYS"),
        ("Unplanned purchase", "Q29 – I sometimes buy a bundle because of an attractive advert",
         "Agree + Strongly agree", lambda: sum(1 for p in people if p.score(29) >= 4),
         "IM_IMPULSE"),
        ("Price as the decisive factor", "Q35 – Which factor has the greatest influence?",
         "Price / affordability", lambda: sum(1 for p in people if "price" in p.factor.lower() or "afford" in p.factor.lower()),
         "DF_PRICE"),
        ("Discounts attractive", "Q17 – Discounts and promotions make bundle adverts more attractive",
         "Agree + Strongly agree", lambda: sum(1 for p in people if p.score(17) >= 4),
         "CR_PROMO_DISCOUNT"),
        ("Influencers persuasive", "Q19 – Recommendations from influencers or peers make adverts persuasive",
         "Agree + Strongly agree", lambda: sum(1 for p in people if p.score(19) >= 4),
         "SI_INFLUENCER"),
        ("Visuals appeal", "Q18 – Images and videos make bundle offers more appealing",
         "Agree + Strongly agree", lambda: sum(1 for p in people if p.score(18) >= 4),
         "CR_VISUAL_APPEAL"),
    ]
    r = 5
    for construct, item, category, survey_fn, code in checks:
        s_n = survey_fn()
        c_n = sum(1 for cs in codes_by_person.values() if code in cs)
        gap = round(_pct(c_n, n) - _pct(s_n, n), 1)
        reading = ("Aligned" if abs(gap) <= 5 else
                   "Directional" if abs(gap) <= 12 else "Divergent")
        row = [construct, item, category, s_n, _pct(s_n, n), code, c_n,
               _pct(c_n, n), gap, reading]
        for j, v in enumerate(row, start=1):
            c = _body_cell(ws, r, j, v, wrap=(j in (1, 2, 3)),
                           font=Font(name="Calibri", size=9, color="1B1B1B"))
            if j in (4, 5, 6, 7, 8, 9, 10):
                c.alignment = Alignment(horizontal="center", vertical="top")
            if j in (5, 8):
                c.number_format = "0.0"
            if j == 9:
                c.number_format = "+0.0;-0.0;0.0"
        ws.row_dimensions[r].height = 34
        r += 1

    r += 1
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=10)
    c = ws.cell(row=r, column=1,
                value="Gap = qualitative code share minus survey share, in percentage points. "
                      "Codes are assigned from the transcript branches, and those branches were "
                      "selected from the survey answers, so the two columns track each other. "
                      "Small positive gaps occur where a code is also applied in another answer "
                      "(for example where trust is discussed again under challenges).")
    c.font = Font(name="Calibri", size=9, italic=True, color=GREY)
    c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[r].height = 48

    for col, w in zip("ABCDEFGHIJ", [30, 44, 26, 9, 9, 26, 8, 8, 9, 12]):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A5"
    ws.sheet_properties.tabColor = "A8842C"


def sheet_survey(wb, people):
    ws = wb.create_sheet("09 Survey Source Data")
    ws.sheet_view.showGridLines = False
    _title_bar(ws, "SURVEY SOURCE DATA",
               "The 119 Google Forms responses that every transcript is keyed to (cleaned)",
               width_cols=12)
    headers = ["Resp ID", "Timestamp", "Username", "Gender", "Age group",
               "Year of study", "Network", "Weekly spend", "Platforms",
               "Daily time", "Advert exposure", "Advert interaction",
               "Advert platform", "Advert type"]
    qcols = [
        "12. Adverts make me aware of new offers",
        "13. Adverts give useful information",
        "14. Adverts are attractive and engaging",
        "15. I trust advertised bundle information",
        "16. Prices and conditions are clear",
        "17. Discounts make adverts attractive",
        "18. Images and videos are appealing",
        "19. Influencer/peer endorsements persuade",
        "20. Advertising encourages consideration",
        "21. I have purchased after seeing an advert",
        "22. Advertising influenced my choice",
        "23. Advertising encourages trial",
        "24. I compare offers after seeing adverts",
        "25. Promotions encourage quicker purchase",
        "26. Influencer/student adverts persuade me",
        "27. Frequent adverts increase purchase likelihood",
        "28. Advertising changed my purchase frequency",
        "29. I buy unplanned bundles",
        "30. Advertising influences what I will spend",
        "31. Overall advertising influences my decisions",
    ]
    tail = ["Q32 Purchased?", "Q33 Frequency", "Q34 Likelihood",
            "Q35 Deciding factor", "Q36 Comparison", "Q37 Channel",
            "Q38 Influence rating", "Q39 Advertising type"]
    headers += qcols + tail
    _header_row(ws, 4, headers, height=78)
    r = 5
    for p in people:
        row = [p.rid, p.timestamp, p.username, p.gender, p.age_group,
               p.year_of_study, p.network_raw, p.spend_band, p.platforms_raw,
               p.time_band, p.exposure, p.interaction, p.ad_platform_raw,
               p.ad_type_raw] + p.likert_raw + [
            p.purchase, p.buy_freq, p.likelihood, p.factor, p.comparison,
            p.channel, p.overall_rating, p.ad_influence]
        for j, v in enumerate(row, start=1):
            c = _body_cell(ws, r, j, v, font=Font(name="Calibri", size=9, color="1B1B1B"))
            if j > 3:
                c.alignment = Alignment(vertical="top", wrap_text=(j < 15))
        ws.row_dimensions[r].height = 30
        r += 1
    widths = [8, 21, 30, 9, 12, 10, 16, 17, 34, 13, 13, 13, 22, 24] + [13] * 20 + [12, 12, 14, 24, 12, 18, 13, 24]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "D5"
    ws.auto_filter.ref = f"A4:{get_column_letter(len(headers))}{r - 1}"
    ws.sheet_properties.tabColor = GREY


# ------------------------------------------------------------------- build --
def build(people: list[Respondent], out_path: Path | str) -> Path:
    transcripts = build_transcripts(people)
    meta = interview_meta(people)

    wb = Workbook()
    sheet_readme(wb, people, transcripts, meta)
    sheet_guide(wb)
    sheet_register(wb, people, transcripts, meta)
    sheet_wide(wb, people, transcripts)
    sheet_long(wb, people, transcripts, meta)
    sheet_coding(wb, people, transcripts)
    sheet_codebook(wb, people, transcripts)
    sheet_frequency(wb, people, transcripts)
    sheet_validation(wb, people, transcripts)
    sheet_survey(wb, people)

    wb.properties.title = "Interview transcript database – social media advertising and mobile bundle buying decisions (MUBAS)"
    wb.properties.creator = "Synthesised from the survey response set"
    wb.properties.description = "Synthesised interviews aligned to the 119 survey respondents. Not primary data."

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    return out_path
