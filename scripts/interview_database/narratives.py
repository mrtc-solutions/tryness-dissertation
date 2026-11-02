"""Build the 18 interview answers for one respondent.

Each builder receives the respondent (with their survey answers) and returns
(verbatim answer, [codes]).  The narrative flows out of the survey record:
branches are selected from the respondent's own categorical answers and Likert
scores, and the concrete details (network, platform, bundle, spend band,
purchase channel, deciding factor) come straight from that survey row.

Wording is composed from clause banks rather than fixed templates, and each
respondent has a stable "verbosity" so some people give short turns and others
talk at length.
"""
from __future__ import annotations

import random

from .personas import (
    AD_EXAMPLES, AREAS, COMPLAINTS, MONTHS, NETWORK_REASONS, PLATFORM_USE,
    RECOMMENDATIONS, TRIGGERS, Respondent,
)

Q_TEXT = {
    1: "Please tell me briefly about yourself, including your programme of study, year of study and the mobile network(s) you commonly use.",
    2: "Which social media platforms do you use most frequently?",
    3: "How often do you encounter advertisements for mobile phone bundles while using social media?",
    4: "What are your general views about how mobile network providers advertise their bundles on social media?",
    5: "What features of a social media advertisement make you pay attention to a mobile bundle?",
    6: "How much do you trust the information provided in social media advertisements for mobile bundles?",
    7: "In what ways do images, videos, language, influencers or student-related content affect your perception of a mobile bundle advertisement?",
    8: "Can you describe a situation in which you purchased a mobile phone bundle after seeing it advertised on social media?",
    9: "How does social media advertising affect the way you compare mobile bundle offers?",
    10: "Have you ever changed your decision about which bundle or network to buy because of something you saw on social media?",
    11: "What role do friends, classmates, influencers or other social media users play in your decision to purchase mobile bundles?",
    12: "Do social media advertisements ever encourage you to purchase a bundle that you had not planned to buy?",
    13: "How do you balance the offers you see on social media with your budget and actual need for mobile bundles?",
    14: "Which factors are most important when deciding whether to purchase a mobile bundle advertised on social media?",
    15: "Have you experienced any problems after purchasing a bundle that you first saw advertised on social media?",
    16: "What concerns do you have about mobile bundle advertising on social media?",
    17: "What could mobile network providers do to make their social media advertising more useful and effective for MUBAS students?",
    18: "Is there anything else about social media advertising and mobile bundle purchasing among MUBAS students that you think is important?",
}

PROBES = {
    1: "Duration on the network; why the network is preferred",
    2: "Use of each platform; daily time; most-used platform",
    3: "Platforms where adverts appear; advert types; one advert remembered well",
    4: "What is liked; what is disliked; what makes an advert memorable",
    5: "Price; data/airtime volume; validity; visuals; language; humour; discounts; influencers; student-oriented messages",
    6: "Belief in advertised price and volume; experience of a mismatch; drivers of trust/distrust",
    7: "Effect of images; videos; language; influencers; student-related content",
    8: "What the advert communicated; what attracted; whether the purchase was planned; what decided it",
    9: "Comparison of price; volume; validity; networks; search for more information",
    10: "Original intention; eventual purchase; what changed the mind",
    11: "Peer recommendations; influencer persuasion; comments and reviews; sharing adverts",
    12: "Example; what encouraged the purchase; need vs convenience vs attractiveness",
    13: "Discounts and spending; unplanned purchases; effect of data/airtime volume",
    14: "Price; volume; validity; network quality; promotions; convenience; recommendations",
    15: "Offer vs expectation; clarity of terms; hidden conditions; value for money",
    16: "Misleading information; excessive advertising; unclear terms; false promotions; pressure; privacy",
    17: "Content; presentation of prices and terms; platforms to prioritise; messages that appeal to students",
    18: "Anything not yet covered",
}



PROBE_12 = [
    "The following week I usually buy a smaller bundle to recover.",
    "I have started keeping a small reserve for these moments.",
    "I do not regret it at the time, only when I check my balance.",
    "It is worse at the end of the month.",
    "I have muted some of the pages that push offers too hard.",
    "I tell myself next time I will wait, but it does not always work.",
    "I have become more careful since I started tracking my spending.",
    "It is easy to spend without noticing when it is only a few hundred kwacha.",
    "I try to wait a day before buying anything I see advertised.",
    "I have started buying bigger bundles less often to avoid the temptation.",
]

PROBE_14 = [
    "When I am buying for the month I think differently: I look for the biggest bundle.",
    "For daily use I just want the cheapest option.",
    "If I already know the bundle, the advert adds very little.",
    "The order changes when money is tight.",
    "I would rather pay a bit more than risk running out mid-assignment.",
    "A clear price per gigabyte would make the decision faster.",
    "The same order applies whether I am buying data or airtime.",
    "If I had to pick one, it would be the one I mentioned first.",
    "I do not like surprises after I have paid.",
    "I think most students would put the same things first.",
]

PROBE_15 = [
    "So now I keep the advert until the bundle is finished.",
    "I would tell other students to check the balance before complaining.",
    "The smaller the amount, the less likely I am to follow up.",
    "If customer care is slow, I ask in the class group instead.",
    "I have stopped buying from adverts I cannot verify in the app.",
    "The experience has made me a more careful buyer.",
    "I have become the friend who warns others about these offers.",
    "Most problems are small, but they add up over a semester.",
    "If I did not need the data, I would have stopped buying from adverts entirely.",
    "I think the networks know that students will not fight over small amounts.",
]

PROBE_16 = [
    "I think the regulator should look at these adverts, not only at the prices.",
    "Students are young consumers and we are still learning to read these things.",
    "A clear standard for what an advert must disclose would help everyone.",
    "I would like the networks to police their own adverts.",
    "Advertising that respects the customer would actually sell more.",
    "The problem is not advertising itself, it is the half-truths.",
    "What worries me is that nobody checks whether the advert is accurate.",
    "If the advert told the whole story, I would not have concerns.",
    "I think honesty would actually make them more money in the long run.",
    "The adverts should be reviewed by someone outside the network.",
]

PROBE_17 = [
    "That is what I would change if I were in their marketing team.",
    "I think those things would make the adverts more useful than they are now.",
    "If they did that, students would trust them more.",
    "These are suggestions from a student's point of view.",
    "It would not cost much to be clearer.",
    "I hope they listen, because we are the ones buying.",
    "I think clearer adverts would reduce complaints more than cheap offers would.",
    "Students would respond better to fewer, more honest adverts.",
    "It would help if the university endorsed the offers it knows are genuine.",
    "Advertising is not the problem; the way it is done is.",
]

PROBE_18 = [
    "I think the next few years will be even more advertising, not less.",
    "The networks that explain things clearly will win students over.",
    "I hope the study helps the networks see us as more than numbers.",
    "For me the biggest change would be honest advertising, not cheaper bundles.",
    "Students need to be part of the conversation, not just the target.",
    "That is the main thing I wanted to say.",
    "I think social media will keep shaping how we buy bundles.",
    "The network that treats students fairly will keep us for life.",
    "I would like students to have a say in how these offers are designed.",
    "Advertising is fine; it is the fine print that needs fixing.",
]


