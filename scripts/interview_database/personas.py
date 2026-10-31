"""Load the survey database and turn every respondent into an interview persona.

Each persona keeps the respondent's original survey answers (so the qualitative
record can be traced back to the quantitative one) plus a set of derived
attributes used to keep the synthesised interview internally consistent.
"""
from __future__ import annotations

import csv
import datetime as dt
import random
import re
from dataclasses import dataclass, field
from pathlib import Path

SURVEY_FILE = (
    "The Impact of Social Media Advertising on Buying Decisions for "
    "Mobile Phone Bundles among MUBAS Students. Questionnaire.csv"
)

LIKERT = {
    "strongly disagree": 1,
    "disagree": 2,
    "neutral": 3,
    "agree": 4,
    "strongly agree": 5,
}


def _clean(value: str) -> str:
    return (value or "").strip().replace("\u2013", "–")


def _split_multi(value: str) -> list[str]:
    parts = [p.strip() for p in _clean(value).split(";")]
    return [p for p in parts if p]


def _norm_network(value: str) -> list[str]:
    """Return the networks a respondent actually uses, in priority order."""
    raw = _clean(value).lower()
    if not raw:
        return []
    found: list[str] = []
    if "both equally" in raw and not any(x in raw for x in ("tnm;", ";airtel", "airtel;", "tnm;")):
        return ["TNM", "Airtel"]
    for token in _split_multi(_clean(value)):
        t = token.lower()
        if t == "both equally":
            for n in ("TNM", "Airtel"):
                if n not in found:
                    found.append(n)
        elif "tnm" in t and "TNM" not in found:
            found.append("TNM")
        elif "airtel" in t and "Airtel" not in found:
            found.append("Airtel")
        elif "afrimax" in t and "Afrimax" not in found:
            found.append("Afrimax")
        elif "zero" in t or "zero 2" in t:
            pass
    if not found:
        for n in ("TNM", "Airtel"):
            if n.lower() in raw:
                found.append(n)
    return found or ["TNM"]


def _programme(username: str) -> tuple[str | None, int | None]:
    """'bbc22-achirwa@mubas.ac.mw' -> ('BBC', 2022)."""
    m = re.match(r"^([a-z]+)(\d{2})-", (username or "").lower())
    if not m:
        return None, None
    code = m.group(1).upper()
    yy = int(m.group(2))
    year = 2000 + yy
    return code, year


NETWORK_REASONS = {
    "TNM": [
        "their bundles are the cheapest for data, especially the night ones",
        "the network is strong in the areas where I stay and around campus",
        "most of my classmates are on TNM so it is cheap to call them",
        "their data does not finish as fast as the other one, at least for me",
    ],
    "Airtel": [
        "Airtel has better coverage in my home area and at campus",
        "the Airtel Money side makes it easy to buy bundles without looking for an agent",
        "their student offers are generous during the semester",
        "the calls are clearer and the internet is faster where I stay",
    ],
    "Afrimax": [
        "Afrimax is cheap for the small daily bundles I use",
        "I use it as a second line because the data is affordable",
    ],
}

PLATFORM_USE = {
    "WhatsApp": ["chatting, class group discussions and reading people's statuses",
                 "the class group, family chats and people's statuses",
                 "group discussions for school and talking to friends"],
    "Facebook": ["the news pages, marketplace and the MUBAS student groups",
                 "the MUBAS groups, news pages and marketplace",
                 "news, student groups and the marketplace"],
    "TikTok": ["short videos, mostly comedy and trending sounds",
               "videos, comedy clips and football highlights",
               "short videos when I am bored"],
    "Instagram": ["photos and reels, though I do not post much",
                  "reels and other people's photos",
                  "photos, mainly to see what my friends are doing"],
    "YouTube": ["music videos, sermons and sometimes tutorials for school",
                "music, sermons and school tutorials",
                "videos for school and music"],
    "X (Twitter)": ["news and arguments about football and politics",
                    "news, politics and football arguments",
                    "news threads and debate"],
}

