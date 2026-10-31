"""Build the 18 interview answers for one respondent.

Every builder receives the respondent (with their survey answers) and returns
(verbatim answer, [codes]).  The answer *flows* out of the survey record:
the branch taken for each question is driven by the respondent's own
categorical answers and Likert scores, and the concrete details (network,
platform, bundle, spend band, purchase channel, deciding factor) are taken
straight from the survey row.
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
    """Uppercase the first character only (keep Chichewa, TNM, etc.)."""
    return text[:1].upper() + text[1:] if text else text


def _lower_first(text: str) -> str:
    if not text:
        return text
    return text[0].lower() + text[1:]


def plat_text(p: Respondent) -> str:
    return _join([pl for pl in p.platforms]) if p.platforms else "WhatsApp and Facebook"


def ad_platform_text(p: Respondent) -> str:
    plats = [x for x in p.ad_platforms if x]
    if not plats:
        return p.platforms[0] if p.platforms else "Facebook"
    return _join(plats)


def ad_type_text(p: Respondent) -> str:
    types = [t.lower() for t in p.ad_types if t]
    if not types:
        return "data bundles"
    return _join(types)


def channel_text(p: Respondent) -> str:
    ch = p.channel.lower()
    net = p.primary_network
    if "app" in ch:
        return f"straight from the {net} app on my phone"
    if "mobile money" in ch:
        money = "Mpamba" if net == "TNM" else "Airtel Money"
        return f"through {money} on my phone"
    if "ussd" in ch:
        return f"using the {net} USSD menu, *111# style"
    if "agent" in ch:
        return "from an airtime agent near the hostel"
    return f"from the {net} app"


def compare_text(p: Respondent) -> str:
    c = p.comparison.lower()
    label = {"always": "Always", "often": "Often", "sometimes": "Sometimes",
             "rarely": "Rarely", "never": "Never"}.get(c, "Sometimes")
    return label


def type_category(p: Respondent) -> str:
    raw = p.ad_type_raw.lower()
    if "combo" in raw and "data" not in raw:
        return "combo"
    if "voice" in raw and "data" not in raw:
        return "voice"
    if "combo" in raw and "voice" not in raw:
        return "combo"
    return "data"


def factor_code(p: Respondent) -> str | None:
    """The Q35 deciding factor mapped to exactly one decision-criteria code."""
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


def net_reason(p: Respondent) -> str:
    bank = NETWORK_REASONS.get(p.primary_network, NETWORK_REASONS["TNM"])
    return p.rng.choice(bank)


def exposure_label(p: Respondent) -> str:
    return p.exposure or "Sometimes"


# --------------------------------------------------------------------------
# Q1  Background
# --------------------------------------------------------------------------
def q1(p: Respondent, rng: random.Random):
    prog = p.programme
    if prog:
        study = rng.choice([
            f"I am doing {prog}.",
            f"My programme is {prog}.",
            f"I am studying {prog}.",
        ])
    else:
        study = rng.choice([
            "I am doing my undergraduate studies.",
            "I am pursuing my degree.",
            "I am on the undergraduate programme.",
        ])

    openers = [
        f"I am {p.age_value} years old, a {p.gender_phrase}, and I am in {p.year_phrase} at MUBAS.",
        f"Okay, I am a {p.gender_phrase} of {p.age_value} years, currently in {p.year_phrase} here at MUBAS.",
        f"I am {p.age_value} years old and I am in {p.year_phrase} of my studies at MUBAS.",
        f"I am a {p.gender_phrase} in {p.year_phrase} at MUBAS.",
    ]
    residence = rng.choice([
        f"I stay in {rng.choice(AREAS)} and I commute to campus.",
        f"I rent a room in {rng.choice(AREAS)}, so I am a day student.",
        f"I am in a hostel around {rng.choice(AREAS)}.",
        f"I stay with my family in {rng.choice(AREAS)}.",
    ])

    net = p.primary_network
    years_on_net = rng.choice([2, 3, 3, 4, 5, 6, 7])
    if p.dual_network:
        other = "Airtel" if net == "TNM" else "TNM"
        networks = rng.choice([
            f"For my phone I use both {net} and {other}, but {net} is the one I load most.",
            f"I keep two lines, {net} and {other}. {net} is my main one.",
            f"I am on {net} mainly, though I also have {other} for the people who are on that side.",
        ])
    elif p.has_afrimax:
        networks = rng.choice([
            f"I mainly use {net}, and I also have an Afrimax line for cheap data.",
            f"My main line is {net}; Afrimax is just there for small data.",
        ])
    else:
        networks = rng.choice([
            f"For my phone I use {net} only.",
            f"I am a {net} subscriber, that is the only line I have.",
            f"I use {net} on one handset.",
        ])

    closing = rng.choice([
        "That is basically me, in short.",
        "Apart from school, I am usually online or with friends.",
        "That is a small picture of who I am.",
        "",
    ])

    duration = rng.choice([
        f"I have been on {net} for about {years_on_net} years now.",
        f"I have used {net} for roughly {years_on_net} years.",
        f"I joined {net} about {years_on_net} years ago, and I have never really moved.",
        f"It is about {years_on_net} years now on {net}.",
    ])
    reason = rng.choice([
        f"I prefer it because {net_reason(p)}.",
        f"The main reason I stay is that {net_reason(p)}.",
        f"For me it comes down to this: {net_reason(p)}.",
        f"I chose it because {net_reason(p)}.",
    ])
    text = (
        f"{rng.choice(openers)} {study} {residence} "
        f"{networks} {duration} {reason} {closing}"
    ).replace("  ", " ").strip()
    return text, []


# --------------------------------------------------------------------------
# Q2  Platforms
# --------------------------------------------------------------------------
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
    use_clauses = []
    for pl in plats[:3]:
        options = PLATFORM_USE.get(pl)
        use = rng.choice(options) if options else "general browsing"
        use_clauses.append(f"{pl} for {use}")
    usage = _join(use_clauses)

    time_map = {
        "Less than 1 hour": "less than an hour",
        "1–3 hours": "one to three hours",
        "4–6 hours": "four to six hours",
        "More than 6 hours": "more than six hours",
    }
    time_txt = time_map.get(p.time_band, "a few hours")
    time_tail = {
        "Less than 1 hour": "I try to keep it low because data is money.",
        "1–3 hours": "Most of that is in the evening after classes.",
        "4–6 hours": "It is a lot, I know, but a big part of my day is on the phone.",
        "More than 6 hours": "Honestly it is too much; sometimes I am on the phone even during a lecture.",
    }.get(p.time_band, "")

    main = plats[0]
    time_sentence = rng.choice([
        f"On a normal day I would say I spend {time_txt} on social media, maybe a bit more on weekends.",
        f"I am on social media for {time_txt} a day; weekends can push it higher.",
        f"During the week it is roughly {time_txt} a day, and a little more when I am free.",
        f"I would estimate {time_txt} daily, sometimes less when the data is finished.",
    ])
    text = (
        rng.choice([
            f"I use {plat_text(p)}.",
            f"The platforms I am on are {plat_text(p)}.",
            f"Mostly {plat_text(p)}.",
            f"I am on {plat_text(p)}, like most students.",
        ])
        + f" I use {usage}. {time_sentence} {time_tail} "
        + rng.choice([
            f"If you ask which one I open first, it is {main}.",
            f"{main} is the one I check most often.",
            f"I would say {main} takes most of my time.",
            f"But {main} is where I spend most of the time.",
        ])
    )
    codes = [PLATFORM_CODES[pl] for pl in plats if pl in PLATFORM_CODES]
    return text, codes[:4]


# --------------------------------------------------------------------------
# Q3  Exposure to adverts
# --------------------------------------------------------------------------
def q3(p: Respondent, rng: random.Random):
    exp = exposure_label(p).lower()
    rng_ = rng
    if exp == "very often":
        freq = rng_.choice([
            "Almost every time I open the app. I would say several times a day.",
            "Very often, to the point that I know some of the adverts by heart.",
            "Every day, multiple times. They follow you from Facebook to TikTok.",
        ])
        codes = ["AE_AD_FREQUENT"]
    elif exp == "often":
        freq = rng_.choice([
            "Often, maybe once or twice a day.",
            "Quite often. Most days I will see at least one.",
            "Often, especially in the evening when I am scrolling.",
        ])
        codes = ["AE_AD_FREQUENT"]
    elif exp == "sometimes":
        freq = rng_.choice([
            "Not every day. Maybe two or three times a week.",
            "Sometimes. It depends on how much I am on the phone that week.",
            "Once in a while. Some weeks I see many, other weeks none.",
        ])
        codes = []
    elif exp == "rarely":
        freq = rng_.choice([
            "Very rarely. Maybe once in two weeks.",
            "Not often at all. I can go a long time without seeing one.",
            "Rarely, and when I do it is usually by accident.",
        ])
        codes = ["AE_AD_RARE"]
    else:
        freq = rng_.choice([
            "Honestly I cannot remember the last time I saw one.",
            "Never, or almost never. I do not think the adverts are targeting me.",
            "I do not really see them. Maybe they come but I scroll past without noticing.",
        ])
        codes = ["AE_AD_RARE"]

    platform_clause = rng_.choice([
        f"When I do see them, it is mostly on {ad_platform_text(p)}.",
        f"They appear mostly on {ad_platform_text(p)} for me.",
        f"I notice them more on {ad_platform_text(p)}.",
    ])

    cat = type_category(p)
    if "data" in p.ad_type_raw.lower() and "combo" in p.ad_type_raw.lower():
        tclause = rng_.choice([
            "What I see most are data bundles, but the combo bundles also come up a lot.",
            "It is a mix: data bundles mostly, and combo bundles for calls and SMS.",
        ])
    elif cat == "combo":
        tclause = "What I notice most are the combo bundles, the ones with data, voice and SMS together."
    elif cat == "voice":
        tclause = "What I notice most are the voice and airtime bundles."
    else:
        tclause = rng_.choice([
            "What I notice most are data bundles, especially the daily and weekly ones.",
            "It is mostly data bundle adverts, the small daily ones and the weekly ones.",
            "Data bundles, almost all of them.",
        ])
        codes.append("AE_DATA_BUNDLE_DOMINANT")

    if exp == "never":
        return (f"{freq} Even when they appear, they do not stay in my mind, so I cannot describe one. "
                "It is usually data bundles, but I scroll past without noticing. "
                "Maybe they are there but I do not pay attention."), codes

    example = rng_.choice(AD_EXAMPLES[cat])
    example_clause = rng_.choice([
        f"There is one I remember well: {example}.",
        f"For example, {example}.",
        f"I can still picture it: {example}.",
    ])
    stick = rng_.choice([
        "It stayed with me because the price was written big on the screen, so I could tell immediately whether it was for me.",
        "It stayed with me because the person in it looked like an ordinary student, not a model.",
        "I remember it because the offer was running for only that weekend.",
        "It stayed with me because my friends were also talking about it.",
    ])

    text = f"{freq} {platform_clause} {tclause} {example_clause} {stick}"
    return text, codes


# --------------------------------------------------------------------------
# Q4  General views
# --------------------------------------------------------------------------
def q4(p: Respondent, rng: random.Random):
    positive = rng.choice([
        "The good thing is that they keep us informed. Before social media I would only know about a bundle when I opened the app or heard from a friend.",
        "I like that you can see the prices without going anywhere. It saves time and it makes the networks compete.",
        "On the positive side, the adverts are colourful and easy to understand, and they show offers I would never have known about.",
        "They are doing a good job of reaching students where we are, because we live on these platforms anyway.",
    ])
    trust = p.trust_level
    if trust <= 2.5:
        negative = rng.choice([
            "But the adverts are too sweet. The price on the poster and the price in the app are sometimes not the same, and the small print is not explained.",
            "My problem is that they overpromise. The bundle looks big on the advert, then you buy it and it behaves differently.",
            "What I dislike is that they show the price but not the conditions. You only discover the fair usage limit after you have paid.",
        ])
        codes = ["TR_DOUBT", "MI_TERMS_UNCLEAR"]
    elif trust <= 3.6:
        negative = rng.choice([
            "But they are repetitive, and the same advert will follow you on every platform until you are tired of it.",
            "The adverts are fine, my issue is that they do not always show the validity clearly.",
            "What I do not like is the pressure language, things like 'last chance' when the bundle will still be there tomorrow.",
            "They are a bit too many, especially at night, but I would not say they lie.",
        ])
        codes = ["CH_OVERPROMOTION"] if "repetitive" in negative or "too many" in negative else (
            ["CH_PRESSURE"] if "pressure" in negative else ["MI_TERMS_UNCLEAR"])
    else:
        negative = rng.choice([
            "There is not much to complain about, except maybe that they repeat the same advert too many times.",
            "I do not have a big problem with them. Maybe they could show the validity more clearly.",
            "If I had to complain, it is that the adverts are too many during exam time when I am trying to focus.",
            "Honestly they are fine. The only thing I would change is the amount of repetition.",
        ])
        codes = ["TR_TRUST"]
        if "repeat" in negative or "too many" in negative:
            codes.append("CH_OVERPROMOTION")

    memorable = rng.choice([
        "An advert stays in my head when it has a clear price and a face I can relate to. If it is just noise and flashing colours, I forget it immediately.",
        "What makes them memorable for me is a simple message: this much data, this much money, this many days. When they start dancing around, I switch off.",
        "Humor works on me, and so does a real student in a real lecture room. Those ones I will even forward to my friends.",
        "I remember adverts that show the actual speed or the actual bundle balance on the screen, because then it feels honest.",
    ])
    text = f"{positive} {negative} {memorable}"
    return text, codes


# --------------------------------------------------------------------------
# Q5  Attention features
# --------------------------------------------------------------------------
def q5(p: Respondent, rng: random.Random):
    factor = p.factor.lower()
    first = "the price"
    if "data" in factor or "volume" in factor:
        first = "the amount of data"
    elif "validity" in factor:
        first = "the validity period"
    elif "discount" in factor or "promotion" in factor:
        first = "the discount"

    lead = rng.choice([
        f"The first thing that catches me is {first}.",
        f"For me it starts with {first}.",
        f"I stop scrolling when I see {first}.",
    ])
    second = rng.choice([
        "After that I look at how long the bundle lasts, because a big bundle that expires in a day is useless to me.",
        "Then I check the volume and the validity together. The three things have to make sense as a package.",
        "Then I look at whether there is a promotion on top, like bonus data or double airtime.",
        "Then I look at the network quality where I stay, because a cheap bundle on a slow network is not cheap.",
    ])
    extra = []
    if p.score(18) >= 4:
        extra.append(rng.choice([
            "A short video with sound catches me more than a poster, especially if it shows someone actually using the data.",
            "Clear images and a bit of movement in the advert make a difference for me.",
        ]))
    if p.score(17) >= 4:
        extra.append(rng.choice([
            "A countdown or a 'today only' tag will make me look twice.",
            "When they put the old price and the new price side by side, that is what sells it for me.",
        ]))
    if p.score(19) >= 4:
        extra.append(rng.choice([
            "And if the person in the advert is someone I follow, I pay more attention.",
            "I also notice when a fellow student or someone popular is in the advert.",
        ]))
    if not extra:
        extra.append(rng.choice([
            "I am not moved by celebrities or big productions; just give me the numbers clearly.",
            "Honestly, fancy videos do not matter to me. Show me the price and the size and I will decide.",
        ]))
    if rng.random() < 0.62:
        humour = rng.choice([
            "Humour helps, especially in Chichewa, because it feels like they are talking to us and not reading a statement.",
            "The language matters too. When they mix English with Chichewa, it feels more natural.",
            "English is fine, but a little Chichewa gets my attention because it feels local.",
        ])
        language_code = True
    else:
        humour = rng.choice([
            "The language does not move me much; I just want the message to be clear.",
            "I do not need jokes or Chichewa, I need the price and the size.",
            "English is fine for me. The words do not change the value of the bundle.",
        ])
        language_code = False
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
    text = f"{lead} {second} {' '.join(extra)} {humour}"
    return text, codes


# --------------------------------------------------------------------------
# Q6  Trust
# --------------------------------------------------------------------------
def q6(p: Respondent, rng: random.Random):
    t = p.trust_level
    complaint = rng.choice(COMPLAINTS)
    if t >= 4:
        core = rng.choice([
            "I trust them reasonably well, maybe four out of five. When I buy what was advertised, the bundle is usually there, and the price in the app matches what the advert said.",
            "I do trust them, especially the big networks. They cannot afford to lie openly because people would post about it.",
            "On the whole I believe the adverts. I have bought several bundles from adverts and they delivered what was promised.",
        ])
        caveat = rng.choice([
            "The only thing I watch is the validity. Sometimes the advert says weekly but the data is split into night and day bundles.",
            "My only reservation is the speed after you use a certain amount, but the price and the volume are usually correct.",
            f"Once {complaint}, but I would not call it a lie, more of a technical issue.",
        ])
        codes = ["TR_TRUST"]
    elif t >= 3:
        core = rng.choice([
            "I trust them halfway. I believe the price and the volume because those are easy to check, but I do not trust the 'unlimited' language.",
            "Half and half. The bundle is real, but the experience is not always what the advert promised.",
            "I trust the numbers, not the adjectives. If it says 6GB for MK5,000, that is usually true. When it says 'fastest network', that is marketing.",
        ])
        caveat = rng.choice([
            f"I have had a case where {complaint}.",
            "Once I bought a bundle that was advertised as a week and it finished in four days, but the customer care said it depends on usage.",
            "I also read the comments before I buy, because the comments tell you what the advert will not.",
        ])
        codes = ["TR_DOUBT"]
    else:
        core = rng.choice([
            "Not much, to be honest. What is on the poster and what you get in the app are two different things.",
            "I do not trust them. These adverts are designed to make you buy, not to inform you.",
            "I have learned to be careful. I trust the app balance more than anything the advert says.",
        ])
        caveat = rng.choice([
            f"I have been disappointed before: {complaint}.",
            f"I have experienced it myself: {complaint}, and nobody explained anything.",
            "There was a promotion I bought into, and the bonus data never came.",
        ])
        codes = ["TR_DOUBT", "TR_MISMATCH_EXPERIENCE"]

    trust_build = rng.choice([
        "What makes me trust an advert is when the terms are written in full, and when people in the comments say they actually bought it.",
        "Clear terms build trust for me. If I have to zoom in to read the conditions, I already suspect something.",
        "I trust an advert when the network is known and when the same offer appears inside the official app.",
        "I trust it when a friend has used it. Word of mouth beats the advert itself.",
    ])
    depth = rng.choice([
        "The advert is written by the marketing people, but the bundle is run by the technical people, and I think the two do not always talk to each other.",
        "I have learned to check the app before I complain, because sometimes the bundle is there and I just did not see it.",
        "So my trust is not blind. I read the conditions, especially the part about the validity.",
        "What would help is if the advert carried the same information as the app, word for word.",
    ])
    text = f"{core} {caveat} {trust_build} {depth}"
    return text, codes


# --------------------------------------------------------------------------
# Q7  Images, videos, language, influencers
# --------------------------------------------------------------------------
def q7(p: Respondent, rng: random.Random):
    visuals = p.score(18)
    influencers = p.score(19)
    if visuals >= 4:
        vis = rng.choice([
            "Videos affect me a lot. If I can see the data being used, or someone downloading a past paper in seconds, it feels real.",
            "Images work on me when they are clean. A good picture with the price in the middle will stop me.",
            "A short video with a clear message is more persuasive than a long poster full of words.",
        ])
    elif visuals <= 2:
        vis = rng.choice([
            "Images and videos do not really change my mind. I look at the numbers.",
            "For me the visuals are just decoration. I want to see the price and the size of the bundle.",
            "A nice video can catch my eye, but it will not make me buy. The value has to be there.",
        ])
    else:
        vis = rng.choice([
            "The visuals help, but they are not the main thing. If the offer is good, even a plain poster will work.",
            "A good image will make me stop, but I still check the numbers before I do anything.",
        ])

    if influencers >= 4:
        inf = rng.choice([
            "Influencers do affect me, especially when it is someone from Malawi that I follow. I know they are paid, but it still makes the bundle feel familiar.",
            "When a fellow student or a popular person endorses a bundle, I take it more seriously. It is like a recommendation from a friend.",
            "I pay attention to influencers because they usually demonstrate the bundle on their phone.",
        ])
        codes = ["SI_INFLUENCER"]
    elif influencers <= 2:
        inf = rng.choice([
            "Influencers do not move me at all. They are paid to say good things, so I take it as an advert and nothing more.",
            "I actually trust influencers less. If they are being paid, they will not tell you the bundle finishes early.",
            "Celebrities do not persuade me. I would rather hear from an ordinary classmate.",
        ])
        codes = []
    else:
        inf = rng.choice([
            "Influencers are somewhere in the middle. If I already know the person, I listen; if not, I ignore.",
            "I do not follow influencers much, but when a classmate recommends something I take it seriously.",
        ])
        codes = []

    if rng.random() < 0.72:
        student = rng.choice([
            "What affects me most is student-related content. When the advert shows a lecture room, a hostel room, someone buying bundles with upkeep money, it feels like it was made for us.",
            "Student-oriented adverts carry more weight for me because they show our reality, not a businessman in an office.",
            "I like it when they mention MUBAS or use a student, because then I know they are thinking of us and not just of people with salaries.",
        ])
        codes.append("CR_STUDENT_CONTENT")
    else:
        student = rng.choice([
            "Student-related content does not change much for me. A student in the advert and a businessman in the advert are the same to me if the price is wrong.",
            "I do not care whether the person in the advert is a student; I care about the bundle.",
            "Those 'student' adverts feel like marketing talk to me. I still check the numbers myself.",
        ])

    if rng.random() < 0.68:
        lang = rng.choice([
            "The language also matters. When they mix in Chichewa or humor, the advert feels human.",
            "And the language should not be too formal. Students respond to how we actually speak.",
            "Language is part of the picture. A slogan in Chichewa sticks longer than a paragraph in English.",
        ])
        codes.append("CR_LANGUAGE_HUMOUR")
    else:
        lang = rng.choice([
            "The language does not matter much to me; English is fine as long as the message is clear.",
            "I do not need Chichewa in the advert, I just need the numbers.",
            "Humour is nice, but I do not buy because of a joke.",
        ])

    if visuals >= 4:
        codes.append("CR_VISUAL_APPEAL")
    text = f"{vis} {inf} {student} {lang}"
    return text, codes


# --------------------------------------------------------------------------
# Q8  Purchase situation
# --------------------------------------------------------------------------
def q8(p: Respondent, rng: random.Random):
    status = p.purchase_status
    month = rng.choice(MONTHS)
    trigger = rng.choice(TRIGGERS)
    bundle = p.bundle_example
    plat = ad_platform_text(p)
    channel = channel_text(p)
    factor = p.factor.lower()
    if "price" in factor or "afford" in factor:
        attract = "The price was the main thing, because it was within what I could afford that week."
    elif "data" in factor or "volume" in factor:
        attract = "What attracted me was the amount of data for that price. The value per kwacha made sense."
    elif "validity" in factor:
        attract = "What attracted me was the validity. I knew the bundle would carry me for the whole week."
    elif "discount" in factor or "promotion" in factor:
        attract = "The promotion is what got me. There was a discount and I did not want to miss it."
    elif "network" in factor:
        attract = "I trusted the network quality more than anything else."
    else:
        attract = "It was convenient. I could buy from my phone without moving."

    if status in ("YES", "LIMITED") and p.exposure in ("Rarely", "Never"):
        core = rng.choice([
            f"I do not come across them often, but there was one in {month}. {trigger[:1].upper() + trigger[1:]}, and the advert for {bundle} came up on {plat}. I bought it {channel}.",
            f"The adverts rarely reach me, but I remember one from {month}: {bundle} on {plat}. I had a need at that time, so I bought it {channel}.",
        ])
        follow = rng.choice([
            "I would say the advert played a small part; the need was already there.",
            "It is one of the few times an advert actually moved me to buy.",
            "I have not repeated it many times since, but that one worked on me.",
        ])
        return f"{core} {attract} {follow}", ["PC_PURCHASED", "IM_PLANNED"]

    if status in ("YES", "LIMITED"):
        if status == "LIMITED":
            planned = rng.choice([
                "I would not say I planned it, but I did not regret it either.",
                "I was going to buy a bundle anyway, so the advert only decided which one.",
                "It was not a big decision; I just saw it and took it.",
            ])
            core = rng.choice([
                f"There was a time in {month} when {trigger}. I saw the advert for {bundle} on {plat}, and I decided to try it.",
                f"One case I can remember was in {month}. {trigger[:1].upper() + trigger[1:]}. The advert for {bundle} kept coming up on {plat}, so I bought it.",
            ])
            codes = ["PC_PURCHASED", "IM_PLANNED"]
        else:
            if any(k in trigger for k in ("data finished", "needed data", "expire", "assignment")):
                planned = rng.choice([
                    "I was going to buy data that day anyway, but the advert decided which bundle.",
                    "I had planned to buy data, just not that particular bundle.",
                    "The need was already there; the advert only pointed me to a better option.",
                ])
            else:
                planned = rng.choice([
                    "No, I was not planning to buy at that moment. The advert is what put the idea in my head.",
                    "I had a bundle already, but it was almost finished, so the advert came at the right time.",
                    "I had planned to buy data that day, but not that particular bundle.",
                ])
            core = rng.choice([
                f"It was in {month}. {trigger[:1].upper() + trigger[1:]}. I was on {plat} and the advert for {bundle} came up, with the price written clearly. I looked at it for a while, checked the validity, and bought it {channel}.",
                f"I remember one in {month} when {trigger}. I saw {bundle} advertised on {plat}. The advert showed exactly what you get, so I did not have to think too long. I bought it {channel}.",
                f"During {month}, {trigger}, so I went to {plat} to see if there was an offer. I found the advert for {bundle}, and I bought it {channel} right there.",
            ])
            codes = ["PC_PURCHASED", "IM_IMPULSE"] if p.score(29) >= 4 else ["PC_PURCHASED", "IM_PLANNED"]
        follow = rng.choice([
            "What finally decided it was the price. I compared it in my head with what I usually buy and it was better.",
            "What decided it was the value: the bundle was bigger than what I normally get for the same money.",
            "I think it was the way the advert presented it. It made the offer look urgent and I did not want to miss it.",
            "It was a combination of the offer and the fact that I needed data at that moment.",
        ])
        if p.purchase_status == "LIMITED":
            tail = rng.choice([
                "Since then I have bought bundles from adverts maybe once or twice, not more.",
                "It happens occasionally, but I would not say it is my normal way of buying.",
            ])
        elif p.trust_level <= 2.6:
            tail = rng.choice([
                f"I used it, although {rng.choice(COMPLAINTS)}.",
                "It worked, but not exactly the way the advert made it look.",
                "After that I became more careful about what the advert promises.",
            ])
        else:
            tail = rng.choice([
                "The bundle worked as advertised, so I did not regret it.",
                f"I used it and it was fine, although {rng.choice(COMPLAINTS)}.",
                "After that I started paying attention to the adverts more.",
            ])
        text = f"{core} {attract} {planned} {follow} {tail}"
        return text, codes

    if status == "UNSURE":
        core = rng.choice([
            f"It is hard to separate. I have bought {bundle} after seeing it advertised, but I cannot say the advert is what pushed me.",
            f"Maybe in {month}, but I am not certain. I saw the advert on {plat} and later bought a bundle, but I would have bought data anyway.",
            "I am not sure how to answer that, because I buy bundles all the time. Some of them I first saw in an advert, but the decision is usually about need.",
        ])
        follow = rng.choice([
            "The advert might plant the idea, but by the time I buy, I am thinking about how much data I need and how much money I have.",
            "So I would say the advert informs me more than it decides for me.",
            "If I count it, maybe once or twice, but it was not a clear case of 'I saw it, so I bought it'.",
        ])
        return f"{core} {follow}", ["PC_NOT_PURCHASED", "IM_PLANNED"]

    # NO
    core = rng.choice([
        "I have to be honest, I have not bought a bundle because of an advert. I buy when my data finishes, usually from the app.",
        "No, not really. I see the adverts and they are interesting, but when I buy it is because I need data, not because of what I saw.",
        "I cannot point to a single time. I normally buy my bundles on a fixed day, so the adverts do not really create the purchase.",
    ])
    follow = rng.choice([
        "The adverts inform me, yes, and they might make me choose a different bundle, but they do not make me buy.",
        "So for me advertising works more on awareness than on the actual decision.",
        "I think if I had more money maybe the adverts would push me, but at the moment my budget decides.",
    ])
    extra = rng.choice([
        "Even when an offer looks good, I compare it with what I usually buy and then go back to my normal bundle.",
        "I still look at the adverts, though. They tell me when the prices change, and that is useful.",
        "My buying is tied to my data finishing, not to what is trending on the timeline.",
    ])
    return f"{core} {follow} {extra}", ["PC_NOT_PURCHASED", "IM_PLANNED"]


# --------------------------------------------------------------------------
# Q9  Comparison
# --------------------------------------------------------------------------
def q9(p: Respondent, rng: random.Random):
    label = compare_text(p)
    plat = ad_platform_text(p)
    pnet = p.primary_network
    factor = p.factor.lower()

    if label == "Always":
        core = rng.choice([
            "I always compare before I buy. I open the app, look at the price per GB, and check how long the bundle lasts.",
            "I compare every time. I will look at the bundle I saw advertised and then check what the other network is offering for the same money.",
            "Always. I do not buy the first thing I see, even if the advert is nice.",
        ])
        codes = ["CP_COMPARE_ALWAYS"]
    elif label == "Often":
        core = rng.choice([
            "I compare often, though not every single time. If the advert is for a bundle I already know, I just buy.",
            "Most of the time I compare, especially when the amount involved is more than a thousand kwacha.",
            "I usually compare. The advert starts the process, then I go and check.",
        ])
        codes = ["CP_COMPARE_SOMETIMES"]
    elif label == "Sometimes":
        core = rng.choice([
            "Sometimes I compare, sometimes I just buy. It depends on how urgent the need is.",
            "I compare when I have time. If I am in a hurry, I buy the first reasonable offer.",
            "Not always. If the advert is clear and the price is what I normally pay, I do not see the need to compare.",
        ])
        codes = ["CP_COMPARE_SOMETIMES"]
    elif label == "Rarely":
        core = rng.choice([
            "Rarely. I know what I normally buy, so I do not spend time comparing.",
            "Not really. I usually buy the same bundle every week.",
            "Very rarely. Maybe if the advert is for a bundle I have never used.",
        ])
        codes = ["CP_LITTLE_COMPARISON"]
    else:
        core = rng.choice([
            "I do not compare at all. When my data is finished I just buy what I know.",
            "Never. Comparing takes time and the difference is usually small.",
            "Honestly no. I see the advert, I buy, and I move on.",
        ])
        codes = ["CP_LITTLE_COMPARISON"]

    inside = rng.choice([
        "What I compare is price per GB, the validity, and whether the bundle works at night.",
        "I look at three things: the price, how many gigabytes, and how many days.",
        "I compare the volume and the validity. A bundle that looks cheap but lasts one day is expensive.",
        "I compare across networks, because the same money can give you very different bundles.",
    ])
    search = rng.choice([
        f"I also check the comments on the advert and ask in the class WhatsApp group before I commit.",
        f"If the advert is on {plat}, I read the comments to see whether people say it is genuine.",
        "I do not search much online; I ask a friend or check the network app.",
        "I check the network app to confirm the bundle is real before I pay.",
    ])
    fc = factor_code(p)
    if fc:
        codes.append(fc)
    closing = rng.choice([
        "The advertisement is what puts the offer in front of me, but the comparison is mine.",
        "So the advert starts the conversation, and then I do my own homework.",
        "I use the advert as a starting point, not as the answer.",
        "In short, advertising points me to offers, but comparing is how I protect my money.",
    ])
    depth = rng.choice([
        "When the need is urgent, though, comparison goes out of the window and I just buy.",
        "I also compare with what I bought last time, so I know whether the prices have moved.",
        "The problem is that the comparison takes data, which is exactly what I am trying to buy.",
        "Sometimes the difference is so small that comparing wastes time.",
    ])
    text = f"{core} {inside} {search} {closing} {depth}"
    return text, codes


# --------------------------------------------------------------------------
# Q10  Changed decision
# --------------------------------------------------------------------------
def q10(p: Respondent, rng: random.Random):
    a = p.primary_network
    b = "Airtel" if a == "TNM" else "TNM"
    if p.dual_network:
        b = "Airtel" if a == "TNM" else "TNM"
    if p.purchase_status == "NO":
        core = rng.choice([
            f"Not really. The adverts show me what {b} is offering, but I have not moved because of them.",
            f"I have not changed network or bundle because of an advert. I notice the offers, then I buy what I normally buy.",
            "I would say the adverts influence what I notice, not what I choose. My buying has stayed the same.",
        ])
        why = rng.choice([
            f"My people are on {a} and the bundles are familiar, so changing would cost me more than it saves.",
            "Changing means a new number, and that is a cost on its own.",
            "I need a strong reason to change, and an advert alone is not enough.",
        ])
        outcome = rng.choice([
            f"So I stay with {a} and buy what fits my budget.",
            "The adverts inform me, but loyalty wins.",
            "Maybe one day, but not because of an advert alone.",
        ])
        return f"{core} {why} {outcome}", ["PC_BRAND_LOYAL"]

    if p.score(22) >= 4 or p.persuasion >= 3.7:
        core = rng.choice([
            f"Yes, that has happened. I went in intending to buy my usual bundle on {a}, and then I saw an advert for a better offer on {b} and I changed.",
            f"Once. I was going to buy the {a} weekly bundle, but an advert on TikTok showed a bigger bundle for almost the same price on {b}, so I tried it.",
            f"Yes, more than once. I usually start with {a}, but if the advert shows a promotion on the other network, I move.",
        ])
        why = rng.choice([
            "What changed my mind was the price for the volume. The difference was too big to ignore.",
            "The discount is what did it. The advert showed the old price crossed out and I decided on the spot.",
            "It was the way they showed the bundle working. It convinced me that the offer was real.",
            "My friends were talking about the same offer in the class group, so I decided to try it.",
        ])
        outcome = rng.choice([
            f"In the end I bought the {b} bundle, and I have been mixing the two networks since then.",
            f"I bought the {b} one, though I did not stay with it for long.",
            f"I moved to {b} for that month, then went back to {a}.",
        ])
        codes = ["PC_CHANGED_CHOICE"]
    elif p.score(22) <= 2:
        core = rng.choice([
            f"Not really. I am loyal to {a}; it would take a very big difference to move me.",
            f"No. I see the adverts for the other network, but I do not change because my people are on {a} and the bundles are familiar.",
            f"I have not changed network because of an advert. I might change the size of the bundle, but not the network.",
        ])
        why = rng.choice([
            "Changing networks means telling everybody your new number, and that is a cost on its own.",
            "The savings would have to be serious for me to move. Right now the difference is small.",
            "I do not want the stress of a new line. I just adjust what I buy.",
        ])
        outcome = rng.choice([
            f"So I stay with {a} and buy what fits my budget.",
            "The adverts inform me, but loyalty wins.",
            "Maybe one day, but not because of an advert alone.",
        ])
        codes = ["PC_BRAND_LOYAL"]
    else:
        core = rng.choice([
            f"Not the network, no. But the bundle size, yes. I might plan to buy the small bundle and end up buying the bigger one because of an advert.",
            "I have changed the bundle I buy, but not the network. The advert makes me think bigger.",
            "Only within the same network. I will move from a daily to a weekly bundle if the advert shows a better deal.",
        ])
        why = rng.choice([
            "It is the value per kwacha that changes my mind, not the brand.",
            "The promotion made the bigger bundle look cheaper than buying small bundles daily.",
            "I changed because the advert showed a bonus that the small bundle does not have.",
        ])
        outcome = rng.choice([
            f"So I still use {a}, but the advert decides which of their bundles I take.",
            "In the end I bought the bigger bundle once, then went back to my normal one.",
            "The network stays, the bundle changes.",
        ])
        codes = ["PC_CHANGED_CHOICE"]
    depth = rng.choice([
        "I think timing matters too. When money is low I do not even open the adverts, so the influence depends on the month.",
        "For me the network decision is also emotional. If I have been with them for years, I give them a chance.",
        "But I do not switch easily, because changing means telling everybody a new number.",
        "What I have learned is that the advert is a proposal, not a command.",
    ])
    text = f"{core} {why} {outcome} {depth}"
    return text, codes


# --------------------------------------------------------------------------
# Q11  Friends, classmates, influencers
# --------------------------------------------------------------------------
def q11(p: Respondent, rng: random.Random):
    if rng.random() < 0.82:
        peer = rng.choice([
            "Friends and classmates play a big role. If two or three people in my group say a bundle is good, I will try it.",
            "My classmates influence me more than the adverts do. We forward offers in the class WhatsApp group and discuss them.",
            "Word of mouth from friends is strong. An advert I can ignore, but a friend saying 'I bought this and it is worth it' I will act on.",
            "I share adverts with my friends and they share with me. That is how most offers reach me, actually.",
        ])
        codes = ["SI_PEER"]
    else:
        peer = rng.choice([
            "Friends and classmates do not really influence what bundle I buy. We talk about offers, but each person decides alone.",
            "I would not say my friends decide for me. We discuss bundles, but my budget is my own.",
        ])
        codes = []

    if p.score(19) >= 4:
        inf = rng.choice([
            "Influencers also matter, especially the local ones who show the bundle on their phone. They make it look real.",
            "When an influencer I follow uses a bundle, I am more curious. It feels like a demonstration rather than a sales pitch.",
            "I follow a few influencers, and yes, their endorsements make me consider offers I would otherwise skip.",
        ])
        codes.append("SI_INFLUENCER")
    elif p.score(19) <= 2:
        inf = rng.choice([
            "Influencers, not so much. I know they are paid and they will say anything.",
            "I ignore celebrity endorsements. They do not use those bundles in real life.",
            "Influencers have little effect on me. A friend's opinion is worth ten influencers.",
        ])
    else:
        inf = rng.choice([
            "Influencers are neutral for me. If I know them, maybe; if not, I scroll.",
            "I listen to influencers only when they are people I already trust.",
            "I see influencers, but they do not decide anything for me.",
        ])

    if rng.random() < 0.72:
        comments = rng.choice([
            "I also read the comments. If people are complaining that they bought and got nothing, that is a red flag for me.",
            "Comments can kill an advert. One person saying 'this is a scam' and I am gone.",
            "I read comments to see the real experience. Sometimes the comments are more honest than the advert.",
            "I check what people are saying under the post before I spend anything.",
        ])
        codes.append("CH_MISLEADING")
    else:
        comments = rng.choice([
            "I do not read the comments much. I check the app and decide.",
            "I rarely look at the comments; people complain about everything anyway.",
        ])

    depth = rng.choice([
        "We forward adverts to each other almost every week, so by the time I see one I have already heard an opinion.",
        "Students trust other students more than they trust the networks, I think.",
        "But there is a limit. If a friend recommends something every day, you start to wonder whether they are being paid.",
        "The class group is where most offers reach me, honestly, more than the timeline.",
    ])
    text = f"{peer} {inf} {comments} {depth}"
    return text, codes


# --------------------------------------------------------------------------
# Q12  Unplanned purchase
# --------------------------------------------------------------------------
def q12(p: Respondent, rng: random.Random):
    impulse = p.score(29)
    discount = p.score(17)
    if impulse >= 4 and p.purchase_status == "UNSURE":
        core = rng.choice([
            "Maybe once or twice, but I cannot clearly separate it from normal buying. I buy bundles I had not planned for, and some of them I had seen advertised.",
            "It is possible, but I would not swear to it. I know I have bought data outside my plan; whether the advert caused it, I am not sure.",
        ])
        example = rng.choice([
            "There was a week I topped up twice, and one of those bundles I had seen advertised that same day.",
            "I remember buying a weekly bundle in the middle of the week, which was not my plan.",
        ])
        why = rng.choice([
            "So for me the advert and the need work together, and I cannot say which one won.",
            "I would describe it as the advert reminding me, rather than pushing me.",
        ])
        return f"{core} {example} {why}", ["IM_IMPULSE"]

    if impulse >= 4 and p.purchase_status == "NO":
        core = rng.choice([
            "I do buy bundles I had not planned for, but not because of the advert. It is usually because my data finished earlier than I expected.",
            "Yes, unplanned purchases happen to me, though I would put it down to need rather than advertising. When the data is gone, I buy.",
            "It happens, but the advert is not the reason. I buy outside my plan when I have to, for example in the middle of an assignment.",
        ])
        example = rng.choice([
            "There was a week I bought three small bundles because the first two disappeared fast.",
            "Last month I bought an extra weekly bundle in the middle of the week, which I had not planned.",
            "I remember topping up twice in one day, but that was because I was downloading notes.",
        ])
        why = rng.choice([
            "So I would say advertising makes me aware, but it does not make me buy. My usage does.",
            "The offers are attractive, but I cannot say I have bought something only because of an advert.",
            "It is need and convenience, not the beauty of the advert.",
        ])
        return f"{core} {example} {why}", ["IM_IMPULSE", "PC_NOT_PURCHASED"]

    if impulse >= 4 and p.purchase_status == "LIMITED":
        core = rng.choice([
            "It has happened, though not as often as the adverts would like. Every few months I buy a bundle that was not in my plan.",
            "Yes, occasionally. I would not call it a habit, but there are times the offer catches me at a weak moment.",
        ])
        example = rng.choice([
            "The last one was a weekend promotion with bonus data. I still had data, but I bought it anyway.",
            "There was a night bundle offer I bought while lying in bed, without checking my balance.",
        ])
        why = rng.choice([
            "It was the attractiveness of the offer, not need. That is why it does not happen every week.",
            "It was convenience and the promotion together. I could buy it in two taps, so I did.",
        ])
        return f"{core} {example} {why}", ["IM_IMPULSE"]

    if impulse >= 4:
        core = rng.choice([
            "Yes, it happens. I will see an advert and buy a bundle that was not in my plan for the week.",
            "It has happened more than once. The advert makes the offer look like it is about to disappear, so I buy.",
            "Yes. Especially when there is a promotion, I end up buying data I did not plan for.",
        ])
        example = rng.choice([
            f"The last one was {p.bundle_example}. I saw it on {ad_platform_text(p)} and bought it the same day.",
            "There was a weekend promotion with bonus data and I bought it even though I still had data.",
            "I saw a limited offer while I was in bed and bought it there and then. I did not even check my balance.",
        ])
        why = rng.choice([
            "It was the attractiveness of the offer, not need. I did not need it, but the price looked too good.",
            "It was a mix of convenience and the offer. I could buy it in two taps, so I did.",
            "What encouraged me was the urgency in the advert, the countdown and the 'today only' language.",
        ])
        codes = ["IM_IMPULSE"]
    elif impulse == 3 and p.purchase_status in ("NO", "UNSURE"):
        core = rng.choice([
            "Sometimes I am tempted, but I would not say the advert makes me buy. I usually stay within my plan.",
            "It depends. The advert can make me want the bundle, but whether I buy is another question.",
            "Once in a while I think about it, but I cannot point to a bundle I bought only because of an advert.",
        ])
        example = rng.choice([
            "There are offers I have seen and wanted, but by the time I get money the moment has passed.",
            "Maybe I have bought a bundle on the same day I saw an advert, but I was going to buy data anyway.",
            "I have looked at an offer, checked the price, and left it.",
        ])
        why = rng.choice([
            "So the temptation is real, but my budget usually wins.",
            "For me the advert raises interest; it does not close the sale.",
            "I would call it influence on what I consider, not on what I buy.",
        ])
        return f"{core} {example} {why}", ["IM_PLANNED", "BD_SPEND_CAP"]

    elif impulse == 3:
        core = rng.choice([
            "Not often. I usually stay within my plan, though a good offer can make me think twice.",
            "It depends on the month. When money is tight I just scroll; when I have a little extra I might consider it.",
            "Only once in a while, and usually I go back to my usual bundle.",
        ])
        example = rng.choice([
            f"I have looked twice at {p.bundle_example} when it was on promotion, but I did not always buy.",
            "There are offers I have wanted, but by the time I get money the moment has passed.",
            "Maybe I have bought data on the same day I saw an advert, but I was going to buy data anyway.",
        ])
        why = rng.choice([
            "So the advert raises my interest; my plan decides what I actually buy.",
            "I would call it influence on what I consider, not on what I spend.",
            "The discount catches my eye, but it does not move my budget.",
        ])
        codes = ["IM_PLANNED", "BD_SPEND_CAP"]
    else:
        core = rng.choice([
            "Not really. I plan my bundles, so I know what I am going to buy before I open social media.",
            "Rarely. I have a budget and I try to stay within it.",
            "No, I am careful. If I do not need data, an advert will not make me buy.",
        ])
        example = rng.choice([
            "If it happens, it is small, maybe an extra daily bundle when I am travelling.",
            "I cannot remember a time I bought something I did not plan for.",
            "Maybe once when there was a big promotion, but I would not count it.",
        ])
        why = rng.choice([
            "For me the need comes first. The advert can only suggest, not decide.",
            "I look at my budget first and then at the advert. Usually the budget says no.",
            "I have learned to ignore the urgency language. That 'last chance' is there every week.",
        ])
        codes = ["IM_PLANNED", "BD_SPEND_CAP"]
    depth = rng.choice([
        "At the end of the day the choice is still mine, so I do not blame the networks.",
        "My roommate is worse than me; she buys almost every promotion she sees.",
        "I think this is why students run out of upkeep money before the month ends.",
        "I have started muting some of those pages, especially when I am broke.",
    ])
    text = f"{core} {example} {why} {depth}"
    return text, codes


# --------------------------------------------------------------------------
# Q13  Budget and need
# --------------------------------------------------------------------------
def q13(p: Respondent, rng: random.Random):
    spend = p.weekly_spend
    plan = rng.choice([
        f"I spend {spend} on bundles, so I have to plan. I usually buy one main bundle at the beginning of the week and then small ones when it runs out.",
        f"My budget is {spend}. I buy the main bundle first, then I only top up if there is an emergency.",
        f"I spend {spend}, and honestly it is already a lot for a student. I plan by buying weekly instead of daily, because daily bundles are more expensive in the long run.",
    ])
    if p.score(17) >= 4:
        disc = rng.choice([
            "Discounts do encourage me to spend more. When I see a promotion I sometimes spend money I had set aside for something else.",
            "Yes, a discount can push me above my plan. That is why I try not to open the app when I am broke.",
            "Promotions are dangerous for my budget. They make me buy more data than I need.",
        ])
        codes = ["CR_PROMO_DISCOUNT"]
    else:
        disc = rng.choice([
            "Discounts do not move me much. If I did not plan for it, I skip it, even with a discount.",
            "I like discounts, but I do not let them change my budget.",
            "A promotion is nice, but my budget is fixed. I compare the discount against what I actually need.",
        ])
        codes = ["BD_SPEND_CAP"]

    volume = rng.choice([
        "The amount of data matters because I would rather buy a big bundle once than keep buying small ones. It is cheaper per GB.",
        "I look at volume against validity. A huge bundle that expires in a day is not useful to me.",
        "Data volume is what I check first, then the price. If the volume is not enough for the week, I do not buy.",
    ])
    need = rng.choice([
        "At the end of the day, need decides. If I have data, I do not buy, no matter how good the advert is.",
        "I ask myself one question: do I need this now? If the answer is no, the advert can wait.",
        "I try to separate the excitement of the advert from the actual need. It is not always easy.",
    ])
    text = f"{plan} {disc} {volume} {need}"
    return text, codes


# --------------------------------------------------------------------------
# Q14  Most important factors
# --------------------------------------------------------------------------
def q14(p: Respondent, rng: random.Random):
    factor = p.factor.lower()
    options = [
        ("price", ["Price, first and foremost. If it is not affordable, nothing else matters.",
                   "Affordability. I look at how much it costs before anything else.",
                   "The price. I am a student, so the money is the first filter."], "DF_PRICE"),
        ("data", ["The amount of data. I want value for what I pay, so the volume has to be worth it.",
                  "Data volume is the biggest factor for me. I use a lot of data for school and entertainment.",
                  "How many gigabytes I get. That is what I compare before the price."], "DF_DATA_VOLUME"),
        ("volume", ["The amount of data. I want value for what I pay, so the volume has to be worth it.",
                    "Data volume is the biggest factor for me. I use a lot of data for school and entertainment.",
                    "How many gigabytes I get. That is what I compare before the price."], "DF_DATA_VOLUME"),
        ("validity", ["The validity period. A bundle is only useful if it lasts long enough.",
                      "How long the bundle lasts. I would rather pay more for a weekly bundle than buy daily.",
                      "Validity is the deal breaker for me. Cheap and short is not cheap."], "DF_VALIDITY"),
        ("discount", ["The promotion. If there is a discount or bonus, I am interested.",
                      "A good promotion is what makes me move, even before the volume.",
                      "Discounts and bonuses, because they change the value of the bundle."], "DF_PROMOTION"),
        ("network", ["Network reliability. I would rather pay a bit more and have internet that works.",
                     "The quality of the network. A cheap bundle on a dead network is useless.",
                     "Coverage and speed. That is the first thing for me."], "DF_NETWORK_QUALITY"),
        ("recommend", ["Recommendations. If people I trust have used it, I am more willing.",
                       "What my friends and classmates say carries the most weight.",
                       "Peer recommendation. It beats any advert."], "DF_RECOMMENDATION"),
        ("convenience", ["Convenience. I want to buy quickly from my phone without looking for an agent.",
                         "Ease of buying. If it takes long to purchase, I lose interest.",
                         "The convenience of buying it right away, without looking for an agent."], "DF_CONVENIENCE"),
    ]
    lead_text, lead_code = None, None
    for key, texts, code in options:
        if key in factor:
            lead_text, lead_code = rng.choice(texts), code
            break
    if lead_text is None:
        lead_text, lead_code = rng.choice(options[-1][1]), "DF_CONVENIENCE"

    followers = [
        ("After that, validity. There is no point buying data that expires before I use it.", "DF_VALIDITY"),
        ("After that, network quality, because data that does not load is a waste.", "DF_NETWORK_QUALITY"),
        ("After that, the volume, because I need enough to carry me through the week.", "DF_DATA_VOLUME"),
        ("After that, convenience. I want to buy from the app without stress.", "DF_CONVENIENCE"),
        ("After that, the price, because a good bundle I cannot afford is still useless.", "DF_PRICE"),
    ]
    followers = [f for f in followers if f[1] != lead_code]
    second_text, second_code = rng.choice(followers)
    third_options = [
        "Recommendations matter less to me; I would rather test it myself.",
        "I do not care much about celebrity adverts; the numbers decide.",
        "The advert itself only matters if those first things are right.",
    ]
    if lead_code != "DF_PROMOTION":
        third_options.append("Promotions are a bonus, not the main reason.")
    third = rng.choice(third_options)
    closing = rng.choice([
        "That is the order in my head when I see an advert.",
        "So when I open an advert, that is what I am checking.",
        "That is how I decide, and the advert only helps if it answers those questions.",
    ])
    depth = rng.choice([
        "When I am buying for the month I think differently; I look for the biggest bundle. For daily use I just want the cheapest.",
        "And if the network is slow, I do not care how cheap it was; I feel cheated either way.",
        "Sometimes the advert only makes me aware; the actual decision is made in the app when I see my balance.",
        "I have also learned to look at the price per gigabyte rather than the headline price.",
        "The advert matters most for the first two things; after that it is just noise.",
    ])
    text = f"{lead_text} {second_text} {third} {closing} {depth}"
    fc = factor_code(p)
    return text, ([fc] if fc else [lead_code])


# --------------------------------------------------------------------------
# Q15  Problems experienced
# --------------------------------------------------------------------------
def q15(p: Respondent, rng: random.Random):
    complaint = rng.choice(COMPLAINTS)
    if p.trust_level <= 2.6 or p.score(15) <= 2:
        core = rng.choice([
            f"Yes, more than once. {complaint.capitalize()}.",
            f"I have had a problem. {complaint.capitalize()}.",
            f"Yes. {complaint.capitalize()}. Nobody warns you about that in the advert.",
        ])
        detail = rng.choice([
            "The offer was not different from what was advertised, but the experience was. The terms were not clear at all.",
            "When I complained they said it depends on usage, but the advert had promised the bundle would last a week.",
            "There were conditions hidden in the small print that the advert never mentioned.",
        ])
        codes = ["CH_MISMATCH", "MI_TERMS_UNCLEAR"]
    elif p.trust_level <= 3.6:
        core = rng.choice([
            f"Not a serious problem, but {complaint}.",
            f"Once in a while. {complaint.capitalize()}, but nothing that made me stop buying.",
            f"Small issues, yes. {complaint.capitalize()}.",
        ])
        detail = rng.choice([
            "The terms were clear enough, but the advert would have been better if it explained the fair usage.",
            "The offer was what they advertised; the issue was the speed, not the honesty.",
            "I would not call it a lie, more of a gap between the advert and the real experience.",
        ])
        codes = ["CH_NETWORK_QUALITY"]
    else:
        core = rng.choice([
            "No, I have not had a serious problem. What I bought is what I got.",
            "Nothing major. The bundle delivered what the advert said.",
            "I have not been cheated. Maybe the data goes fast sometimes, but that is normal.",
        ])
        detail = rng.choice([
            "The one thing I notice is that the bundle finishes earlier when I share the hotspot, but that is my own usage.",
            "The terms have been clear in my experience, though I always read them before buying.",
            "I buy from the official app, so maybe that is why I have not had issues.",
        ])
        codes = ["TR_TRUST"]
    value = rng.choice([
        "Overall I still think bundles are worth it; it is the conditions that need to be clearer, not the products themselves.",
        "Value for money is there if you choose the right bundle, but the advertising should be more honest.",
        "So my advice to other students is to check the app balance and read the conditions before buying.",
    ])
    depth = rng.choice([
        "So now I screenshot the advert before I buy, in case I need to complain.",
        "Customer care usually helps, but following up costs time and data, which is the irony.",
        "I think most students do not complain; they just stop buying that bundle.",
        "The bundle itself is fine. It is the way it is presented that needs work.",
    ])
    text = f"{core} {detail} {value} {depth}"
    return text, codes


# --------------------------------------------------------------------------
# Q16  Concerns
# --------------------------------------------------------------------------
def q16(p: Respondent, rng: random.Random):
    if p.trust_level <= 2.6:
        parts = [
            rng.choice([
                "My biggest concern is misleading information. The advert will say 'unlimited' and then there is a fair usage limit nobody mentioned.",
                "Misleading adverts are my number one concern. They show the best case and hide the conditions.",
                "That the advert and the real bundle are not the same thing. That is what worries me.",
            ]),
            rng.choice([
                "The conditions are never explained. You find out about the fair usage limit after you have paid.",
                "False promotions worry me, especially the bonus data that never arrives.",
                "The terms are hidden in the small print, and nobody reads the small print on a phone.",
            ]),
            rng.choice([
                "I also worry about the pressure to buy. The countdowns and 'last chance' messages make students spend money they do not have.",
                "And there is too much of it. The same advert follows you on every platform until you are tired.",
                "Then there is the targeting. Sometimes the advert appears after I have just searched for a bundle, which feels like being watched.",
            ]),
        ]
        codes = ["CH_MISLEADING", "CH_TERMS", "CH_PRESSURE"]
    elif p.trust_level <= 3.6:
        parts = [
            rng.choice([
                "My concern is that the adverts exaggerate. Not outright lies, but they show the best side of the bundle and leave out the speed and the fair usage.",
                "I worry that the information is not complete. The price is there, but the conditions are not.",
                "I would say the adverts are only half the story. The other half you discover after buying.",
            ]),
            rng.choice([
                "Excessive advertising is also a problem. It is too much, especially at night.",
                "And there is pressure to buy. These 'today only' offers are usually there tomorrow as well.",
                "The targeting also makes me uncomfortable, because the adverts seem to follow my searches.",
            ]),
            rng.choice([
                "So my concern is not that they are cheating, but that they are not being fully open.",
                "I would just like the terms to be as visible as the price.",
                "Students end up spending money on bundles they did not really need because of how the offer is presented.",
            ]),
        ]
        codes = ["CH_MISLEADING", "CH_OVERPROMOTION", "CH_PRESSURE"]
    else:
        parts = [
            rng.choice([
                "To be fair, I would not say the adverts are dishonest. My concern is more about the amount of advertising.",
                "I do not have a big worry about honesty. The networks are generally straight with us.",
                "My concerns are not really about misleading information; the offers I have bought were as advertised.",
            ]),
            rng.choice([
                "The adverts are too many and too repetitive. You see the same offer all day on different platforms.",
                "It is the pressure on students that worries me. The language makes people spend their upkeep money on data.",
                "Privacy and targeting are my concerns. The adverts seem to know what I have been searching for.",
            ]),
            rng.choice([
                "The small print could still be clearer, even if the main claims are true.",
                "I would like the validity and the speed to be stated as clearly as the price.",
                "So it is more about how they advertise than about what they promise.",
            ]),
        ]
        codes = ["CH_OVERPROMOTION"]
    parts.append(rng.choice([
        "I think students also need to be taught to read the conditions, not only to look at the price.",
        "The networks should remember that students talk to each other, so a bad advert travels fast.",
        "Advertising is not the enemy; advertising that hides things is.",
        "The advertising also has to respect that students are on tight budgets.",
    ]))
    text = " ".join(parts)
    return text, codes


# --------------------------------------------------------------------------
# Q17  Recommendations
# --------------------------------------------------------------------------
REC_CODE = {
    "full price": "RC_TRANSPARENCY",
    "student bundles": "RC_STUDENT_BUNDLES",
    "where students actually are": "RC_PLATFORM_PRIORITY",
    "use real students": "RC_CREATIVE",
    "stop repeating": "RC_CREATIVE",
    "Chichewa": "RC_CREATIVE",
    "honest about the speed": "RC_TRANSPARENCY",
    "message inside the app": "RC_PLATFORM_PRIORITY",
}


def _rec_code(text: str) -> str:
    for key, code in REC_CODE.items():
        if key.lower() in text.lower():
            return code
    return "RC_TRANSPARENCY"


def q17(p: Respondent, rng: random.Random):
    rec = rng.choice(RECOMMENDATIONS)
    second = rng.choice([r for r in RECOMMENDATIONS
                         if r != rec and "student bundle" not in r.lower()])
    codes = [_rec_code(rec), _rec_code(second)]

    priority = p.platforms[0] if p.platforms else "TikTok"
    parts = [f"{_sentence(rec)}.", f"{_sentence(second)}."]

    if rng.random() < 0.68:
        if priority == "Facebook":
            platform_rec = rng.choice([
                "Facebook still reaches a lot of students, but WhatsApp status and TikTok are where we actually spend time, so they should not ignore those.",
                "They should keep Facebook but put more into WhatsApp status and TikTok, because that is where students scroll daily.",
            ])
        else:
            platform_rec = rng.choice([
                f"They should put more effort into {priority} and WhatsApp status, because that is where students spend their time.",
                f"For platforms, {priority} and WhatsApp are the ones to prioritise; Facebook is where our parents are.",
                f"I would tell them to focus on {priority}, and to make the adverts shorter and clearer there.",
            ])
        parts.append(platform_rec)
        codes.append("RC_PLATFORM_PRIORITY")

    if rng.random() < 0.68:
        parts.append(rng.choice([
            "The content should show real students, real speeds and real prices. No big productions, just honesty.",
            "They should use short videos with a student in them, and put the price, the volume and the validity on the screen for the whole video.",
            "They should show the bundle in use, like someone downloading notes or watching a match, instead of just dancing.",
        ]))
        codes.append("RC_CREATIVE")

    if rng.random() < 0.6:
        if "student bundle" in rec.lower():
            parts.append(rng.choice([
                "They should also consider offers that combine data with calls, because we call our parents.",
                "Timing matters too: offers launched at the start of the semester would land when we actually have upkeep money.",
                "And the offers should run for longer. Buying weekly feels like a subscription you cannot escape.",
            ]))
        else:
            parts.append(rng.choice([
                "And a proper student bundle, maybe during exam time, priced for people who survive on upkeep, would help a lot.",
                "They should also consider offers that combine data with calls, because we call our parents.",
                "A semester-long student offer, instead of weekly bundles, would suit the way we actually spend.",
            ]))
            codes.append("RC_STUDENT_BUNDLES")

    return " ".join(parts), codes


# --------------------------------------------------------------------------
# Q18  Anything else
# --------------------------------------------------------------------------
def q18(p: Respondent, rng: random.Random):
    rating = p.overall_rating.lower()
    closing = rng.choice([
        "The only thing I would add is that social media advertising works, but it works differently on different students.",
        "I think the study is important, because many students do not even realise how much these adverts influence them.",
        "What I would add is that the influence is not always direct. The advert may not make you buy today, but it stays somewhere in your mind.",
        "I would add that the networks should treat students as a serious market, not just as people to push promotions to.",
    ])
    if "very high" in rating or rating == "high":
        extra = rng.choice([
            "For me the influence is real and I can see it in my own spending. Most of the bundles I buy, I first saw advertised.",
            "I would say the influence is high, especially when there is a promotion. My buying changed after I started following these pages.",
        ])
    elif rating == "moderate":
        extra = rng.choice([
            "For me the influence is moderate. The adverts make me aware, but the final decision is about need and money.",
            "I would say it is in the middle. They do not control me, but they definitely shape what I consider.",
        ])
    elif "low" in rating:
        extra = rng.choice([
            "For me the influence is low. I buy what I need, and the adverts mostly pass me by.",
            "I would say the influence is low in my case, though I know it is different for other students.",
        ])
    else:
        extra = rng.choice([
            "It depends on the month and on how much money I have. When I am broke the influence is low, when I have upkeep it is higher.",
            "I do not have a single answer; it changes with the offer and with my budget.",
        ])
    thanks = rng.choice([
        "Otherwise, that is all I can think of. Thank you for the interview.",
        "I think I have said everything. Thank you.",
        "That is my contribution. I hope it helps the study.",
        "That is all from my side. Thank you for listening.",
        "I cannot think of anything else. Thank you very much.",
        "So yes, that is my experience. Thank you.",
    ])
    depth = rng.choice([
        "The networks should see students as long-term customers, because most of us will keep the same number after graduation.",
        "I also think the university could invite the networks to advertise through official channels, so students know what is genuine.",
        "Advertising is part of student life now. The question is whether it is helping us or just taking our money.",
        "If the offers were clearer, I think more students would buy, and fewer would complain.",
    ])
    text = f"{closing} {extra} {depth} {thanks}"
    return text, []


BUILDERS = {
    1: q1, 2: q2, 3: q3, 4: q4, 5: q5, 6: q6, 7: q7, 8: q8, 9: q9,
    10: q10, 11: q11, 12: q12, 13: q13, 14: q14, 15: q15, 16: q16,
    17: q17, 18: q18,
}