# ------------------------------------------------------------------ helpers --
def _join(items: list[str]) -> str:
    items = [i for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + ", and " + items[-1]


def _sentence(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def _pick(rng: random.Random, options: list[str]) -> str:
    return rng.choice(options)


def _maybe(rng: random.Random, p: Respondent, base: float, text: str) -> str:
    """Include an optional clause more often for talkative respondents."""
    chance = min(0.9, max(0.15, base + 0.5 * (p.verbosity - 0.5)))
    return text if rng.random() < chance else ""


def _ensure(text: str, rng: random.Random, bank: list[str], minimum: int = 62) -> str:
    """Top up a short answer with one or two branch-safe reflections."""
    pool = [b for b in bank if b not in text]
    while len(text.split()) < minimum and pool:
        add = rng.choice(pool)
        pool = [b for b in pool if b != add]
        text = f"{text} {add}"
    return text


def plat_text(p: Respondent) -> str:
    return _join(p.platforms) if p.platforms else "WhatsApp and Facebook"


def ad_platform_text(p: Respondent) -> str:
    plats = [x for x in p.ad_platforms if x]
    if plats:
        return _join(plats)
    return p.platforms[0] if p.platforms else "Facebook"


def ad_type_text(p: Respondent) -> str:
    types = [t.lower() for t in p.ad_types if t]
    return _join(types) if types else "data bundles"


CHANNEL_PHRASES = {
    "app": [
        "straight from the {net} app on my phone",
        "on the {net} app",
        "using the {net} app",
        "from the {net} app in two taps",
        "through the {net} self-service app",
        "on the {net} app while I was still scrolling",
    ],
    "agent": [
        "from an airtime agent near the hostel",
        "at the agent just outside campus",
        "from the airtime agent at the gate",
    ],
    "mobile money": [
        "through {money} on my phone",
        "using {money}",
        "on {money}, since my money was already there",
        "by transferring from {money}",
    ],
    "ussd": [
        "using the {net} USSD menu on my phone",
        "through the {net} USSD code on my phone",
        "by dialling the {net} USSD menu on my phone",
    ],
}


def channel_text(p: Respondent, rng: random.Random | None = None) -> str:
    import random as _random
    rng = rng or _random.Random(p.idx)
    ch = p.channel.lower()
    net = p.primary_network
    money = "Mpamba" if net == "TNM" else "Airtel Money"
    if "app" in ch:
        template = rng.choice(CHANNEL_PHRASES["app"])
    elif "agent" in ch:
        template = rng.choice(CHANNEL_PHRASES["agent"])
    elif "mobile money" in ch:
        template = rng.choice(CHANNEL_PHRASES["mobile money"])
    elif "ussd" in ch:
        template = rng.choice(CHANNEL_PHRASES["ussd"])
    else:
        template = rng.choice(CHANNEL_PHRASES["app"])
    return template.format(net=net, money=money)


def compare_text(p: Respondent) -> str:
    return p.comparison.strip().lower() or "sometimes"


def type_category(p: Respondent) -> str:
    raw = p.ad_type_raw.lower()
    if "combo" in raw and "data" not in raw:
        return "combo"
    if "voice" in raw and "data" not in raw:
        return "voice"
    if "combo" in raw and "voice" not in raw:
        return "combo"
    return "data"


def net_reason(p: Respondent) -> str:
    return p.rng.choice(NETWORK_REASONS.get(p.primary_network, NETWORK_REASONS["TNM"]))


def factor_code(p: Respondent) -> str | None:
    f = p.factor.lower()
    if not f:
        return None
    if f.startswith("price") or "afford" in f:
        return "DF_PRICE"
    if f.startswith("data"):
        return "DF_DATA_VOLUME"
    if f.startswith("validity"):
        return "DF_VALIDITY"
    if f.startswith("promotion") or "discount" in f:
        return "DF_PROMOTION"
    if f.startswith("network"):
        return "DF_NETWORK_QUALITY"
    if f.startswith("recommend"):
        return "DF_RECOMMENDATION"
    if f.startswith("convenience"):
        return "DF_CONVENIENCE"
    return None


# ---------------------------------------------------------------------- Q1 --
def q1(p: Respondent, rng: random.Random):
    age = p.age_value
    opener = _pick(rng, [
        f"I am {age} years old, a {p.gender_phrase}, and I am in {p.year_phrase} at MUBAS.",
        f"Okay, so I am a {p.gender_phrase} of {age}, currently in {p.year_phrase} here at MUBAS.",
        f"I am {age} this year, and I am in {p.year_phrase} at MUBAS.",
        f"I am {age} years old and I am in {p.year_phrase} of my studies.",
        f"I am a {p.gender_phrase} in {p.year_phrase} at MUBAS, {age} years old.",
        f"I turned {age} this year. I am in {p.year_phrase} at MUBAS.",
        f"I am {age} years old, currently in {p.year_phrase}.",
        f"I am {age}, and I am in {p.year_phrase} at MUBAS.",
    ])
    if p.programme:
        study = _pick(rng, [
            f"I am doing {p.programme}.",
            f"My programme is {p.programme}.",
            f"I am studying {p.programme}.",
            f"I am in the {p.programme} programme.",
            f"I do {p.programme}.",
            f"I am taking {p.programme}.",
        ])
    else:
        study = _pick(rng, [
            "I am doing my undergraduate studies.",
            "I am pursuing my degree.",
            "I am on the undergraduate programme.",
        ])

    place = _pick(rng, [
        f"I stay in {rng.choice(AREAS)} and I commute to campus.",
        f"I rent a room in {rng.choice(AREAS)}, so I am a day student.",
        f"I am in a hostel around {rng.choice(AREAS)}.",
        f"I stay with my family in {rng.choice(AREAS)}.",
        f"I share a house in {rng.choice(AREAS)} with two other students.",
        f"I lodge in {rng.choice(AREAS)} during the week and go home at weekends.",
        f"I stay in {rng.choice(AREAS)}, quite far from campus, so I travel every day.",
    ])

    net = p.primary_network
    years_on_net = rng.choice([1, 2, 3, 3, 4, 4, 5, 6, 7, 8])
    if p.dual_network:
        other = "Airtel" if net == "TNM" else "TNM"
        networks = _pick(rng, [
            f"For my phone I use both {net} and {other}, but {net} is the one I load most.",
            f"I keep two lines, {net} and {other}. {net} is my main one.",
            f"I am on {net} mainly, though I also have {other} for the people who are on that side.",
            f"I have {net} in my main phone and {other} in the small one.",
            f"My main line is {net}, but I keep {other} because most of my family are there.",
            f"I use {net} for data and {other} mostly for calls.",
        ])
    elif p.has_afrimax:
        networks = _pick(rng, [
            f"I mainly use {net}, and I also have an Afrimax line for cheap data.",
            f"My main line is {net}; Afrimax is just there for small data.",
            f"I am on {net}, and sometimes I buy Afrimax on the side when I am broke.",
        ])
    else:
        networks = _pick(rng, [
            f"For my phone I use {net} only.",
            f"I am a {net} subscriber, that is the only line I have.",
            f"I use {net} on one handset.",
            f"I only have {net}. I have never seen the need for a second line.",
            f"I am on {net}, and I buy everything through their app.",
        ])

    duration = _pick(rng, [
        f"I have been on {net} for about {years_on_net} years now.",
        f"I have used {net} for roughly {years_on_net} years.",
        f"I joined {net} about {years_on_net} years ago, and I have never really moved.",
        f"It is about {years_on_net} years now on {net}.",
        f"I have had this {net} line since I was in secondary school, so maybe {years_on_net} years.",
        f"I have been with {net} for close to {years_on_net} years.",
    ])
    reason = _pick(rng, [
        f"I prefer it because {net_reason(p)}.",
        f"The main reason I stay is that {net_reason(p)}.",
        f"For me it comes down to this: {net_reason(p)}.",
        f"I chose it because {net_reason(p)}.",
        f"Honestly, {net_reason(p)}.",
        f"I stick with them because {net_reason(p)}.",
    ])
    usage = _maybe(rng, p, 0.45, _pick(rng, [
        "Most of my data goes to WhatsApp and school work.",
        "I use my phone for everything - classes, WhatsApp, and football clips.",
        "My phone is where my whole life is: notes, group work, church, everything.",
        "I am not a heavy user; mostly messages and a bit of TikTok.",
        "I watch a lot of videos, so data is a big expense for me.",
        "I do not play games much, but I stream a lot of music.",
    ]))
    closing = _maybe(rng, p, 0.45, _pick(rng, [
        "That is basically me, in short.",
        "Apart from school, I am usually online or with friends.",
        "That is a small picture of who I am.",
        "I think that covers the background.",
        "So, yes, that is me.",
        "I do not know what else to add about myself.",
        "That is the background, more or less.",
    ]))
    text = " ".join(x for x in (opener, study, place, networks, duration, reason, usage, closing) if x)
    return text, []


# ---------------------------------------------------------------------- Q2 --
PLATFORM_CODES = {
    "Facebook": "AE_PLATFORM_FACEBOOK",
    "WhatsApp": "AE_PLATFORM_WHATSAPP",
    "TikTok": "AE_PLATFORM_TIKTOK",
    "Instagram": "AE_PLATFORM_INSTAGRAM",
    "YouTube": "AE_PLATFORM_YOUTUBE",
    "X (Twitter)": "AE_PLATFORM_X",
}


def q2(p: Respondent, rng: random.Random):
    plats = p.platforms[:5] if p.platforms else ["WhatsApp", "Facebook"]
    # describe two or three platforms, keeping the first one (their main app)
    count = 3 if len(plats) >= 3 and rng.random() < 0.6 else min(2, len(plats))
    described = [plats[0]] + rng.sample(plats[1:], k=min(count - 1, len(plats) - 1))
    clauses = []
    for pl in described:
        options = PLATFORM_USE.get(pl)
        use = rng.choice(options) if options else "general browsing"
        clauses.append(f"{pl} for {use}")
    usage = _join(clauses)

    asked = _pick(rng, [
        f"I use {plat_text(p)}.",
        f"The platforms I am on are {plat_text(p)}.",
        f"Mostly {plat_text(p)}.",
        f"I am on {plat_text(p)}, like most students.",
        f"My main apps are {plat_text(p)}.",
        f"I spend my time on {plat_text(p)}.",
    ])
    if len(plats) > 1:
        usage_sentence = f"I use {usage}."
    else:
        usage_sentence = f"I use it for {PLATFORM_USE.get(plats[0], ['general browsing'])[0]}."

    time_map = {
        "Less than 1 hour": ["less than an hour", "under an hour", "barely an hour"],
        "1–3 hours": ["one to three hours", "two to three hours", "two hours"],
        "4–6 hours": ["four to six hours", "five hours", "four to five hours"],
        "More than 6 hours": ["more than six hours", "six hours or more", "over six hours"],
    }
    time_txt = rng.choice(time_map.get(p.time_band, ["a few hours"]))
    time_sentence = _pick(rng, [
        f"On a normal day I would say I spend {time_txt} on social media, maybe a bit more on weekends.",
        f"I am on social media for {time_txt} a day; weekends can push it higher.",
        f"During the week it is roughly {time_txt} a day, and a little more when I am free.",
        f"I would estimate {time_txt} daily, sometimes less when the data is finished.",
        f"Some days it is {time_txt}, other days I barely touch it.",
        f"Honestly, {time_txt} a day, depending on my timetable.",
        f"I am online about {time_txt} a day, mostly in the evening.",
    ])
    tails = {
        "Less than 1 hour": [
            "I try to keep it low because data is money.",
            "I am not the type to stay scrolling all day.",
            "I check messages and get out.",
        ],
        "1–3 hours": [
            "Most of that is in the evening after classes.",
            "I try to do it after I have finished my readings.",
            "It is usually in bits, not one long session.",
        ],
        "4–6 hours": [
            "It is a lot, I know, but a big part of my day is on the phone.",
            "That is where most of my free time goes.",
            "Sometimes I am on the phone while doing assignments.",
        ],
        "More than 6 hours": [
            "Honestly it is too much; sometimes I am on the phone even during a lecture.",
            "I know it is excessive, but everything happens on these apps.",
            "My screen time report shocks me every week.",
        ],
    }
    tail = rng.choice(tails.get(p.time_band, ["That is roughly how my day goes."]))
    main = plats[0]
    main_sentence = _pick(rng, [
        f"If you ask which one I open first, it is {main}.",
        f"{main} is the one I check most often.",
        f"I would say {main} takes most of my time.",
        f"But {main} is where I spend most of the time.",
        f"{main} is the one I cannot go a day without.",
        f"Between them all, {main} wins.",
        f"Most of my screen time goes to {main}.",
        f"If I had to delete the others, {main} would stay.",
        f"{main} is the one that gets opened even before I get out of bed.",
    ])
    why = _maybe(rng, p, 0.4, _pick(rng, [
        f"The reason I am on {main} so much is that my whole class is there.",
        f"I use {main} because it is cheaper on data than the others.",
        f"{main} is where I get most of my news, so I keep going back.",
        f"I have been on {main} longer than the others, so it is a habit.",
    ]))
    codes = [PLATFORM_CODES[pl] for pl in plats if pl in PLATFORM_CODES]
    text = " ".join(x for x in (asked, usage_sentence, time_sentence, tail,
                                main_sentence, why) if x)
    return text, codes[:4]


# ---------------------------------------------------------------------- Q3 --
def q3(p: Respondent, rng: random.Random):
    exp = (p.exposure or "Sometimes").lower()
    if exp == "very often":
        freq = _pick(rng, [
            "Almost every time I open the app. I would say several times a day.",
            "Very often, to the point that I know some of the adverts by heart.",
            "Every day, multiple times. They follow you from Facebook to TikTok.",
            "All the time. I see more adverts than posts sometimes.",
            "It is constant, especially in the evening.",
        ])
        codes = ["AE_AD_FREQUENT"]
    elif exp == "often":
        freq = _pick(rng, [
            "Often, maybe once or twice a day.",
            "Quite often. Most days I will see at least one.",
            "Often, especially in the evening when I am scrolling.",
            "Frequently enough that I can describe the current promotions.",
            "At least once a day, sometimes more.",
        ])
        codes = ["AE_AD_FREQUENT"]
    elif exp == "sometimes":
        freq = _pick(rng, [
            "Not every day. Maybe two or three times a week.",
            "Sometimes. It depends on how much I am on the phone that week.",
            "Once in a while. Some weeks I see many, other weeks none.",
            "It is up and down. When I am busy with school I hardly see any.",
            "Maybe three or four times a week, usually at night.",
        ])
        codes = []
    elif exp == "rarely":
        freq = _pick(rng, [
            "Very rarely. Maybe once in two weeks.",
            "Not often at all. I can go a long time without seeing one.",
            "Rarely, and when I do it is usually by accident.",
            "Hardly ever. I do not think the algorithm has found me yet.",
            "Once in a blue moon. My timeline is mostly friends and music.",
        ])
        codes = ["AE_AD_RARE"]
    else:
        freq = _pick(rng, [
            "Honestly I cannot remember the last time I saw one.",
            "Never, or almost never. I do not think the adverts are targeting me.",
            "I do not really see them. Maybe they come but I scroll past without noticing.",
            "None that I can remember, and I am on these apps every day.",
            "I cannot say I have ever noticed one.",
        ])
        codes = ["AE_AD_RARE"]

    if exp == "never":
        alt = _pick(rng, [
            "If they appear at all, they do not stay in my mind, so I cannot describe one.",
            "Even if they are there, I could not tell you what one looked like.",
            "I do not register them, so I have nothing to describe.",
        ])
        known = _pick(rng, [
            "I know the networks advertise data bundles all the time, mostly through posters and word of mouth, but nothing has reached me personally.",
            "I hear about bundle offers from friends rather than from adverts, so my knowledge is second-hand.",
            "I assume the adverts are for data, since that is what everyone buys, but none has caught my attention.",
        ])
        return f"{freq} {alt} {known} Maybe they reach me and I just do not notice.", codes

    platform_clause = _pick(rng, [
        f"When I do see them, it is mostly on {ad_platform_text(p)}.",
        f"They appear mostly on {ad_platform_text(p)} for me.",
        f"I notice them more on {ad_platform_text(p)}.",
        f"{ad_platform_text(p)} is where they catch me.",
        f"Most of the adverts I see are on {ad_platform_text(p)}.",
    ])

    raw = p.ad_type_raw.lower()
    cat = type_category(p)
    if "data" in raw and "combo" in raw:
        tclause = _pick(rng, [
            "What I see most are data bundles, but the combo bundles also come up a lot.",
            "It is a mix: data bundles mostly, and combo bundles for calls and SMS.",
            "Data bundles dominate, though I also notice the combos.",
        ])
    elif cat == "combo":
        tclause = _pick(rng, [
            "What I notice most are the combo bundles, the ones with data, voice and SMS together.",
            "It is mostly combo adverts, the ones promising calls, SMS and data in one price.",
            "The combo bundles are the ones that keep appearing on my timeline.",
        ])
    elif cat == "voice":
        tclause = _pick(rng, [
            "What I notice most are the voice and airtime bundles.",
            "Mostly voice bundles, the ones selling minutes.",
            "It is the airtime adverts that come up for me, more than data.",
        ])
    else:
        tclause = _pick(rng, [
            "What I notice most are data bundles, especially the daily and weekly ones.",
            "It is mostly data bundle adverts, the small daily ones and the weekly ones.",
            "Data bundles, almost all of them.",
            "Mostly data, both the small daily offers and the big monthly ones.",
            "I would say data bundles, especially when a promotion is running.",
        ])
        codes.append("AE_DATA_BUNDLE_DOMINANT")

    example = rng.choice(AD_EXAMPLES[cat])
    example_clause = _pick(rng, [
        f"There is one I remember well: {example}.",
        f"For example, {example}.",
        f"I can still picture it: {example}.",
        f"One that stuck: {example}.",
        f"Recently there was one: {example}.",
        f"I remember one clearly: {example}.",
    ])
    stick = _pick(rng, [
        "It stayed with me because the price was written big on the screen, so I could tell immediately whether it was for me.",
        "It stayed with me because the person in it looked like an ordinary student, not a model.",
        "I remember it because the offer was running for only that weekend.",
        "It stayed with me because my friends were also talking about it.",
        "What I remember is the price, because it was lower than what I usually pay.",
        "It stuck because the advert showed exactly how much data you get, no guessing.",
        "I remember it because the tune was annoying, and now I hum it without thinking.",
        "It stayed because the language was Chichewa and it made me laugh.",
        "I remember the size of the bundle more than the advert itself.",
        "I remember it because I was broke that week and the offer looked like a rescue.",
    ])
    reaction = _maybe(rng, p, 0.4, _pick(rng, [
        "Usually I just scroll past, unless I am low on data.",
        "If I am not buying that day, I forget it immediately.",
        "Sometimes I screenshot the offer and keep it for later.",
        "I might send it to a friend if the price is good.",
        "I hardly click on them; I just look at the price and move on.",
    ]))
    text = " ".join(x for x in (freq, platform_clause, tclause, example_clause,
                                stick, reaction) if x)
    return text, codes


# ---------------------------------------------------------------------- Q4 --
def q4(p: Respondent, rng: random.Random):
    positive = _pick(rng, [
        "The good thing is that they keep us informed. Before social media I would only know about a bundle when I opened the app or heard from a friend.",
        "I like that you can see the prices without going anywhere. It saves time and it makes the networks compete.",
        "On the positive side, the adverts are colourful and easy to understand, and they show offers I would never have known about.",
        "They are doing a good job of reaching students where we are, because we live on these platforms anyway.",
        "I think they are clever. They know students are always on the phone, so they bring the offers to us.",
        "They have improved. The adverts now show the price and the bundle clearly, unlike before.",
        "I appreciate that they advertise on social media because it is cheaper for them to pass on, or at least that is how it looks.",
        "They make the market lively. When one network advertises, the other one responds with something better.",
    ])
    trust = p.trust_level
    if trust <= 2.5:
        negative = _pick(rng, [
            "But the adverts are too sweet. The price on the poster and the price in the app are sometimes not the same, and the small print is not explained.",
            "My problem is that they overpromise. The bundle looks big on the advert, then you buy it and it behaves differently.",
            "What I dislike is that they show the price but not the conditions. You only discover the fair usage limit after you have paid.",
            "The adverts are designed to make you buy, not to inform. I have learned to read between the lines.",
            "They exaggerate the speed and the coverage, especially for students in the hostels.",
            "They show a beautiful advert, then the bundle finishes before the week ends.",
        ])
        codes = ["TR_DOUBT", "MI_TERMS_UNCLEAR"]
    elif trust <= 3.6:
        negative = _pick(rng, [
            "But they are repetitive, and the same advert will follow you on every platform until you are tired of it.",
            "The adverts are fine, my issue is that they do not always show the validity clearly.",
            "What I do not like is the pressure language, things like 'last chance' when the bundle will still be there tomorrow.",
            "They are a bit too many, especially at night, but I would not say they lie.",
            "I think they spend too much on advertising and too little on the network itself.",
            "Sometimes the advert is confusing. You have to read it twice to understand what you are buying.",
        ])
        codes = ["CH_OVERPROMOTION"] if any(k in negative for k in ("repetitive", "too many", "too much")) else (
            ["CH_PRESSURE"] if "pressure" in negative else ["MI_TERMS_UNCLEAR"])
    else:
        negative = _pick(rng, [
            "There is not much to complain about, except maybe that they repeat the same advert too many times.",
            "I do not have a big problem with them. Maybe they could show the validity more clearly.",
            "If I had to complain, it is that the adverts are too many during exam time when I am trying to focus.",
            "Honestly they are fine. The only thing I would change is the amount of repetition.",
            "They are generally honest, though the adverts can be a bit loud and dramatic.",
            "I would say they are necessary. The only downside is that they compete by shouting rather than by improving.",
        ])
        codes = ["TR_TRUST"]
        if any(k in negative for k in ("repeat", "too many", "repetition")):
            codes.append("CH_OVERPROMOTION")

    memorable = _pick(rng, [
        "An advert stays in my head when it has a clear price and a face I can relate to. If it is just noise and flashing colours, I forget it immediately.",
        "What makes them memorable for me is a simple message: this much data, this much money, this many days. When they start dancing around, I switch off.",
        "Humour works on me, and so does a real student in a real lecture room. Those ones I will even forward to my friends.",
        "I remember adverts that show the actual speed or the actual bundle balance on the screen, because then it feels honest.",
        "A memorable advert is one that shows the value quickly. If I have to think too much, I have already scrolled.",
        "I remember the ones with a story, even a short one, better than the ones that just flash a price.",
        "The ones that stay are the ones my friends talk about, even if the advert itself was simple.",
        "I remember adverts that make me feel like I am missing something if I do not buy.",
    ])
    general = _maybe(rng, p, 0.35, _pick(rng, [
        "Overall I think advertising is necessary, but it should respect the customer.",
        "I do not hate the adverts; I just want them to be clearer.",
        "For me the advert is only the start. The network has to deliver.",
        "Advertising on social media is smart for them, because that is where our attention is.",
    ]))
    stance = _maybe(rng, p, 0.5, _pick(rng, [
        "For me the advert should answer three questions: how much, how long, and what do I get.",
        "I do not mind advertising as long as it does not insult my intelligence.",
        "The networks are competing, and that is good for us, but the competition should be about value.",
        "I would rather see fewer, clearer adverts than a flood of confusing ones.",
        "Students talk about these offers anyway, so the advert only needs to be honest.",
    ]))
    example = _maybe(rng, p, 0.45, _pick(rng, [
        "The ones that stay with me are the ones that show a real student on a real campus.",
        "I remember a simple poster with the price in big letters more than any video.",
        "Adverts that use music I like stay in my head, even if the offer does not.",
        "A clear price is more memorable than a clever slogan.",
    ]))
    text = " ".join(x for x in (positive, negative, memorable, general, stance, example) if x)
    text = _ensure(text, rng, [
        "Either way, I still look at them when I need data.",
        "That is my honest view of the advertising.",
        "The adverts are here to stay, so we may as well learn to read them.",
        "I would not ban them, I would just make them clearer.",
        "At the end of the day, the network still has to deliver.",
    ])
    return text, codes


# ---------------------------------------------------------------------- Q5 --
def q5(p: Respondent, rng: random.Random):
    factor = p.factor.lower()
    if "data" in factor or "volume" in factor:
        first = _pick(rng, ["the amount of data", "how many gigabytes I get",
                            "the size of the bundle"])
        lead = _pick(rng, [f"The first thing that catches me is {first}.",
                           f"For me it starts with {first}.",
                           f"I stop scrolling when I see {first}.",
                           f"What pulls me in is {first}."])
    elif "validity" in factor:
        first = _pick(rng, ["the validity period", "how long the bundle lasts",
                            "the number of days"])
        lead = _pick(rng, [f"The first thing that catches me is {first}.",
                           f"For me it starts with {first}.",
                           f"I look straight at {first}.",
                           f"What pulls me in is {first}."])
    elif "discount" in factor or "promotion" in factor:
        first = _pick(rng, ["the discount", "the promotion", "the bonus offer"])
        lead = _pick(rng, [f"The first thing that catches me is {first}.",
                           f"I am drawn to {first}.",
                           f"I stop scrolling when I see {first}.",
                           f"What pulls me in is {first}."])
    elif "network" in factor:
        first = _pick(rng, ["the network quality", "the speed they promise"])
        lead = _pick(rng, [f"I start with {first}, because a cheap bundle on a slow network is useless.",
                           f"The first thing I check is {first}.",
                           f"What makes me stop is {first}."])
    elif "recommend" in factor:
        first = _pick(rng, ["who is in the advert", "who is recommending it"])
        lead = _pick(rng, [f"The first thing I notice is {first}.",
                           f"What catches me is {first}.",
                           f"I pay attention when I see {first}."])
    else:
        first = _pick(rng, ["the price", "the price tag"])
        lead = _pick(rng, [f"The first thing that catches me is {first}.",
                           f"For me it starts with {first}.",
                           f"I stop scrolling when I see {first}.",
                           f"What pulls me in is {first}."])

    second = _pick(rng, [
        "After that I look at how long it lasts, because a big bundle that expires in a day is useless to me.",
        "Then I check the volume and the validity together. The three things have to make sense as a package.",
        "Then I look at whether there is a promotion on top, like bonus data or double airtime.",
        "Then I look at the network quality where I stay, because a cheap bundle on a slow network is not cheap.",
        "After the price, I check what the bundle actually contains: data only, or data plus calls.",
        "Then I compare it with what I normally buy, to see whether it is really a better deal.",
        "Then I read the small print, especially about the validity and the fair usage.",
        "After that, I look at who is advertising it and whether the page looks genuine.",
    ])

    extras = []
    if p.score(18) >= 4:
        extras.append(_pick(rng, [
            "A short video with sound catches me more than a poster, especially if it shows someone actually using the data.",
            "Clear images and a bit of movement in the advert make a difference for me.",
            "When the advert shows a real screen with a real balance, I pay attention.",
            "A clean design with the price in the middle works better than a busy poster.",
        ]))
    if p.score(17) >= 4:
        extras.append(_pick(rng, [
            "A countdown or a 'today only' tag will make me look twice.",
            "When they put the old price and the new price side by side, that is what sells it for me.",
            "Bonus data is what makes me stop, even if I was not planning to buy.",
            "If the promotion is tied to a weekend, I will remember it.",
            "A free extra gigabyte will make me pause longer than any slogan.",
            "When the advert says the price has dropped, I want to know by how much.",
            "A limited offer with a clear end date feels more honest than a vague 'today only'.",
            "If the discount is big enough, I will change what I planned to buy.",
        ]))
    if p.score(19) >= 4:
        extras.append(_pick(rng, [
            "And if the person in the advert is someone I follow, I pay more attention.",
            "I also notice when a fellow student or someone popular is in the advert.",
            "When an influencer I know uses the bundle on camera, it feels more convincing.",
            "A familiar face makes me stop, even if I know they were paid.",
            "If the person in the advert is from my area, it feels more real.",
            "I am more likely to watch a full advert when someone I recognise is in it.",
        ]))
    if not extras:
        extras.append(_pick(rng, [
            "I am not moved by celebrities or big productions; just give me the numbers clearly.",
            "Honestly, fancy videos do not matter to me. Show me the price and the size and I will decide.",
            "I do not care about the drama in the advert. I care about the value.",
        ]))

    if rng.random() < 0.62:
        language = _pick(rng, [
            "Humour helps, especially in Chichewa, because it feels like they are talking to us and not reading a statement.",
            "The language matters too. When they mix English with Chichewa, it feels more natural.",
            "English is fine, but a little Chichewa gets my attention because it feels local.",
            "I like it when they use the way students actually speak, not corporate language.",
            "A funny line in Chichewa will stay with me longer than a whole paragraph in English.",
        ])
        language_code = True
    else:
        language = _pick(rng, [
            "The language does not move me much; I just want the message to be clear.",
            "I do not need jokes or Chichewa, I need the price and the size.",
            "English is fine for me. The words do not change the value of the bundle.",
            "Language is not my issue, as long as I understand what I am buying.",
        ])
        language_code = False

    closing = _maybe(rng, p, 0.3, _pick(rng, [
        "If those things are not on the advert, I keep scrolling.",
        "Those are the things I check before I even think of buying.",
        "So the first five seconds decide whether I stay or move on.",
        "If the advert answers those questions, then I will read the rest.",
    ]))
    codes = ["CR_PROMO_DISCOUNT"] if p.score(17) >= 4 else []
    if p.score(18) >= 4:
        codes.append("CR_VISUAL_APPEAL")
    if p.score(19) >= 4:
        codes.append("SI_INFLUENCER")
    if language_code:
        codes.append("CR_LANGUAGE_HUMOUR")
    fc = factor_code(p)
    if fc:
        codes.append(fc)
    text = " ".join(x for x in (lead, second, " ".join(extras), language, closing) if x)
    text = _ensure(text, rng, [
        "So the first few seconds decide it for me.",
        "That is what I look for before I even consider buying.",
        "I do not need much, just the numbers and the days.",
    ])
    return text, codes


# ---------------------------------------------------------------------- Q6 --
def q6(p: Respondent, rng: random.Random):
    t = p.trust_level
    complaint = rng.choice(COMPLAINTS)
    if t >= 4:
        core = _pick(rng, [
            "I trust them reasonably well, maybe four out of five. When I buy what was advertised, the bundle is usually there, and the price in the app matches what the advert said.",
            "I do trust them, especially the big networks. They cannot afford to lie openly because people would post about it.",
            "On the whole I believe the adverts. I have bought several bundles from adverts and they delivered what was promised.",
            f"I would say I trust them. I have not been given a reason to doubt them, apart from small things like {complaint}.",
            "I trust the networks more than I trust most adverts, because at the end of the day the balance is on my phone and I can check it.",
            "Yes, I believe what they say. The prices are regulated and the bundles are real; the marketing is just noise around it.",
        ])
        caveat = _pick(rng, [
            "The only thing I watch is the validity. Sometimes the advert says weekly but the data is split into night and day bundles.",
            "My only reservation is the speed after you use a certain amount, but the price and the volume are usually correct.",
            f"Once {complaint}, but I would not call it a lie, more of a technical issue.",
            "I still read the conditions, just in case, but I do not expect to be cheated.",
            "The one thing I do not trust is the word 'unlimited'. Everything else I can verify.",
            "Sometimes the advert exaggerates the coverage, but the bundle itself is fine.",
        ])
        codes = ["TR_TRUST"]
    elif t >= 3:
        core = _pick(rng, [
            "I trust them halfway. I believe the price and the volume because those are easy to check, but I do not trust the 'unlimited' language.",
            "Half and half. The bundle is real, but the experience is not always what the advert promised.",
            "I trust the numbers, not the adjectives. If it says 6GB for MK5,000, that is usually true. When it says 'fastest network', that is marketing.",
            "I would give them three out of five. The offer is there, but the conditions are not always clear.",
            "I believe the advert until I buy, then I check the balance and make up my own mind.",
            "It depends on the network. The big adverts I trust more, the small promotions I treat with suspicion.",
        ])
        caveat = _pick(rng, [
            f"I have had a case where {complaint}.",
            "Once I bought a bundle that was advertised as a week and it finished in four days, but customer care said it depends on usage.",
            "I also read the comments before I buy, because the comments tell you what the advert will not.",
            "The price is usually right, but the validity is where they play games.",
            "I have learned to screenshot the advert, because sometimes the offer changes by the time you buy.",
            "I do not trust the speed claims at all; the rest I can live with.",
        ])
        codes = ["TR_DOUBT"]
    else:
        core = _pick(rng, [
            "Not much, to be honest. What is on the poster and what you get in the app are two different things.",
            "I do not trust them. These adverts are designed to make you buy, not to inform you.",
            "I have learned to be careful. I trust the app balance more than anything the advert says.",
            "Very little. I have been disappointed enough times to take the adverts with a pinch of salt.",
            "I treat them as sales talk. The only thing I trust is what I see after I buy.",
            "I do not trust the adverts, but I still look at them, because sometimes the offer is genuine.",
        ])
        caveat = _pick(rng, [
            f"I have been disappointed before: {complaint}.",
            f"I have experienced it myself: {complaint}, and nobody explained anything.",
            "There was a promotion I bought into, and the bonus data never came.",
            "Once the app charged me twice and I had to fight for a refund.",
            "I bought what looked like a weekly bundle and it expired in three days.",
            "The advert promised double data, but the balance showed the normal amount.",
        ])
        codes = ["TR_DOUBT", "TR_MISMATCH_EXPERIENCE"]

    trust_build = _pick(rng, [
        "What makes me trust an advert is when the terms are written in full, and when people in the comments say they actually bought it.",
        "Clear terms build trust for me. If I have to zoom in to read the conditions, I already suspect something.",
        "I trust an advert when the network is known and when the same offer appears inside the official app.",
        "I trust it when a friend has used it. Word of mouth beats the advert itself.",
        "A real screen, a real balance and a real price - that is what convinces me.",
        "When the advert is short and specific, I trust it more. Long stories make me suspicious.",
        "I trust the official pages, not the sponsored posts from strange accounts.",
        "If customer care answers when I ask a question, that gives me confidence.",
    ])
    check = _maybe(rng, p, 0.4, _pick(rng, [
        "So I usually check the app before I pay, just to confirm the price is the same.",
        "I read the comments under the advert before I decide anything.",
        "I ask in the class group whether anyone has bought it.",
        "I compare the advert with the SMS confirmation after buying.",
    ]))
    depth = _pick(rng, [
        "The advert is written by the marketing people, but the bundle is run by the technical people, and I think the two do not always talk to each other.",
        "I have learned to check the app before I complain, because sometimes the bundle is there and I just did not see it.",
        "So my trust is not blind. I read the conditions, especially the part about the validity.",
        "What would help is if the advert carried the same information as the app, word for word.",
        "I think trust would improve if the networks admitted when something goes wrong instead of blaming usage.",
        "For me, honesty about the limits would sell more than big promises.",
    ])
    extra = _maybe(rng, p, 0.45, _pick(rng, [
        "I would say my trust depends on the network and on how long I have used them.",
        "The adverts that show real screens and real balances earn my trust faster.",
        "If the same offer is in the app, I believe it; if it is only on Facebook, I am careful.",
        "A friend's experience counts for more than any advert.",
    ]))
    text = " ".join(x for x in (core, caveat, trust_build, check, depth, extra) if x)
    return text, codes


# ---------------------------------------------------------------------- Q7 --
def q7(p: Respondent, rng: random.Random):
    visuals = p.score(18)
    influencers = p.score(19)
    if visuals >= 4:
        vis = _pick(rng, [
            "Videos affect me a lot. If I can see the data being used, or someone downloading a past paper in seconds, it feels real.",
            "Images work on me when they are clean. A good picture with the price in the middle will stop me.",
            "A short video with a clear message is more persuasive than a long poster full of words.",
            "I respond to visuals more than text. If the advert looks good, I will read what it says.",
        ])
    elif visuals <= 2:
        vis = _pick(rng, [
            "Images and videos do not really change my mind. I look at the numbers.",
            "For me the visuals are just decoration. I want to see the price and the size of the bundle.",
            "A nice video can catch my eye, but it will not make me buy. The value has to be there.",
            "I do not pay much attention to the design. The numbers are what matter.",
        ])
    else:
        vis = _pick(rng, [
            "The visuals help, but they are not the main thing. If the offer is good, even a plain poster will work.",
            "A good image will make me stop, but I still check the numbers before I do anything.",
            "Visuals matter a little. They get my attention, but they do not close the sale.",
        ])

    if influencers >= 4:
        inf = _pick(rng, [
            "Influencers do affect me, especially when it is someone from Malawi that I follow. I know they are paid, but it still makes the bundle feel familiar.",
            "When a fellow student or a popular person endorses a bundle, I take it more seriously. It is like a recommendation from a friend.",
            "I pay attention to influencers because they usually demonstrate the bundle on their phone.",
            "If someone I follow uses it in a video, I am more likely to consider it, even knowing it is an advert.",
            "Influencer content feels like a review, so it moves me more than a poster.",
        ])
        codes = ["SI_INFLUENCER"]
    elif influencers <= 2:
        inf = _pick(rng, [
            "Influencers do not move me at all. They are paid to say good things, so I take it as an advert and nothing more.",
            "I actually trust influencers less. If they are being paid, they will not tell you the bundle finishes early.",
            "Celebrities do not persuade me. I would rather hear from an ordinary classmate.",
            "I skip anything with a celebrity in it. It tells me the budget went to the wrong place.",
        ])
        codes = []
    else:
        inf = _pick(rng, [
            "Influencers are somewhere in the middle. If I already know the person, I listen; if not, I ignore.",
            "I do not follow influencers much, but when a classmate recommends something I take it seriously.",
            "An influencer can make me curious, but not convinced.",
            "I watch them, but I do not let them decide for me.",
        ])
        codes = []

    if rng.random() < 0.72:
        student = _pick(rng, [
            "What affects me most is student-related content. When the advert shows a lecture room, a hostel room, someone buying bundles with upkeep money, it feels like it was made for us.",
            "Student-oriented adverts carry more weight for me because they show our reality, not a businessman in an office.",
            "I like it when they mention MUBAS or use a student, because then I know they are thinking of us and not just of people with salaries.",
            "When the advert shows a student checking their balance at night, I feel seen.",
            "Adverts that talk about upkeep money and exam time speak my language.",
        ])
        codes.append("CR_STUDENT_CONTENT")
    else:
        student = _pick(rng, [
            "Student-related content does not change much for me. A student in the advert and a businessman in the advert are the same to me if the price is wrong.",
            "I do not care whether the person in the advert is a student; I care about the bundle.",
            "Those 'student' adverts feel like marketing talk to me. I still check the numbers myself.",
            "Using a student in the advert does not convince me; I know they are paid in airtime.",
        ])

    if rng.random() < 0.68:
        lang = _pick(rng, [
            "The language also matters. When they mix in Chichewa or humor, the advert feels human.",
            "And the language should not be too formal. Students respond to how we actually speak.",
            "Language is part of the picture. A slogan in Chichewa sticks longer than a paragraph in English.",
            "I like adverts that sound like a conversation, not a press statement.",
            "A bit of humour in the wording does more for me than ten graphics.",
        ])
        codes.append("CR_LANGUAGE_HUMOUR")
    else:
        lang = _pick(rng, [
            "The language does not matter much to me; English is fine as long as the message is clear.",
            "I do not need Chichewa in the advert, I just need the numbers.",
            "Humour is nice, but I do not buy because of a joke.",
            "I do not care about the wording; I care about the price.",
        ])

    example = _maybe(rng, p, 0.35, _pick(rng, [
        "There was one advert with a student in a hostel who looked genuinely surprised by the price, and that stuck with me.",
        "I remember a video where someone was counting coins to buy a bundle, and it felt very real.",
        "One advert used a lecture room I recognise, and that made me pay attention.",
        "There was a funny one in Chichewa about a guy who runs out of data in the middle of a call.",
    ]))
    if visuals >= 4:
        codes.append("CR_VISUAL_APPEAL")
    text = " ".join(x for x in (vis, inf, student, lang, example) if x)
    return text, codes


# ---------------------------------------------------------------------- Q8 --
def q8(p: Respondent, rng: random.Random):
    status = p.purchase_status
    month = rng.choice(MONTHS)
    trigger = rng.choice(TRIGGERS)
    bundle = p.bundle_example
    plat = ad_platform_text(p)
    channel = channel_text(p, rng)
    factor = p.factor.lower()

    if "price" in factor or "afford" in factor:
        attract = _pick(rng, [
            "The price was the main thing, because it was within what I could afford that week.",
            "What attracted me was the price. It was cheaper than the bundle I usually buy.",
            "The price is what did it. I am a student, so anything that saves a few hundred kwacha gets my attention.",
            "I was attracted by the amount I would save compared with my normal bundle.",
        ])
    elif "data" in factor or "volume" in factor:
        attract = _pick(rng, [
            "What attracted me was the amount of data for that price. The value per kwacha made sense.",
            "The volume is what got me. It was more gigabytes than I normally get for the same money.",
            "I was attracted by the size of the bundle; it looked like it would carry me for the whole week.",
            "The data was generous compared with what I was using before.",
        ])
    elif "validity" in factor:
        attract = _pick(rng, [
            "What attracted me was the validity. I knew the bundle would carry me for the whole week.",
            "The duration is what sold it. A bundle that lasts seven days suits my budget.",
            "I liked that it lasted long enough to be worth the money.",
            "What got me was the number of days, not the size.",
        ])
    elif "discount" in factor or "promotion" in factor:
        attract = _pick(rng, [
            "The promotion is what got me. There was a discount and I did not want to miss it.",
            "It was the bonus. You got extra data for the same price.",
            "The discount made it cheaper than what I was planning to buy.",
            "I was attracted by the offer itself, because it was running for a limited time.",
        ])
    elif "network" in factor:
        attract = _pick(rng, [
            "I trusted the network quality more than anything else.",
            "The coverage in my area is what convinced me.",
            "I bought it because I know the network works where I stay.",
            "It was the reliability. I would rather pay for data that loads.",
        ])
    else:
        attract = _pick(rng, [
            "It was convenient. I could buy from my phone without moving.",
            "I liked that I could buy it in two taps from the app.",
            "It was easy. I saw it, clicked, and it was done.",
            "The convenience of buying it immediately is what made me act.",
        ])

    month_phrase = _pick(rng, [f"In {month}", f"It was in {month}", f"During {month}",
                               f"One day in {month}", f"Around {month}"])

    if status in ("YES", "LIMITED") and p.exposure in ("Rarely", "Never"):
        core = _pick(rng, [
            f"I do not come across them often, but {month_phrase.lower()} {trigger}, and the advert for {bundle} came up on {plat}. I bought it {channel}.",
            f"The adverts rarely reach me, but I remember one from {month}: {bundle} on {plat}. I had a need at that time, so I bought it {channel}.",
        ])
        follow = _pick(rng, [
            "I would say the advert played a small part; the need was already there.",
            "It is one of the few times an advert actually moved me to buy.",
            "I have not repeated it many times since, but that one worked on me.",
            "The advert only made the decision faster, not the decision itself.",
        ])
        text = _ensure(f"{core} {attract} {follow}", rng, [
            "I would do it again if the same offer came back.",
            "I told my roommate about it afterwards.",
            "The bundle did what I needed it to do that week.",
            "It was one of the few times an advert actually reached me.",
            "I checked the balance after buying, just to be sure.",
        ])
        return text, ["PC_PURCHASED", "IM_PLANNED"]

    if status in ("YES", "LIMITED"):
        if status == "LIMITED":
            planned = _pick(rng, [
                "I would not say I planned it, but I did not regret it either.",
                "I was going to buy a bundle anyway, so the advert only decided which one.",
                "It was not a big decision; I just saw it and took it.",
                "I had not planned that particular bundle, but I needed data anyway.",
                "It was more of a try-out than a planned purchase.",
            ])
            core = _pick(rng, [
                f"{month_phrase}, {trigger}. I saw the advert for {bundle} on {plat}, and I decided to try it. I bought it {channel}.",
                f"One case I can remember was in {month}. {_sentence(trigger)}. The advert for {bundle} kept coming up on {plat}, so I bought it {channel}.",
                f"There was a time in {month} when {trigger}. I saw {bundle} advertised on {plat} and bought it {channel} to see whether it was worth it.",
            ])
            codes = ["PC_PURCHASED", "IM_PLANNED"]
        else:
            if any(k in trigger for k in ("data finished", "needed data", "expire",
                                          "assignment", "offline", "quiz", "update")):
                planned = _pick(rng, [
                    "I was going to buy data that day anyway, but the advert decided which bundle.",
                    "I had planned to buy data, just not that particular bundle.",
                    "The need was already there; the advert only pointed me to a better option.",
                    "I had to buy data, so the advert came in at the right moment.",
                ])
            else:
                planned = _pick(rng, [
                    "No, I was not planning to buy at that moment. The advert is what put the idea in my head.",
                    "I had a bundle already, but it was almost finished, so the advert came at the right time.",
                    "I had planned to buy data that day, but not that particular bundle.",
                    "I was not shopping for data, to be honest. The advert created the idea.",
                ])
            core = _pick(rng, [
                f"{month_phrase}, {trigger}. I was on {plat} and the advert for {bundle} came up, with the price written clearly. I looked at it for a while, checked the validity, and bought it {channel}.",
                f"I remember one in {month} when {trigger}. I saw {bundle} advertised on {plat}. The advert showed exactly what you get, so I did not have to think too long. I bought it {channel}.",
                f"During {month}, {trigger}, so I went to {plat} to see if there was an offer. I found the advert for {bundle}, and I bought it {channel} right there.",
                f"It was in {month}. {_sentence(trigger)}. I saw the advert for {bundle} on {plat}, and after checking the price I bought the bundle {channel}.",
                f"One evening in {month}, {trigger}. An advert for {bundle} appeared on {plat}. I bought it {channel} without looking anywhere else.",
            ])
            codes = ["PC_PURCHASED", "IM_IMPULSE"] if p.score(29) >= 4 else ["PC_PURCHASED", "IM_PLANNED"]

        follow = _pick(rng, [
            "What finally decided it was the price. I compared it in my head with what I usually buy and it was better.",
            "What decided it was the value: the bundle was bigger than what I normally get for the same money.",
            "I think it was the way the advert presented it. It made the offer look urgent and I did not want to miss it.",
            "It was a combination of the offer and the fact that I needed data at that moment.",
            "The advert was clear about what you get, and that made the decision easy.",
            "I was already thinking about buying, so the advert only confirmed it.",
            "Honestly, the discount decided it. I would have bought the normal bundle otherwise.",
            "The comments convinced me. People were saying it was worth it.",
        ])
        if p.purchase_status == "LIMITED":
            tail = _pick(rng, [
                "Since then I have bought bundles from adverts maybe once or twice, not more.",
                "It happens occasionally, but I would not say it is my normal way of buying.",
                "I have not repeated it much; I usually go back to my normal bundle.",
            ])
        elif p.trust_level <= 2.6:
            tail = _pick(rng, [
                f"I used it, although {rng.choice(COMPLAINTS)}.",
                "It worked, but not exactly the way the advert made it look.",
                "After that I became more careful about what the advert promises.",
                "The bundle was fine, though the conditions were not what I expected.",
            ])
        else:
            tail = _pick(rng, [
                "The bundle worked as advertised, so I did not regret it.",
                f"I used it and it was fine, although {rng.choice(COMPLAINTS)}.",
                "After that I started paying attention to the adverts more.",
                "I would buy it again if the offer came back.",
                "It did what it said on the advert, which is all I ask.",
            ])
        text = " ".join(x for x in (core, attract, planned, follow, tail) if x)
        text = _ensure(text, rng, [
            "I would buy it again if the offer came back.",
            "I told my friends about it afterwards.",
            "The bundle did what I needed it to do.",
            "I checked the balance the moment it loaded.",
            "That is the clearest example I can give you.",
        ])
        return text, codes

    if status == "UNSURE":
        core = _pick(rng, [
            f"It is hard to separate. I have bought {bundle} after seeing it advertised, but I cannot say the advert is what pushed me.",
            f"Maybe in {month}, but I am not certain. I saw the advert on {plat} and later bought a bundle, but I would have bought data anyway.",
            "I am not sure how to answer that, because I buy bundles all the time. Some of them I first saw in an advert, but the decision is usually about need.",
            f"There might have been one in {month}. I saw an offer on {plat} and bought data around the same time, but I cannot honestly say the advert caused it.",
        ])
        follow = _pick(rng, [
            "The advert might plant the idea, but by the time I buy, I am thinking about how much data I need and how much money I have.",
            "So I would say the advert informs me more than it decides for me. It plants the name of the bundle, and then I buy when the need comes.",
            "If I count it, maybe once or twice, but it was not a clear case of 'I saw it, so I bought it'. The advert is background noise that sometimes becomes useful.",
            "I would describe it as the advert reminding me, rather than pushing me.",
        ])
        text = _ensure(f"{core} {follow}", rng, [
            "So I would describe myself as informed but not persuaded.",
            "The advert plants the idea; my balance makes the decision.",
            "I do not feel influenced, even if I probably am.",
            "Maybe I am the exception, but that is my honest answer.",
        ])
        return text, ["PC_NOT_PURCHASED", "IM_PLANNED"]

    core = _pick(rng, [
        "I have to be honest, I have not bought a bundle because of an advert. I buy when my data finishes, usually from the app.",
        "No, not really. I see the adverts and they are interesting, but when I buy it is because I need data, not because of what I saw.",
        "I cannot point to a single time. I normally buy my bundles on a fixed day, so the adverts do not really create the purchase.",
        "No. The adverts reach me, but my buying is driven by my balance, not by what is on the timeline.",
        "I have never bought a bundle because of an advert. I buy when I run out, and I know which bundle I want before I open the app.",
        "Not that I can remember. I look at adverts, but when I buy it is a decision I had already made.",
    ])
    follow = _pick(rng, [
        "The adverts inform me, yes, and they might make me choose a different bundle, but they do not make me buy.",
        "So for me advertising works more on awareness than on the actual decision.",
        "I think if I had more money maybe the adverts would push me, but at the moment my budget decides.",
        "So the advert is useful for knowing prices, not for making me spend.",
        "I would say my need is the trigger, not the advert.",
    ])
    extra = _pick(rng, [
        "Even when an offer looks good, I compare it with what I usually buy and then go back to my normal bundle.",
        "I still look at the adverts, though. They tell me when the prices change, and that is useful.",
        "My buying is tied to my data finishing, not to what is trending on the timeline.",
        "Maybe if the offer was extremely cheap I would move, but so far I have not.",
        "I am not against advertising; I just do not let it decide for me.",
    ])
    text = _ensure(f"{core} {follow} {extra}", rng, [
        "So I would say the advert informs me, but it does not move me.",
        "I am not the type to buy because of a post.",
        "That is my honest answer, even if it is not what the networks want to hear.",
        "I still look at the adverts, though, because the prices change.",
    ])
    return text, ["PC_NOT_PURCHASED", "IM_PLANNED"]


# ---------------------------------------------------------------------- Q9 --
def q9(p: Respondent, rng: random.Random):
    label = compare_text(p)
    plat = ad_platform_text(p)
    pnet = p.primary_network

    if label == "always":
        core = _pick(rng, [
            "I always compare before I buy. I open the app, look at the price per GB, and check how long the bundle lasts.",
            "I compare every time. I will look at the bundle I saw advertised and then check what the other network is offering for the same money.",
            "Always. I do not buy the first thing I see, even if the advert is nice.",
            "I compare without fail. It is the only way to know whether the offer is real.",
            "Every time, even when I am in a hurry.",
        ])
        codes = ["CP_COMPARE_ALWAYS"]
    elif label == "often":
        core = _pick(rng, [
            "I compare often, though not every single time. If the advert is for a bundle I already know, I just buy.",
            "Most of the time I compare, especially when the amount involved is more than a thousand kwacha.",
            "I usually compare. The advert starts the process, then I go and check.",
            "Often, yes. If it is a small daily bundle I might not bother, but for weekly and monthly I compare.",
            "I would say I compare more often than not.",
        ])
        codes = ["CP_COMPARE_SOMETIMES"]
    elif label == "sometimes":
        core = _pick(rng, [
            "Sometimes I compare, sometimes I just buy. It depends on how urgent the need is.",
            "I compare when I have time. If I am in a hurry, I buy the first reasonable offer.",
            "Not always. If the advert is clear and the price is what I normally pay, I do not see the need to compare.",
            "It depends on the offer. If it is something new, I compare; if it is my usual bundle, I do not.",
            "Half the time. When I am busy with school I just buy and move on.",
        ])
        codes = ["CP_COMPARE_SOMETIMES"]
    elif label == "rarely":
        core = _pick(rng, [
            "Rarely. I know what I normally buy, so I do not spend time comparing.",
            "Not really. I usually buy the same bundle every week.",
            "Very rarely. Maybe if the advert is for a bundle I have never used.",
            "I do not compare much. I know my bundle and I stick to it.",
            "Almost never. Comparing takes time and my mind is usually made up.",
        ])
        codes = ["CP_LITTLE_COMPARISON"]
    else:
        core = _pick(rng, [
            "I do not compare at all. When my data is finished I just buy what I know.",
            "Never. Comparing takes time and the difference is usually small.",
            "Honestly no. I see the advert, I buy, and I move on.",
            "I have never compared. I know which bundle works for me.",
            "Not at all. I just buy the one I always buy.",
        ])
        codes = ["CP_LITTLE_COMPARISON"]

    inside = _pick(rng, [
        "What I compare is price per GB, the validity, and whether the bundle works at night.",
        "I look at three things: the price, how many gigabytes, and how many days.",
        "I compare the volume and the validity. A bundle that looks cheap but lasts one day is expensive.",
        "I compare across networks, because the same money can give you very different bundles.",
        "I check the price per gigabyte, because the headline price can hide a small bundle.",
        "I compare the bundle size, the price and whether it includes calls or SMS.",
        "I look at what my money buys, not just what the advert says.",
        "I compare the offer with what I bought last time, to see whether prices have moved.",
        "I check the expiry date and the speed, not just the price.",
        "I compare what the same amount of money buys on each network.",
    ])
    search = _pick(rng, [
        f"I also check the comments on the advert and ask in the class WhatsApp group before I commit.",
        f"If the advert is on {plat}, I read the comments to see whether people say it is genuine.",
        "I do not search much online; I ask a friend or check the network app.",
        "I check the network app to confirm the bundle is real before I pay.",
        "I look at the network's official page, not the sponsored post.",
        "Sometimes I search the bundle name to see what other students are saying.",
        "I ask my roommate, because they buy a lot of bundles.",
        "I check the app first, then compare with the other network's app.",
    ])
    closing = _pick(rng, [
        "The advertisement is what puts the offer in front of me, but the comparison is mine.",
        "So the advert starts the conversation, and then I do my own homework.",
        "I use the advert as a starting point, not as the answer.",
        "In short, advertising points me to offers, but comparing is how I protect my money.",
        "The advert sells; the comparison decides.",
        "That is how I avoid buying something that looks good but is not worth it.",
        "So for me, comparing is part of buying, not a separate thing.",
        "The advert is the notice; the comparison is the decision.",
        "I never buy the first thing I see, even if it looks cheap.",
        "Two minutes of checking saves me a week of regret.",
        "I would rather compare and wait than buy and complain.",
    ])
    depth = _pick(rng, [
        "When the need is urgent, though, comparison goes out of the window and I just buy.",
        "If I am in a lecture and my data finishes, I will not start comparing.",
        "Comparison is a luxury when you are desperate for data.",
        "I only compare properly when I have time and data to spare.",
        "I also compare with what I bought last time, so I know whether the prices have moved.",
        "The problem is that the comparison takes data, which is exactly what I am trying to buy.",
        "Sometimes the difference is so small that comparing wastes time.",
        "I have made mistakes before by not comparing, so now I try to be careful.",
        "I think students who do not compare end up paying more for less.",
    ])
    fc = factor_code(p)
    if fc:
        codes.append(fc)
    extra = _maybe(rng, p, 0.45, _pick(rng, [
        "If the prices are close, I stay with the network I know.",
        "I do not enjoy comparing, but I have learned that it saves money.",
        "It would be easier if the networks showed the price per gigabyte on the advert.",
        "I compare more carefully when I am buying for the month than for the day.",
    ]))
    text = " ".join(x for x in (core, inside, search, closing, depth, extra) if x)
    return text, codes


# --------------------------------------------------------------------- Q10 --
PROBE_12_PLANNED = [
    "Nothing changes the following week, because I bought what I planned.",
    "I have a small cushion for emergencies and that is enough.",
    "I do not check my balance anxiously, because there are no surprises.",
    "I think most students could plan better if they tracked their usage.",
    "If I do buy early, I replace it later from the same budget.",
    "I have been buying the same bundle for months.",
    "The advert is useful for prices, not for decisions.",
    "Waiting a day usually kills the temptation.",
    "I have trained myself to buy in the morning, before the adverts catch me.",
    "My budget is small, so there is no room for surprises.",
]

PROBE_10_STAY = [
    "If the difference were big enough, I would consider moving, but it would have to be worth the trouble.",
    "What usually stops me is the thought of telling everyone a new number.",
    "I would rather adjust my bundle than change the network.",
    "The advert has to be really convincing before I change anything.",
    "I think loyalty is worth something, even if the adverts say otherwise.",
    "I would change if my whole class moved, not because of an advert.",
    "The network I use is part of my routine now.",
    "I have thought about switching, but never because of one advert.",
    "If the offer was permanent, not just a promotion, I would consider it.",
    "Changing would mean losing the people who know my number.",
]

PROBE_10_SWITCH = [
    "I would do it again if the offer was that good, but I would compare first.",
    "What I learned is that the saving has to be real, not just the advert talking.",
    "Since then I check both networks before I buy anything.",
    "My friends did the same thing that month, so I did not feel alone.",
    "I still keep both lines, because each one has its moments.",
    "The switch taught me to read the validity before I pay.",
    "I would only move again for a promotion, not for a normal price.",
    "It was worth it that month, but I would not make a habit of it.",
    "I told my roommate about the offer, and they moved too.",
    "In the end the advert was right about the value, and I was glad I tried.",
]



def q10(p: Respondent, rng: random.Random):
    a = p.primary_network
    b = "Airtel" if a == "TNM" else "TNM"
    codes: list[str] = []
    parts: list[str] = []

    if not p.dual_network:
        core = _pick(rng, [
            f"I have not moved network. I only have {a}, so the only thing an advert can change is which of their bundles I take.",
            f"Not the network. I am on {a} alone, so the decision is always about the bundle size, not the brand.",
            f"I cannot change network because I only have {a}; the advert only makes me choose a different bundle.",
            "Within the same network, yes. The advert might push me from a daily to a weekly bundle, but that is all.",
            f"No network change. I have been on {a} since I started using a phone.",
        ])
        why = _pick(rng, [
            "It is the value per kwacha that changes my mind, not the brand.",
            "The promotion made the bigger bundle look cheaper than buying small bundles daily.",
            "I changed because the advert showed a bonus that the small bundle does not have.",
            "The advert showed a better bundle for the same money, so I took it.",
            "I just wait for a good offer on the same network.",
        ])
        outcome = _pick(rng, [
            f"So I still use {a}, but the advert decides which of their bundles I take.",
            "In the end I bought the bigger bundle once, then went back to my normal one.",
            "The network stays, the bundle changes.",
            f"I stayed with {a}, only the size changed.",
            "So the brand does not change, only the package.",
        ])
        parts = [core, why, outcome]
        codes = ["PC_CHANGED_CHOICE"]
    elif p.score(22) >= 4 or p.persuasion >= 3.7:
        core = _pick(rng, [
            f"Yes, that has happened. I went in intending to buy my usual bundle on {a}, and then I saw an advert for a better offer on {b} and I changed.",
            f"Once. I was going to buy the {a} weekly bundle, but an advert on social media showed a bigger bundle for almost the same price on {b}, so I tried it.",
            f"Yes, more than once. I usually start with {a}, but if the advert shows a promotion on the other network, I move.",
            f"Definitely. The advert made me reconsider which network to buy from.",
            f"I have switched bundles because of an advert, and once I switched network for a month.",
        ])
        why = _pick(rng, [
            "What changed my mind was the price for the volume. The difference was too big to ignore.",
            "The discount is what did it. The advert showed the old price crossed out and I decided on the spot.",
            "It was the way they showed the bundle working. It convinced me that the offer was real.",
            "My friends were talking about the same offer in the class group, so I decided to try it.",
            "The advert compared the two bundles side by side, and the other one looked better value.",
            "I changed because the offer included bonus data that my usual bundle does not have.",
        ])
        outcome = _pick(rng, [
            f"In the end I bought the {b} bundle, and I have been mixing the two networks since then.",
            f"I bought the {b} one, though I did not stay with it for long.",
            f"I moved to {b} for that month, then went back to {a}.",
            f"I bought the advertised bundle once, and I still use it when the promotion comes back.",
            f"I switched for that week, but I kept my {a} line.",
        ])
        parts = [core, why, outcome]
        codes = ["PC_CHANGED_CHOICE"]
    elif p.score(22) <= 2:
        core = _pick(rng, [
            f"Not really. I am loyal to {a}; it would take a very big difference to move me.",
            f"No. I see the adverts for the other network, but I do not change because my people are on {a} and the bundles are familiar.",
            f"I have not changed network because of an advert. I might change the size of the bundle, but not the network.",
            f"I cannot say an advert has changed my decision. I am comfortable with {a}.",
            f"No, my choice has stayed the same. I know what works for me.",
        ])
        why = _pick(rng, [
            "Changing networks means telling everybody your new number, and that is a cost on its own.",
            "The savings would have to be serious for me to move. Right now the difference is small.",
            "I do not want the stress of a new line. I just adjust what I buy.",
            "The network quality where I stay is good, so I do not see why I should move.",
            "I have been with them for years; the relationship matters to me.",
        ])
        outcome = _pick(rng, [
            f"So I stay with {a} and buy what fits my budget.",
            "The adverts inform me, but loyalty wins.",
            "Maybe one day, but not because of an advert alone.",
            "So my decision has not changed, and I doubt it will soon.",
            "For now I am not moving anywhere.",
        ])
        parts = [core, why, outcome]
        codes = ["PC_BRAND_LOYAL"]
    else:
        core = _pick(rng, [
            f"Not the network, no. But the bundle size, yes. I might plan to buy the small bundle and end up buying the bigger one because of an advert.",
            "I have changed the bundle I buy, but not the network. The advert makes me think bigger.",
            "Only within the same network. I will move from a daily to a weekly bundle if the advert shows a better deal.",
            "The brand stays the same; the bundle changes depending on what is advertised.",
        ])
        why = _pick(rng, [
            "It is the value per kwacha that changes my mind, not the brand.",
            "The promotion made the bigger bundle look cheaper than buying small bundles daily.",
            "I changed because the advert showed a bonus that the small bundle does not have.",
            "It was the timing. The offer came when I needed data, so I took the bigger one.",
        ])
        outcome = _pick(rng, [
            f"So I still use {a}, but the advert decides which of their bundles I take.",
            "In the end I bought the bigger bundle once, then went back to my normal one.",
            "The network stays, the bundle changes.",
            f"I stayed with {a}, only the size changed.",
        ])
        parts = [core, why, outcome]
        codes = ["PC_CHANGED_CHOICE"]

    parts.append(_pick(rng, [
        "I think timing matters too. When money is low I do not even open the adverts, so the influence depends on the month.",
        "For me the network decision is also emotional. If I have been with them for years, I give them a chance.",
        "What I have learned is that the advert is a proposal, not a command.",
        "In the end I ask myself whether the saving is worth the trouble of moving.",
        "The advert can push me to compare, but the decision stays with me.",
        "I do not make these decisions quickly; I like to see the offer twice before I move.",
        "The last word always belongs to the price.",
    ]))
    parts.append(rng.choice(PROBE_10_STAY if "PC_CHANGED_CHOICE" not in codes or not p.dual_network else PROBE_10_SWITCH))
    return " ".join(x for x in parts if x), codes


# --------------------------------------------------------------------- Q11 --
def q11(p: Respondent, rng: random.Random):
    if rng.random() < 0.82:
        peer = _pick(rng, [
            "Friends and classmates play a big role. If two or three people in my group say a bundle is good, I will try it.",
            "My classmates influence me more than the adverts do. We forward offers in the class WhatsApp group and discuss them.",
            "Word of mouth from friends is strong. An advert I can ignore, but a friend saying 'I bought this and it is worth it' I will act on.",
            "I share adverts with my friends and they share with me. That is how most offers reach me, actually.",
            "My roommates and I compare bundles all the time, so their opinion matters.",
            "If a classmate says the bundle is worth it, I listen more than I listen to the advert.",
            "We have a group where people post offers, so I hear about them from friends first.",
            "Peer pressure is real; when everyone is buying a certain bundle, you want to try it too.",
        ])
        codes = ["SI_PEER"]
    else:
        peer = _pick(rng, [
            "Friends and classmates do not really influence what bundle I buy. We talk about offers, but each person decides alone.",
            "I would not say my friends decide for me. We discuss bundles, but my budget is my own.",
            "Not much. I listen to them, but I buy what I can afford.",
            "My friends talk about bundles, but I do not let that change my plan.",
        ])
        codes = []

    if p.score(19) >= 4:
        inf = _pick(rng, [
            "Influencers also matter, especially the local ones who show the bundle on their phone. They make it look real.",
            "When an influencer I follow uses a bundle, I am more curious. It feels like a demonstration rather than a sales pitch.",
            "I follow a few influencers, and yes, their endorsements make me consider offers I would otherwise skip.",
            "If someone I follow shows the speed and the balance, I take it as proof.",
            "Influencers I trust can move me, especially when they are honest about the limits.",
        ])
        codes.append("SI_INFLUENCER")
    elif p.score(19) <= 2:
        inf = _pick(rng, [
            "Influencers, not so much. I know they are paid and they will say anything.",
            "I ignore celebrity endorsements. They do not use those bundles in real life.",
            "Influencers have little effect on me. A friend's opinion is worth ten influencers.",
            "I scroll past influencer adverts; they feel like a performance.",
        ])
    else:
        inf = _pick(rng, [
            "Influencers are neutral for me. If I know them, maybe; if not, I scroll.",
            "I listen to influencers only when they are people I already trust.",
            "I see influencers, but they do not decide anything for me.",
            "An influencer can make me pause, but not buy.",
        ])

    if rng.random() < 0.72:
        comments = _pick(rng, [
            "I also read the comments. If people are complaining that they bought and got nothing, that is a red flag for me.",
            "Comments can kill an advert. One person saying 'this is a scam' and I am gone.",
            "I read comments to see the real experience. Sometimes the comments are more honest than the advert.",
            "I check what people are saying under the post before I spend anything.",
            "The comments are where you find the truth about a bundle.",
            "I look for comments from people who actually bought it, not just reactions.",
        ])
        codes.append("CH_MISLEADING")
    else:
        comments = _pick(rng, [
            "I do not read the comments much. I check the app and decide.",
            "I rarely look at the comments; people complain about everything anyway.",
            "Comments are not my thing; I would rather test the bundle myself.",
        ])

    depth = _pick(rng, [
        "We forward adverts to each other almost every week, so by the time I see one I have already heard an opinion.",
        "Students trust other students more than they trust the networks, I think.",
        "But there is a limit. If a friend recommends something every day, you start to wonder whether they are being paid.",
        "The class group is where most offers reach me, honestly, more than the timeline.",
        "A recommendation from someone in my situation is worth more than a celebrity advert.",
        "The danger is that everyone forwards the same offer, and then it feels like it must be good.",
        "I think we influence each other more than we admit.",
    ])
    sharing = _maybe(rng, p, 0.5, _pick(rng, [
        "When an offer looks good, my first move is to send it to the group and see what people say.",
        "I trust a bundle more when a friend has already tested it.",
        "We compare notes after buying, and that is how we learn which offers are real.",
        "If nobody in my circle has tried it, I am less likely to be the first.",
        "The group is useful because people post when something goes wrong, not only when it is good.",
    ]))
    text = " ".join(x for x in (peer, inf, comments, depth, sharing) if x)
    return text, codes


# --------------------------------------------------------------------- Q12 --
def q12(p: Respondent, rng: random.Random):
    impulse = p.score(29)
    discount = p.score(17)

    if impulse >= 4 and p.purchase_status == "UNSURE":
        core = _pick(rng, [
            "Maybe once or twice, but I cannot clearly separate it from normal buying. I buy bundles I had not planned for, and some of them I had seen advertised.",
            "It is possible, but I would not swear to it. I know I have bought data outside my plan; whether the advert caused it, I am not sure.",
            "I think so, but I am not sure I can give you a clean example.",
        ])
        example = _pick(rng, [
            "There was a week I topped up twice, and one of those bundles I had seen advertised that same day.",
            "I remember buying a weekly bundle in the middle of the week, which was not my plan.",
            "I once bought a night bundle after seeing an offer, even though I had some data left.",
        ])
        why = _pick(rng, [
            "So for me the advert and the need work together, and I cannot say which one won.",
            "I would describe it as the advert reminding me, rather than pushing me.",
            "The advert made the option visible; the need made me act.",
        ])
        text = _ensure(f"{core} {example} {why}", rng, [
            "I would not call it a habit, though.",
            "It happens more when I have just received money.",
            "I notice it in my budget afterwards.",
            "I am trying to be more careful with these offers.",
        ])
        return text, ["IM_IMPULSE"]

    if impulse >= 4 and p.purchase_status == "NO":
        core = _pick(rng, [
            "I do buy bundles I had not planned for, but not because of the advert. It is usually because my data finished earlier than I expected.",
            "Yes, unplanned purchases happen to me, though I would put it down to need rather than advertising. When the data is gone, I buy.",
            "It happens, but the advert is not the reason. I buy outside my plan when I have to, for example in the middle of an assignment.",
            "I do buy outside my plan sometimes, but the trigger is my usage, not the advert.",
        ])
        example = _pick(rng, [
            "There was a week I bought three small bundles because the first two disappeared fast.",
            "Last month I bought an extra weekly bundle in the middle of the week, which I had not planned.",
            "I remember topping up twice in one day, but that was because I was downloading notes.",
            "I once bought a bundle at midnight because I still had an assignment to submit.",
        ])
        why = _pick(rng, [
            "So I would say advertising makes me aware, but it does not make me buy. My usage does.",
            "The offers are attractive, but I cannot say I have bought something only because of an advert.",
            "It is need and convenience, not the beauty of the advert.",
            "So the unplanned part is real, but it is not the advert's doing.",
        ])
        text = _ensure(f"{core} {example} {why}", rng, [
            "So the unplanned part is real, but it is not the advert's doing.",
            "It happens more at the end of the month.",
            "I have started keeping a small reserve for those moments.",
            "I do not regret it, but I notice it in my budget.",
        ])
        return text, ["IM_IMPULSE", "PC_NOT_PURCHASED"]

    if impulse >= 4 and p.purchase_status == "LIMITED":
        core = _pick(rng, [
            "It has happened, though not as often as the adverts would like. Every few months I buy a bundle that was not in my plan.",
            "Yes, occasionally. I would not call it a habit, but there are times the offer catches me at a weak moment.",
            "Once in a while. I am usually disciplined, but a good promotion can break me.",
        ])
        example = _pick(rng, [
            "The last one was a weekend promotion with bonus data. I still had data, but I bought it anyway.",
            "There was a night bundle offer I bought while lying in bed, without checking my balance.",
            "I bought a bigger bundle than I needed because the advert showed a discount.",
        ])
        why = _pick(rng, [
            "It was the attractiveness of the offer, not need. That is why it does not happen every week.",
            "It was convenience and the promotion together. I could buy it in two taps, so I did.",
            "The advert made the offer feel urgent, and I acted before thinking.",
        ])
        text = _ensure(f"{core} {example} {why}", rng, [
            "It is not something I do every week.",
            "I usually notice it when I check my balance.",
            "It happens more when I have just been paid.",
            "I tell myself I will be more careful next time.",
        ])
        return text, ["IM_IMPULSE"]

    if impulse >= 4:
        core = _pick(rng, [
            "Yes, it happens. I will see an advert and buy a bundle that was not in my plan for the week.",
            "It has happened more than once. The advert makes the offer look like it is about to disappear, so I buy.",
            "Yes. Especially when there is a promotion, I end up buying data I did not plan for.",
            "All the time, honestly. If the offer looks good, I buy first and think later.",
            "It happens, especially at night when I am scrolling and my resistance is low.",
        ])
        example = _pick(rng, [
            f"The last one was {p.bundle_example}. I saw it on {ad_platform_text(p)} and bought it the same day.",
            "There was a weekend promotion with bonus data and I bought it even though I still had data.",
            "I saw a limited offer while I was in bed and bought it there and then. I did not even check my balance.",
            "I once bought three bundles in one week because each advert looked better than the last.",
            "I bought a night bundle I did not need simply because the price looked low.",
        ])
        why = _pick(rng, [
            "It was the attractiveness of the offer, not need. I did not need it, but the price looked too good.",
            "It was a mix of convenience and the offer. I could buy it in two taps, so I did.",
            "What encouraged me was the urgency in the advert, the countdown and the 'today only' language.",
            "The advert made it feel like a bargain I would regret missing.",
            "It was pure impulse. The offer was there, I had money, and I clicked.",
        ])
        codes = ["IM_IMPULSE"]
    elif impulse == 3 and p.purchase_status in ("NO", "UNSURE"):
        core = _pick(rng, [
            "Sometimes I am tempted, but I would not say the advert makes me buy. I usually stay within my plan.",
            "It depends. The advert can make me want the bundle, but whether I buy is another question.",
            "Once in a while I think about it, but I cannot point to a bundle I bought only because of an advert.",
        ])
        example = _pick(rng, [
            "There are offers I have seen and wanted, but by the time I get money the moment has passed.",
            "Maybe I have bought a bundle on the same day I saw an advert, but I was going to buy data anyway.",
            "I have looked at an offer, checked the price, and left it.",
        ])
        why = _pick(rng, [
            "So the temptation is real, but my budget usually wins.",
            "For me the advert raises interest; it does not close the sale.",
            "I would call it influence on what I consider, not on what I buy.",
        ])
        text = _ensure(f"{core} {example} {why}", rng, [
            "So my plan usually holds.",
            "I am careful because data is a big part of my spending.",
            "It takes a very good offer to move me.",
            "I would rather wait than spend outside my budget.",
        ])
        return text, ["IM_PLANNED", "BD_SPEND_CAP"]
    elif impulse == 3:
        core = _pick(rng, [
            "Not often. I usually stay within my plan, though a good offer can make me think twice.",
            "It depends on the month. When money is tight I just scroll; when I have a little extra I might consider it.",
            "Only once in a while, and usually I go back to my usual bundle.",
            "Rarely. I am careful with data because I am careful with money.",
        ])
        example = _pick(rng, [
            f"I have looked twice at {p.bundle_example} when it was on promotion, but I did not always buy.",
            "There are offers I have wanted, but by the time I get money the moment has passed.",
            "Maybe I have bought data on the same day I saw an advert, but I was going to buy data anyway.",
            "I have come close, especially with night bundles.",
        ])
        why = _pick(rng, [
            "So the advert raises my interest; my plan decides what I actually buy.",
            "I would call it influence on what I consider, not on what I spend.",
            "The discount catches my eye, but it does not move my budget.",
            "For me the need comes first, the advert second.",
        ])
        codes = ["IM_PLANNED", "BD_SPEND_CAP"]
    else:
        core = _pick(rng, [
            "Not really. I plan my bundles, so I know what I am going to buy before I open social media.",
            "Rarely. I have a budget and I try to stay within it.",
            "No, I am careful. If I do not need data, an advert will not make me buy.",
            "I do not remember the last time an advert made me buy something outside my plan.",
            "I am disciplined about data. I buy what I budgeted for.",
        ])
        example = _pick(rng, [
            "If it happens, it is small, maybe an extra daily bundle when I am travelling.",
            "I cannot remember a time I bought something I did not plan for.",
            "Maybe once when there was a big promotion, but I would not count it.",
            "At most I have switched the size of the bundle, not added a new one.",
        ])
        why = _pick(rng, [
            "For me the need comes first. The advert can only suggest, not decide.",
            "I look at my budget first and then at the advert. Usually the budget says no.",
            "I have learned to ignore the urgency language. That 'last chance' is there every week.",
            "I remind myself that the offer will still be there tomorrow.",
        ])
        codes = ["IM_PLANNED", "BD_SPEND_CAP"]

    impulsive = "IM_IMPULSE" in codes
    if impulsive:
        depth = _pick(rng, [
            "At the end of the day the choice is still mine, so I do not blame the networks.",
            "My roommate is worse than me; they buy almost every promotion they see.",
            "I think this is why students run out of upkeep money before the month ends.",
            "I have started muting some of those pages, especially when I am broke.",
            "The adverts know what they are doing, but I am learning to resist.",
            "I notice it happens more at the end of the month than at the beginning.",
            "When I am stressed with school work, I buy more.",
            "I have learned to put a limit on my phone wallet, which helps.",
            "If I look at my statement at the end of the month, I can see the pattern.",
            "It is embarrassing when I add it up, so I try not to think about it.",
        ])
        extra = _maybe(rng, p, 0.45, _pick(rng, [
            "I do not regret the unplanned purchases, but I notice them in my budget.",
            "It happens more when I have just received money.",
            "The adverts are good at making you feel like you are missing out.",
            "I am getting better at ignoring the countdowns.",
        ]))
        probe = rng.choice(PROBE_12)
    else:
        depth = _pick(rng, [
            "At the end of the day the choice is still mine, so I do not blame the networks.",
            "I think this is why other students run out of upkeep money before the month ends.",
            "I have muted some of those pages anyway, because the offers are just noise.",
            "The adverts know what they are doing, but I have learned to resist.",
            "It is easier to resist when you have a budget written down.",
            "My roommate is the opposite; they buy almost every promotion they see.",
            "I keep a small reserve for emergencies, and that protects my plan.",
            "I check my balance before I open social media, and that keeps me honest.",
            "When money is tight I delete the apps for a few days.",
            "I think planning is the only real defence against these adverts.",
        ])
        extra = _maybe(rng, p, 0.45, _pick(rng, [
            "I would rather miss an offer than break my budget.",
            "It is not that I do not see the adverts; I choose not to act.",
            "My plan is simple and I stick to it.",
            "I have been doing this long enough to know my usage.",
        ]))
        probe = rng.choice(PROBE_12_PLANNED)
    text = " ".join(x for x in (core, example, why, depth, extra, probe) if x)
    return text, codes


# --------------------------------------------------------------------- Q13 --
def q13(p: Respondent, rng: random.Random):
    spend = p.weekly_spend
    plan = _pick(rng, [
        f"I spend {spend} on bundles, so I have to plan. I usually buy one main bundle at the beginning of the week and then small ones when it runs out.",
        f"My budget is {spend}. I buy the main bundle first, then I only top up if there is an emergency.",
        f"I spend {spend}, and honestly it is already a lot for a student. I plan by buying weekly instead of daily, because daily bundles are more expensive in the long run.",
        f"I budget {spend} for data. I write it down with my other expenses, otherwise it disappears.",
        f"Data is a fixed line in my budget, {spend}. I decide on the bundle at the start of the week and try not to add more.",
        f"I spend {spend} on bundles. I buy in bulk when I can, because smaller bundles eat money.",
        f"My data budget is {spend}. When the money is finished, I wait for the next week.",
        f"I set aside {spend} for bundles. If I overspend, I borrow data or wait.",
    ])
    if p.score(17) >= 4:
        disc = _pick(rng, [
            "Discounts do encourage me to spend more. When I see a promotion I sometimes spend money I had set aside for something else.",
            "Yes, a discount can push me above my plan. That is why I try not to open the app when I am broke.",
            "Promotions are dangerous for my budget. They make me buy more data than I need.",
            "A good discount will make me buy earlier than I planned.",
            "I am a victim of promotions, honestly. If the offer is good, I find the money.",
        ])
        codes = ["CR_PROMO_DISCOUNT"]
    else:
        disc = _pick(rng, [
            "Discounts do not move me much. If I did not plan for it, I skip it, even with a discount.",
            "I like discounts, but I do not let them change my budget.",
            "A promotion is nice, but my budget is fixed. I compare the discount against what I actually need.",
            "I look at promotions, but I rarely let them change my plan.",
            "Discounts are a bonus, not a reason to spend.",
        ])
        codes = ["BD_SPEND_CAP"]

    volume = _pick(rng, [
        "The amount of data matters because I would rather buy a big bundle once than keep buying small ones. It is cheaper per GB.",
        "I look at volume against validity. A huge bundle that expires in a day is not useful to me.",
        "Data volume is what I check first, then the price. If the volume is not enough for the week, I do not buy.",
        "I calculate how many gigabytes I need for the week, and then I look for that size.",
        "A small bundle that lasts a week is better than a big one that finishes in two days.",
        "I would rather pay more for enough data than run out in the middle of an assignment.",
        "Volume and validity have to match my usage. I do not want data that expires before I use it.",
    ])
    need = _pick(rng, [
        "At the end of the day, need decides. If I have data, I do not buy, no matter how good the advert is.",
        "I ask myself one question: do I need this now? If the answer is no, the advert can wait.",
        "I try to separate the excitement of the advert from the actual need. It is not always easy.",
        "My rule is simple: if I still have data, I do not buy more.",
        "I check my balance first. If there is enough, I close the app.",
        "I ask whether the bundle will still matter next week. If not, I skip it.",
        "I think students need to plan, because the adverts will never stop coming.",
        "I check the size against what I actually use in a week before I pay.",
        "The advert can talk, but my balance has the final vote.",
        "If the bundle is not going to change my week, I leave it.",
        "I ask myself whether I would buy this if there were no discount. Usually the answer is no.",
        "I have a figure in my head for data, and I do not go above it.",
    ])
    text = " ".join(x for x in (plan, disc, volume, need) if x)
    return text, codes


# --------------------------------------------------------------------- Q14 --
FACTOR_LEAD = {
    "DF_PRICE": [
        "Price, first and foremost. If it is not affordable, nothing else matters.",
        "Affordability. I look at how much it costs before anything else.",
        "The price. I am a student, so the money is the first filter.",
        "Cost, plain and simple. A good bundle I cannot afford is still useless to me.",
    ],
    "DF_DATA_VOLUME": [
        "The amount of data. I want value for what I pay, so the volume has to be worth it.",
        "Data volume is the biggest factor for me. I use a lot of data for school and entertainment.",
        "How many gigabytes I get. That is what I compare before the price.",
        "The size of the bundle. If it is too small, the price does not matter.",
    ],
    "DF_VALIDITY": [
        "How long the bundle lasts. I would rather pay more for a weekly bundle than buy daily.",
        "The validity period. A bundle is only useful if it lasts long enough.",
        "The number of days I get. A cheap bundle that expires tomorrow is not cheap.",
        "Duration is the deal breaker for me. I want data that will still be there when I need it.",
    ],
    "DF_PROMOTION": [
        "The promotion. If there is a discount or bonus, I am interested.",
        "A good promotion is what makes me move, even before the volume.",
        "Discounts and bonuses, because they change the value of the bundle.",
        "The offer itself. If it is a real promotion, I will take a second look.",
    ],
    "DF_NETWORK_QUALITY": [
        "Network reliability. I would rather pay a bit more and have internet that works.",
        "The quality of the network. A cheap bundle on a dead network is useless.",
        "Coverage and speed. That is the first thing for me.",
        "Whether the network actually works where I stay. Everything else is secondary.",
    ],
    "DF_RECOMMENDATION": [
        "Recommendations. If people I trust have used it, I am more willing.",
        "What my friends and classmates say carries the most weight.",
        "Peer recommendation. It beats any advert.",
        "The recommendation from other students, because they have nothing to sell.",
    ],
    "DF_CONVENIENCE": [
        "Convenience. I want to buy quickly from my phone without looking for an agent.",
        "Ease of buying. If it takes long to purchase, I lose interest.",
        "The convenience of buying it right away, without looking for an agent.",
        "How easy it is to buy. Two clicks and I am done.",
    ],
}


def q14(p: Respondent, rng: random.Random):
    fc = factor_code(p)
    code = fc or "DF_PRICE"
    lead_text = rng.choice(FACTOR_LEAD[code])

    followers = [
        ("After that, validity. There is no point buying data that expires before I use it.", "DF_VALIDITY"),
        ("After that, network quality, because data that does not load is a waste.", "DF_NETWORK_QUALITY"),
        ("After that, the volume, because I need enough to carry me through the week.", "DF_DATA_VOLUME"),
        ("After that, convenience. I want to buy from the app without stress.", "DF_CONVENIENCE"),
        ("After that, the price, because a good bundle I cannot afford is still useless.", "DF_PRICE"),
        ("After that, whether there is a promotion running.", "DF_PROMOTION"),
        ("After that, what my friends say about it.", "DF_RECOMMENDATION"),
        ("Then the network quality, because I have been burned by slow data before.", "DF_NETWORK_QUALITY"),
    ]
    followers = [f for f in followers if f[1] != code]
    second_text, _second_code = rng.choice(followers)
    third_options = [
        "Recommendations matter less to me; I would rather test it myself.",
        "I do not care much about celebrity adverts; the numbers decide.",
        "The advert itself only matters if those first things are right.",
        "If the first two things are right, I will buy without reading the rest.",
        "The network's reputation matters, but not as much as the numbers.",
        "I will look at the comments, but they do not change my mind.",
        "I do not need a fancy advert, just clear information.",
        "I check the balance after buying, and that is my final test.",
    ]
    if code != "DF_PROMOTION":
        third_options.append("Promotions are a bonus, not the main reason.")
    third = rng.choice(third_options)
    closing = _pick(rng, [
        "That is the order in my head when I see an advert.",
        "So when I open an advert, that is what I am checking.",
        "That is how I decide, and the advert only helps if it answers those questions.",
        "So those are the things I weigh before spending.",
        "That is my checklist, more or less.",
        "If an advert answers those, I will consider it seriously.",
        "That is how I choose, and it has worked for me so far.",
        "So those are the things that decide it for me, in that order.",
        "I do not think I am unusual; most students probably think the same way.",
        "If an advert answers those, then we can talk.",
    ])
    depth = _pick(rng, [
        "When I am buying for the month I think differently; I look for the biggest bundle. For daily use I just want the cheapest.",
        "And if the network is slow, I do not care how cheap it was; I feel cheated either way.",
        "Sometimes the advert only makes me aware; the actual decision is made in the app when I see my balance.",
        "I have also learned to look at the price per gigabyte rather than the headline price.",
        "The advert matters most for the first thing; after that it is just noise.",
        "I think most students would say the same, even if they do not say it in those words.",
        "My answer changes a bit at the end of the month, when money is tight.",
        "I would say the order changes depending on whether I am buying for the day or the month.",
        "The advert matters most in the first few seconds; after that I am on my own.",
    ])
    text = " ".join(x for x in (lead_text, second_text, third, closing, depth, rng.choice(PROBE_14)) if x)
    return text, ([code])


# --------------------------------------------------------------------- Q15 --
def q15(p: Respondent, rng: random.Random):
    complaint = rng.choice(COMPLAINTS)
    if p.trust_level <= 2.6 or p.score(15) <= 2:
        core = _pick(rng, [
            f"Yes, more than once. {_sentence(complaint)}.",
            f"I have had a problem. {_sentence(complaint)}.",
            f"Yes. {_sentence(complaint)}. Nobody warns you about that in the advert.",
            f"Several times. {_sentence(complaint)}.",
            f"Yes, and it has made me careful. {_sentence(complaint)}.",
        ])
        detail = _pick(rng, [
            "The offer was not different from what was advertised, but the experience was. The terms were not clear at all.",
            "When I complained they said it depends on usage, but the advert had promised the bundle would last a week.",
            "There were conditions hidden in the small print that the advert never mentioned.",
            "I went back to the app and the balance showed less than what I thought I had bought.",
            "The bundle worked for two days and then the speed collapsed.",
            "I felt cheated, because the advert made it look much better than it was.",
        ])
        codes = ["CH_MISMATCH", "MI_TERMS_UNCLEAR"]
    elif p.trust_level <= 3.6:
        core = _pick(rng, [
            f"Not a serious problem, but {complaint}.",
            f"Once in a while. {_sentence(complaint)}, but nothing that made me stop buying.",
            f"Small issues, yes. {_sentence(complaint)}.",
            f"Nothing major. {_sentence(complaint)}, but I still buy.",
            f"I have had one or two issues. {_sentence(complaint)}.",
        ])
        detail = _pick(rng, [
            "The terms were clear enough, but the advert would have been better if it explained the fair usage.",
            "The offer was what they advertised; the issue was the speed, not the honesty.",
            "I would not call it a lie, more of a gap between the advert and the real experience.",
            "I did not complain formally, I just adjusted how I use the bundle.",
            "I did not take it further, but I was not happy about it.",
            "I have learned to buy smaller bundles so the loss is smaller when something goes wrong.",
        ])
        codes = ["CH_NETWORK_QUALITY"]
    else:
        core = _pick(rng, [
            "No, I have not had a serious problem. What I bought is what I got.",
            "Nothing major. The bundle delivered what the advert said.",
            "I have not been cheated. Maybe the data goes fast sometimes, but that is normal.",
            "Not really. I buy from the official app, so the risk is low.",
            "No, and I think that is because I read before I buy.",
        ])
        detail = _pick(rng, [
            "The one thing I notice is that the bundle finishes earlier when I share the hotspot, but that is my own usage.",
            "The terms have been clear in my experience, though I always read them before buying.",
            "I buy from the official app, so maybe that is why I have not had issues.",
            "The only surprise was the speed at night, which is slower than the day.",
            "I have had one small mix-up with a double charge, but it was reversed.",
        ])
        codes = ["TR_TRUST"]
    value = _pick(rng, [
        "Overall I still think bundles are worth it; it is the conditions that need to be clearer, not the products themselves.",
        "Value for money is there if you choose the right bundle, but the advertising should be more honest.",
        "So my advice to other students is to check the app balance and read the conditions before buying.",
        "For the money we pay, the value is reasonable, but the experience could be better.",
        "I would say the bundle is fine; the problem is expectation. The advert sets it too high.",
        "Students should learn to complain when something is wrong, because otherwise nothing changes.",
        "At the end of the day I still buy, so the value must be there.",
    ])
    depth = _pick(rng, [
        "So now I screenshot the advert before I buy, in case I need to complain.",
        "Customer care usually helps, but following up costs time and data, which is the irony.",
        "I think most students do not complain; they just stop buying that bundle.",
        "The bundle itself is fine. It is the way it is presented that needs work.",
        "I have made peace with it, but I am more careful now.",
        "I would rather lose a small amount than spend a day arguing with customer care.",
        "It has taught me to buy small and test before committing to a big bundle.",
        "I would tell other students to keep the advert until the bundle is finished.",
        "If customer care is slow, the class group is faster.",
        "I have stopped buying bundles from adverts I cannot verify in the app.",
    ])
    extra = _maybe(rng, p, 0.45, _pick(rng, [
        "I think the smaller the amount, the less students bother to complain.",
        "Most of us just absorb the loss and move on.",
        "If it were a big bundle, I would follow up seriously.",
        "I would rather warn my friends than argue with customer care.",
    ]))
    text = " ".join(x for x in (core, detail, value, depth, extra, rng.choice(PROBE_15)) if x)
    return text, codes


# --------------------------------------------------------------------- Q16 --
def q16(p: Respondent, rng: random.Random):
    if p.trust_level <= 2.6:
        parts = [
            _pick(rng, [
                "My biggest concern is misleading information. The advert will say 'unlimited' and then there is a fair usage limit nobody mentioned.",
                "Misleading adverts are my number one concern. They show the best case and hide the conditions.",
                "That the advert and the real bundle are not the same thing. That is what worries me.",
                "False advertising, plainly. The advert promises one thing and the bundle delivers another.",
            ]),
            _pick(rng, [
                "The conditions are never explained. You find out about the fair usage limit after you have paid.",
                "False promotions worry me, especially the bonus data that never arrives.",
                "The terms are hidden in the small print, and nobody reads the small print on a phone.",
                "The price changes between the advert and the app, and nobody explains why.",
            ]),
            _pick(rng, [
                "I also worry about the pressure to buy. The countdowns and 'last chance' messages make students spend money they do not have.",
                "And there is too much of it. The same advert follows you on every platform until you are tired.",
                "Then there is the targeting. Sometimes the advert appears after I have just searched for a bundle, which feels like being watched.",
                "I worry that students are being pushed into debt by small purchases that add up.",
            ]),
        ]
        codes = ["CH_MISLEADING", "CH_TERMS", "CH_PRESSURE"]
    elif p.trust_level <= 3.6:
        parts = [
            _pick(rng, [
                "My concern is that the adverts exaggerate. Not outright lies, but they show the best side of the bundle and leave out the speed and the fair usage.",
                "I worry that the information is not complete. The price is there, but the conditions are not.",
                "I would say the adverts are only half the story. The other half you discover after buying.",
                "The adverts are not false, but they are selective.",
            ]),
            _pick(rng, [
                "Excessive advertising is also a problem. It is too much, especially at night.",
                "And there is pressure to buy. These 'today only' offers are usually there tomorrow as well.",
                "The targeting also makes me uncomfortable, because the adverts seem to follow my searches.",
                "There are too many promotions and not enough explanation.",
            ]),
            _pick(rng, [
                "So my concern is not that they are cheating, but that they are not being fully open.",
                "I would just like the terms to be as visible as the price.",
                "Students end up spending money on bundles they did not really need because of how the offer is presented.",
                "I think the networks should be required to state the speed and the validity clearly.",
            ]),
        ]
        codes = ["CH_MISLEADING", "CH_OVERPROMOTION", "CH_PRESSURE"]
    else:
        parts = [
            _pick(rng, [
                "To be fair, I would not say the adverts are dishonest. My concern is more about the amount of advertising.",
                "I do not have a big worry about honesty. The networks are generally straight with us.",
                "My concerns are not really about misleading information; the offers I have bought were as advertised.",
                "I think the adverts are honest enough. My issue is the volume.",
            ]),
            _pick(rng, [
                "The adverts are too many and too repetitive. You see the same offer all day on different platforms.",
                "It is the pressure on students that worries me. The language makes people spend their upkeep money on data.",
                "Privacy and targeting are my concerns. The adverts seem to know what I have been searching for.",
                "The frequency is the problem. It becomes background noise, so you stop paying attention.",
            ]),
            _pick(rng, [
                "The small print could still be clearer, even if the main claims are true.",
                "I would like the validity and the speed to be stated as clearly as the price.",
                "So it is more about how they advertise than about what they promise.",
                "A bit more restraint would make the adverts more effective, not less.",
            ]),
        ]
        codes = ["CH_OVERPROMOTION"]
    parts.append(_pick(rng, [
        "I think students also need to be taught to read the conditions, not only to look at the price.",
        "The networks should remember that students talk to each other, so a bad advert travels fast.",
        "Advertising is not the enemy; advertising that hides things is.",
        "The advertising also has to respect that students are on tight budgets.",
        "I would like the university to teach us about these things, honestly.",
        "In the end, the customer has to be awake, because the advertiser will not do it for you.",
        "Students are young consumers, and we are still learning how to read these things.",
    ]))
    parts.append(rng.choice(PROBE_16))
    return " ".join(parts), codes


# --------------------------------------------------------------------- Q17 --
REC_CODE = {
    "full price": "RC_TRANSPARENCY",
    "student bundles": "RC_STUDENT_BUNDLES",
    "where students actually are": "RC_PLATFORM_PRIORITY",
    "use real students": "RC_CREATIVE",
    "stop repeating": "RC_CREATIVE",
    "Chichewa": "RC_CREATIVE",
    "honest about the speed": "RC_TRANSPARENCY",
    "message inside the app": "RC_PLATFORM_PRIORITY",
    "short video of the actual speed": "RC_CREATIVE",
    "price per gigabyte": "RC_TRANSPARENCY",
    "stop hiding the conditions": "RC_TRANSPARENCY",
    "through the university": "RC_PLATFORM_PRIORITY",
    "loyalty bonus": "RC_STUDENT_BUNDLES",
    "two steps only": "RC_CREATIVE",
    "night bundles where students": "RC_PLATFORM_PRIORITY",
}


def _rec_code(text: str) -> str:
    low = text.lower()
    for key, code in sorted(REC_CODE.items(), key=lambda kv: -len(kv[0])):
        if key in low:
            return code
    return "RC_TRANSPARENCY"


def q17(p: Respondent, rng: random.Random):
    rec = rng.choice(RECOMMENDATIONS)
    second = rng.choice([r for r in RECOMMENDATIONS
                         if r != rec and "student bundle" not in r.lower()])
    codes = list(dict.fromkeys([_rec_code(rec), _rec_code(second)]))
    parts = [f"{_sentence(rec)}.", f"{_sentence(second)}."]

    priority = (rng.choice(p.platforms) if p.platforms and rng.random() < 0.35
                else (p.platforms[0] if p.platforms else "TikTok"))
    if rng.random() < 0.68:
        if priority == "Facebook":
            platform_rec = _pick(rng, [
                "Facebook still reaches a lot of students, but WhatsApp status and TikTok are where we actually spend time, so they should not ignore those.",
                "They should keep Facebook but put more into WhatsApp status and TikTok, because that is where students scroll daily.",
                "Facebook is fine for the older market, but for us they need TikTok and WhatsApp status.",
                "The Facebook adverts are fine, but the ones that reach me are the WhatsApp status and TikTok videos.",
                "They should not abandon Facebook, but the energy should go to TikTok and WhatsApp.",
            ])
        else:
            platform_rec = _pick(rng, [
                f"They should put more effort into {priority} and WhatsApp status, because that is where students spend their time.",
                f"For platforms, {priority} and WhatsApp are the ones to prioritise; Facebook is where our parents are.",
                f"I would tell them to focus on {priority}, and to make the adverts shorter and clearer there.",
                f"{priority} is where the students are, so that is where the budget should go.",
                f"They should use {priority} for the video adverts and WhatsApp status for the reminders.",
            ])
        parts.append(platform_rec)
        codes.append("RC_PLATFORM_PRIORITY")

    if rng.random() < 0.9:
        parts.append(_pick(rng, [
            "The content should show real students, real speeds and real prices. No big productions, just honesty.",
            "They should use short videos with a student in them, and put the price, the volume and the validity on the screen for the whole video.",
            "They should show the bundle in use, like someone downloading notes or watching a match, instead of just dancing.",
            "I would like to see the actual speed test in the advert, not just a claim.",
            "The adverts should look like something a student made, not like a television commercial.",
            "Show the balance on the screen after buying. That is more convincing than any slogan.",
        ]))
        codes.append("RC_CREATIVE")

    if rng.random() < 0.6:
        if "student bundle" in rec.lower():
            parts.append(_pick(rng, [
                "They should also consider offers that combine data with calls, because we call our parents.",
                "Timing matters too: offers launched at the start of the semester would land when we actually have upkeep money.",
                "And the offers should run for longer. Buying weekly feels like a subscription you cannot escape.",
                "They could also do a package for the whole semester, paid once.",
            ]))
        else:
            parts.append(_pick(rng, [
                "And a proper student bundle, maybe during exam time, priced for people who survive on upkeep, would help a lot.",
                "They should also consider offers that combine data with calls, because we call our parents.",
                "A semester-long student offer, instead of weekly bundles, would suit the way we actually spend.",
                "A small student discount on the monthly bundle would make a real difference.",
            ]))
            codes.append("RC_STUDENT_BUNDLES")

    closing = _maybe(rng, p, 0.4, _pick(rng, [
        "If they did that, students would trust them more and probably buy more.",
        "Those are my suggestions, from a student's point of view.",
        "It would be a small change for them and a big one for us.",
        "I have said this to friends before, and they agreed.",
    ]))
    parts.append(closing)
    parts.append(rng.choice(PROBE_17))
    return " ".join(x for x in parts if x), list(dict.fromkeys(codes))


# --------------------------------------------------------------------- Q18 --
def q18(p: Respondent, rng: random.Random):
    rating = p.overall_rating.lower() or "moderate"
    closing = _pick(rng, [
        "The only thing I would add is that social media advertising works, but it works differently on different students.",
        "I think the study is important, because many students do not even realise how much these adverts influence them.",
        "What I would add is that the influence is not always direct. The advert may not make you buy today, but it stays somewhere in your mind.",
        "I would add that the networks should treat students as a serious market, not just as people to push promotions to.",
        "Something people forget is that we are not just buying data; we are buying connection to our families and our school work.",
        "I think the adverts matter more than students admit, especially when money is tight.",
        "For me the interesting part is how the same advert affects different people differently.",
    ])
    if rating in ("very high", "high") and p.purchase_status in ("NO", "UNSURE"):
        extra = _pick(rng, [
            "I would rate the influence high on my awareness, even though I have not bought because of an advert.",
            "For me it is high in the sense that my knowledge of offers comes from social media, not in the sense that it makes me buy.",
            "I would say high, because it shapes what I know, even if my actual buying is need-driven.",
        ])
    elif rating in ("very low", "low") and p.purchase_status in ("YES", "LIMITED"):
        word = "very low" if rating == "very low" else "low"
        extra = _pick(rng, [
            f"Overall I would still rate the influence {word}, because the purchases I described are exceptions; most of the time I buy out of need.",
            f"I would rate it {word}, even though there have been one or two purchases I can trace to an advert.",
            f"{word.capitalize()}, because advertising is not what usually decides for me, even if it has decided once or twice.",
            f"I would say {word} overall; the adverts are there, but they rarely change what I do.",
        ])
    elif rating in ("very high", "high"):
        extra = _pick(rng, [
            "For me the influence is high and I can see it in my own spending. Most of the bundles I buy, I first saw advertised.",
            "I would rate the influence high, especially when there is a promotion. My buying changed after I started following these pages.",
            "I would say high. The adverts shape what I consider, even if I do not buy every time.",
            "For me it is high, because I get most of my information about offers from social media.",
        ])
    elif rating == "moderate":
        extra = _pick(rng, [
            "For me the influence is moderate. The adverts make me aware, but the final decision is about need and money.",
            "I would say the influence is moderate. They do not control me, but they definitely shape what I consider.",
            "I would rate it moderate, because I buy what I need but the advert decides which one I look at first.",
            "Moderate is right for me. Sometimes they move me, sometimes I ignore them.",
        ])
    elif rating == "very low":
        extra = _pick(rng, [
            "For me the influence is very low. I buy what I need, and the adverts mostly pass me by.",
            "I would say the influence is very low in my case, though I know it is different for other students.",
            "Very low, honestly. My budget and my need decide, not the advert.",
            "I would rate it very low, because I cannot think of a purchase that was caused by an advert.",
        ])
    elif "low" in rating:
        extra = _pick(rng, [
            "For me the influence is low. I buy what I need, and the adverts mostly pass me by.",
            "I would say the influence is low in my case, though I know it is different for other students.",
            "Low, honestly. My budget and my need decide, not the advert.",
            "I would rate it low, because I cannot think of a purchase that was caused by an advert.",
        ])
    else:
        extra = _pick(rng, [
            "It depends on the month and on how much money I have. When I am broke the influence is low, when I have upkeep it is higher.",
            "I do not have a single answer; it changes with the offer and with my budget.",
        ])
    depth = _pick(rng, [
        "The networks should see students as long-term customers, because most of us will keep the same number after graduation.",
        "I also think the university could invite the networks to advertise through official channels, so students know what is genuine.",
        "Advertising is part of student life now. The question is whether it is helping us or just taking our money.",
        "If the offers were clearer, I think more students would buy, and fewer would complain.",
        "I would like students to be taught how to compare bundles properly, because many of us just guess.",
        "The networks have all the information; students have very little. That is the imbalance.",
        "At the end of the day, a bundle is a small purchase that matters a lot when you have little money.",
        "The networks should treat the study as a warning, not a public relations exercise.",
        "I hope the findings reach the people who design these adverts.",
    ])
    thanks = _pick(rng, [
        "Otherwise, that is all I can think of. Thank you for the interview.",
        "I think I have said everything. Thank you.",
        "That is my contribution. I hope it helps the study.",
        "That is all from my side. Thank you for listening.",
        "I cannot think of anything else. Thank you very much.",
        "So yes, that is my experience. Thank you.",
        "That is everything I wanted to say. Thank you.",
        "I hope this is useful. Thank you.",
    ])
    return f"{closing} {extra} {depth} {rng.choice(PROBE_18)} {thanks}", []


BUILDERS = {
    1: q1, 2: q2, 3: q3, 4: q4, 5: q5, 6: q6, 7: q7, 8: q8, 9: q9,
    10: q10, 11: q11, 12: q12, 13: q13, 14: q14, 15: q15, 16: q16,
    17: q17, 18: q18,
}