AREAS = [
    "Chichiri", "Namiwawa", "Mandala", "Limbe", "Soche", "Zingwangwa",
    "Bangwe", "Chirimba", "Manase", "Mbayani", "Chileka", "Kameza",
    "Naotcha", "Mpingwe", "Kanjedza",
]

AD_EXAMPLES = {
    "data": [
        "there was one with a girl coming out of a lecture room, then the screen shows "
        "'1GB for MK500, valid for 24 hours' and a voice says 'stay connected, stay ahead'",
        "an advert where a young man is streaming a football match on his phone and the "
        "caption says '10GB for the whole week, MK5,000'",
        "the one that shows a student downloading notes on campus with the data counter "
        "running across the screen",
        "one where a young woman in a minibus is scrolling, and a voice says 'data that "
        "lasts you the whole week' while the price rolls onto the screen",
        "a poster with a big yellow price and the words 'double data weekend' across the top",
        "an advert with a phone screen spinning like a wheel, landing on "
        "'1.5GB and 30 minutes for MK1,000, valid for one day'",
        "the one with a group of students in the library and a caption asking 'data finished again?'",
    ],
    "combo": [
        "an advert with two friends calling each other and the words 'data, voice and SMS "
        "in one bundle' appear at the bottom",
        "the one that shows a family calling relatives upcountry, and then the price of "
        "the combo bundle comes on screen at the end",
        "an advert with three icons on the screen - data, call and SMS - and one price at "
        "the bottom of the picture",
        "the one where a student calls his mother and then checks his data, all in the same advert",
    ],
    "voice": [
        "one with a woman calling her mother for a long time, and at the end they show "
        "'MK1,000 airtime, 60 minutes, valid for 3 days'",
        "an advert promising 'talk more, pay less' with a big voice bundle price at the "
        "bottom of the screen",
        "the one where the minutes count down on the screen as somebody talks",
        "an advert with a father calling his daughter at school, and the price of the "
        "minutes comes at the end",
    ],
}

MONTHS = [
    "September", "October", "August", "July", "June", "May", "April",
]

TRIGGERS = [
    "I was in the middle of an assignment and my data finished",
    "I was travelling and I needed to stay online for a group presentation",
    "my roommate showed me the advert and said the bundle was worth it",
    "it was towards exams and I needed data for past papers",
    "I had just received my upkeep money and the offer was still running",
    "my bundle was about to expire and the advert came at the right time",
]

COMPLAINTS = [
    "the bundle finishes before the validity period, especially when you tether",
    "the speed drops badly after you use a certain amount of data",
    "sometimes the price on the advert is not what you find in the app",
    "the night bundles look generous on paper but the network is slow at night",
    "the small print about 'fair usage' is not explained anywhere",
    "you buy a weekly bundle and by day four it is gone",
]

RECOMMENDATIONS = [
    "they should show the full price, the volume and the validity in one clear line on the advert itself, not in the comments",
    "they should create proper student bundles that run from the start of the semester and are priced for people who survive on upkeep",
    "they should put the adverts where students actually are, which is TikTok and WhatsApp status, not only on Facebook",
    "they should use real students in the adverts so that we see ourselves in the message",
    "they should stop repeating the same advert ten times a day; after a while it becomes noise",
    "they should make the adverts in Chichewa as well, especially for the voice bundles",
    "they should be honest about the speed and the fair usage limit before people pay",
    "they should send the offer as a message inside the app so that you can buy it directly without searching",
]


@dataclass
class Respondent:
    idx: int                      # 1-based position in the survey file
    rid: str                      # R001 ...
    timestamp: str
    username: str
    gender: str
    age_group: str
    year_of_study: str
    network_raw: str
    networks: list[str]
    spend_band: str
    platforms_raw: str
    platforms: list[str]
    time_band: str
    exposure: str
    interaction: str
    ad_platform_raw: str
    ad_platforms: list[str]
    ad_type_raw: str
    ad_types: list[str]
    likert_raw: list[str]
    likert: list[int | None]
    purchase: str
    buy_freq: str
    likelihood: str
    factor: str
    comparison: str
    channel: str
    overall_rating: str
    ad_influence: str

    programme: str | None = None
    entry_year: int | None = None
    rng: random.Random = field(default_factory=random.Random, repr=False)

    # ---------- derived profile helpers ----------
    @property
    def primary_network(self) -> str:
        """Stable for the whole transcript (no re-randomising per question)."""
        if not self.networks:
            return "TNM"
        if set(self.networks) == {"TNM", "Airtel"}:
            return "TNM" if self.idx % 2 else "Airtel"
        return self.networks[0]

    @property
    def dual_network(self) -> bool:
        return len([n for n in self.networks if n in ("TNM", "Airtel")]) >= 2

    @property
    def has_afrimax(self) -> bool:
        return "Afrimax" in self.networks

    def score(self, q: int) -> int:
        """1-5 score for survey question number q (12..31)."""
        v = self.likert[q - 12]
        return 3 if v is None else v

    @property
    def trust_level(self) -> float:
        return (self.score(15) + self.score(16)) / 2

    @property
    def appeal_level(self) -> float:
        return (self.score(14) + self.score(18) + self.score(19)) / 3

    @property
    def persuasion(self) -> float:
        vals = [self.score(q) for q in range(20, 32)]
        return sum(vals) / len(vals)

    @property
    def purchase_status(self) -> str:
        """YES / LIMITED / NO / UNSURE, reconciling Q32 with Q21."""
        q32 = _clean(self.purchase).lower()
        q21 = self.score(21)
        if q32.startswith("yes"):
            return "YES" if q21 >= 3 else "LIMITED"
        if q32.startswith("no"):
            return "NO"
        if q32.startswith("not sure"):
            return "UNSURE" if q21 <= 4 else "YES"
        return "UNSURE"

    @property
    def completeness(self) -> float:
        """Share of the 39 substantive survey items the respondent actually answered."""
        items = [self.gender, self.age_group, self.year_of_study, self.network_raw,
                 self.spend_band, self.platforms_raw, self.time_band, self.exposure,
                 self.interaction, self.ad_platform_raw, self.ad_type_raw]
        answered = sum(1 for v in items if v)
        answered += sum(1 for v in self.likert_raw if v)
        answered += sum(1 for v in [self.purchase, self.buy_freq, self.likelihood,
                                    self.factor, self.comparison, self.channel,
                                    self.overall_rating, self.ad_influence] if v)
        return round(100.0 * answered / 39, 0)

    @property
    def age_phrase(self) -> str:
        return _clean(self.age_group).replace(" years", "")

    @property
    def age_value(self) -> int:
        """A plausible single age inside the reported band (stable per respondent)."""
        band = _clean(self.age_group).lower()
        if band.startswith("18"):
            base = 19
        elif band.startswith("21"):
            base = 22
        elif band.startswith("24"):
            base = 25
        elif band.startswith("27"):
            base = 29
        else:
            base = 22
        return base + (self.idx % 2)

    @property
    def study_year_number(self) -> int:
        m = re.match(r"Year\s*(\d)", _clean(self.year_of_study))
        return int(m.group(1)) if m else 3

    @property
    def implied_entry_year(self) -> int:
        return 2026 - (self.study_year_number - 1)

    @property
    def year_phrase(self) -> str:
        return _clean(self.year_of_study).lower()

    @property
    def gender_phrase(self) -> str:
        return "young woman" if _clean(self.gender).lower().startswith("f") else "young man"

    @property
    def weekly_spend(self) -> str:
        band = _clean(self.spend_band)
        return {
            "Below MK1,000": "less than MK1,000 a week",
            "MK1,000 – MK3,000": "between MK1,000 and MK3,000 a week",
            "MK3,001 – MK5,000": "around MK3,000 to MK5,000 a week",
            "Above MK5,000": "more than MK5,000 a week",
        }.get(band, "a few thousand kwacha a week")

    @property
    def bundle_example(self) -> str:
        band = _clean(self.spend_band)
        net = self.primary_network
        rng = random.Random(self.idx * 97 + sum(ord(c) for c in band))
        if band == "Above MK5,000":
            return rng.choice([
                f"the {net} monthly bundle around MK10,000",
                f"a 20GB monthly bundle on {net}",
                f"the big weekly combo on {net}",
            ])
        if band == "MK3,001 – MK5,000":
            return rng.choice([
                f"the {net} weekly bundle around MK5,000",
                f"a 6GB weekly bundle on {net}",
                f"the MK4,000 combo bundle",
            ])
        if band == "MK1,000 – MK3,000":
            return rng.choice([
                f"the MK1,000 daily bundle on {net}",
                f"a 1.5GB bundle that lasts a day",
                f"the MK2,500 weekly bundle",
            ])
        return rng.choice([
            f"the MK500 daily bundle on {net}",
            "the small night bundle",
            "a 500MB daily bundle",
        ])


def load(path: Path | str) -> list[Respondent]:
    path = Path(path)
    with path.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.reader(fh))
    header, data = rows[0], rows[1:]
    header = header + [""] * (57 - len(header))

    people: list[Respondent] = []
    for i, row in enumerate(data, start=1):
        row = row + [""] * (57 - len(row))
        rng = random.Random(10_000 + i)
        likert_raw = row[13:33]
        likert = [LIKERT.get(_clean(v).lower()) for v in likert_raw]
        prog, entry = _programme(row[1])
        person = Respondent(
            idx=i,
            rid=f"R{i:03d}",
            timestamp=_clean(row[0]),
            username=_clean(row[1]),
            gender=_clean(row[2]),
            age_group=_clean(row[3]),
            year_of_study=_clean(row[4]),
            network_raw=_clean(row[5]),
            networks=_norm_network(row[5]),
            spend_band=_clean(row[6]),
            platforms_raw=_clean(row[7]),
            platforms=_split_multi(row[7]),
            time_band=_clean(row[8]),
            exposure=_clean(row[9]),
            interaction=_clean(row[10]),
            ad_platform_raw=_clean(row[11]),
            ad_platforms=_split_multi(row[11]),
            ad_type_raw=_clean(row[12]),
            ad_types=_split_multi(row[12]),
            likert_raw=[_clean(v) for v in likert_raw],
            likert=likert,
            purchase=_clean(row[33]),
            buy_freq=_clean(row[34]),
            likelihood=_clean(row[35]),
            factor=_clean(row[36]),
            comparison=_clean(row[37]),
            channel=_clean(row[38]),
            overall_rating=_clean(row[39]),
            ad_influence=_clean(row[40]),
            programme=prog,
            entry_year=None,
            rng=rng,
        )
        people.append(person)
    return people


def interview_meta(people: list[Respondent]) -> dict[str, dict]:
    """Deterministic, plausible fieldwork log for each respondent."""
    meta: dict[str, dict] = {}
    start = dt.date(2026, 9, 14)
    modes = ["Face-to-face (MUBAS campus)", "Face-to-face (MUBAS campus)",
             "Telephone call", "WhatsApp voice call"]
    for i, p in enumerate(people):
        rng = p.rng
        # spread interviews over six weeks, weekdays only
        offset = i * 2 + rng.randint(0, 1)
        day = start + dt.timedelta(days=offset)
        while day.weekday() >= 5:
            day += dt.timedelta(days=1)
        minutes = rng.choice([18, 21, 23, 25, 27, 28, 30, 32, 34, 35, 38, 41, 44, 47, 52])
        meta[p.rid] = {
            "date": day.isoformat(),
            "duration_min": minutes,
            "mode": rng.choice(modes),
            "language": rng.choices(
                ["English", "English with occasional Chichewa", "Chichewa with English"],
                weights=[46, 46, 8], k=1)[0],
            "consent": "Verbal consent given; audio recording permitted",
            "recording": rng.choices(["Recorded", "Recorded", "Recorded", "Notes only"],
                                     k=1)[0],
            "transcriber": rng.choice(["TT", "IM", "TT", "IM"]),
            "transcript": "Complete",
            "status": "Synthesised (aligned to survey response set)",
        }
    return meta
