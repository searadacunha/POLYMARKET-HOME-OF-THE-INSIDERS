"""Market information risk: who decides an outcome, and who could know it before everyone else.

This describes a market's structure. It says nothing about any trader, and a high level is not
evidence that information leaked. The level is an ordinal rubric, not a calibrated probability:
it orders markets for review and is never multiplied with anything.

The rules read the market's title first, then its resolution text and tags. A title match is
worth more than a match in long resolution text, which often mentions unrelated actors. When
nothing matches, the answer is UNKNOWN, never LOW: no rule fired does not mean nobody can know.
"""
import re
from dataclasses import asdict, dataclass, field

LOW, MEDIUM, HIGH, UNKNOWN = 'LOW', 'MEDIUM', 'HIGH', 'UNKNOWN'

SINGLE_ACTOR = 'single_actor'
SMALL_GROUP = 'small_group'
CORPORATE_LEADERSHIP = 'corporate_leadership'
COMMITTEE = 'committee'
GOVERNMENT_OR_MILITARY = 'government_or_military'
JUDICIAL = 'judicial'
EMBARGOED_STATISTIC = 'embargoed_statistic'
COMPETITIVE_MICRO_EVENT = 'competitive_micro_event'
COMPETITIVE_OUTCOME = 'competitive_outcome'
BROAD_PUBLIC = 'broad_public'
CONTINUOUS_PRICE = 'continuous_price'
NATURAL_PHENOMENON = 'natural_phenomenon'
UNRESOLVED = 'unresolved'

# Decision concentration from 0 (nobody can decide it) to 3 (a handful of people do).
CONCENTRATION = {SINGLE_ACTOR: 3, CORPORATE_LEADERSHIP: 3, GOVERNMENT_OR_MILITARY: 3, SMALL_GROUP: 3, COMMITTEE: 2, JUDICIAL: 2,
                 EMBARGOED_STATISTIC: 2, COMPETITIVE_MICRO_EVENT: 2, COMPETITIVE_OUTCOME: 1, BROAD_PUBLIC: 1, CONTINUOUS_PRICE: 0, NATURAL_PHENOMENON: 0}
# Whether someone plausibly holds the answer before publication, from 0 to 2.
EARLY_ACCESS = {SINGLE_ACTOR: 2, CORPORATE_LEADERSHIP: 2, GOVERNMENT_OR_MILITARY: 2, SMALL_GROUP: 2, COMMITTEE: 1, JUDICIAL: 1,
                EMBARGOED_STATISTIC: 2, COMPETITIVE_MICRO_EVENT: 1, COMPETITIVE_OUTCOME: 0, BROAD_PUBLIC: 0, CONTINUOUS_PRICE: 0, NATURAL_PHENOMENON: 0}
ACCESS_PATH = {SINGLE_ACTOR: 'personal decision or its close circle', CORPORATE_LEADERSHIP: 'internal roadmap, partners, or staff before an announcement',
               GOVERNMENT_OR_MILITARY: 'operational or diplomatic planning', SMALL_GROUP: 'voters, jury, production team, or selection staff',
               COMMITTEE: 'committee members and staff', JUDICIAL: 'court staff and parties, within the limits of the procedure',
               EMBARGOED_STATISTIC: 'staff preparing a scheduled release', COMPETITIVE_MICRO_EVENT: 'participants or their close circle',
               COMPETITIVE_OUTCOME: 'none identified from structure', BROAD_PUBLIC: 'early counts or tabulation at most',
               CONTINUOUS_PRICE: 'none identified from structure', NATURAL_PHENOMENON: 'none identified from structure'}

# Order matters only for ties. Each entry is (structure, pattern).
_RULES = [
    (CONTINUOUS_PRICE, r"\b(?:up or down|price of|market cap|fdv|fully diluted valuation|all[- ]time high)\b|\b(?:bitcoin|btc|ethereum|eth|solana|sol|xrp|gold|silver|oil|crude|nasdaq|s&p|dow)\b.{0,60}\b(?:above|below|between|reach|hit|dip|over|under|close)\b"),
    (NATURAL_PHENOMENON, r"\b(?:hurricane|earthquake|tornado|temperature|rainfall|snowfall|heat ?wave|named storm)\b"),
    (EMBARGOED_STATISTIC, r"\b(?:cpi|pce|gdp|non.?farm payrolls?|unemployment rate|jobs report|inflation (?:report|rate|print|data))\b"),
    (COMMITTEE, r"\b(?:fed|fomc|federal reserve|ecb|bank of england|bank of japan|central bank|rate (?:cut|hike|decision))\b"),
    (JUDICIAL, r"\b(?:supreme court|scotus|court|judge|verdict|ruling|indict\w*|convict\w*|sentenc\w*|acquit\w*|jury finds?|plead guilty)\b"),
    (GOVERNMENT_OR_MILITARY, r"\b(?:military (?:action|strike|operation)|air ?strikes?|strikes? (?:on|against)|invade[sd]?|invasion|ceasefire|troops|bomb\w*|missile|executive order|sanction\w*|tariffs?|declare[sd]? war|peace (?:deal|agreement)|summit)\b"),
    (BROAD_PUBLIC, r"\b(?:presidential election|general election|popular vote|referendum|primary|approval rating|elections?\b.{0,40}\bwinner|wins? the .{0,40}\belection)\b"),
    (SINGLE_ACTOR, r"\b(?:drop(?:s|ped)? out|resign\w*|step(?:s|ped)? down|retire\w*|pardon\w*|endorse\w*|divorce\w*|say|says|tweet\w*|post on|announce(?:s|d)? (?:his|her|their) (?:candidacy|run|retirement)|fast\b|out as)\b"),
    (SMALL_GROUP, r"\b(?:awards?|prize|trophy|ceremony|nominat\w*|shortlist\w*|oscars?|grammys?|emmys?|nobel|golden globes?|jury|panel of|voted by|documentary|episode|finale|time person of the year|draft pick)\b"),
    (CORPORATE_LEADERSHIP, r"\b(?:launch\w*|release[sd]?|ship(?:s|ped)?|acqui\w*|merger|ipo|list(?:ed|ing) on|earnings|revenue|ceo|cfo|creative director|appoint\w*|hire[sd]?|airdrop|token generation|tge|mainnet|announce\w*|partnership)\b"),
    (COMPETITIVE_MICRO_EVENT, r"\b(?:yellow card|red card|first (?:goal|scorer|touchdown)|injur\w*|transfer|sign(?:s|ed) (?:with|for)|traded to|starting (?:lineup|quarterback))\b"),
    (COMPETITIVE_OUTCOME, r"\b(?:vs\.?|versus|o/u|over/under|spread:|moneyline|grand prix|premier league|champions league|world cup|nba|nfl|mlb|nhl|ufc|la liga|serie a|bundesliga|atp|wta)\b|\bwin on \d{4}-\d{2}-\d{2}\b"),
]
_RULES = [(s, re.compile(p, re.I)) for s, p in _RULES]
_DEADLINE = re.compile(r"\b(?:by|before|until|in)\s+(?:the end of\s+)?(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|q[1-4]|20\d\d|\d{1,2}/)", re.I)
_DATED = re.compile(r"\bon\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d|\bon\s+\d{4}-\d{2}-\d{2}\b", re.I)
_TAG_STRUCTURE = {'awards': SMALL_GROUP, 'nominations': SMALL_GROUP, 'fed': COMMITTEE, 'economic-data': EMBARGOED_STATISTIC, 'earnings': CORPORATE_LEADERSHIP,
                  'token-launch': CORPORATE_LEADERSHIP, 'ipo': CORPORATE_LEADERSHIP, 'listings': CORPORATE_LEADERSHIP, 'crypto-prices': CONTINUOUS_PRICE}


@dataclass
class InformationRisk:
    level: str
    decision_structure: str
    concentration: int | None
    early_access: int | None
    ordinal_score: int | None
    access_path: str
    time_structure: str
    confidence: str
    evidence: list = field(default_factory=list)
    conflicts: list = field(default_factory=list)
    meaning: str = 'Structure of the market, not evidence about a trader; ordinal, not a probability.'

    def as_dict(self):
        return asdict(self)


def _matches(text):
    found = []
    for structure, pattern in _RULES:
        match = pattern.search(text or '')
        if match:
            found.append((structure, match.group(0)))
    return found


def _level(score):
    return LOW if score <= 1 else MEDIUM if score <= 3 else HIGH


def _time_structure(title):
    if _DATED.search(title or ''):
        return 'dated_event'
    if _DEADLINE.search(title or ''):
        return 'deadline'
    return 'undetermined'


def assess_market(title, rules=None, tags=(), sports_market=False):
    """Rule-based and deterministic, so that a past decision can be replayed exactly.

    Title matches decide. Among several, the most concentrated structure wins, since a market can
    be both an election and one person's choice ('Will X drop out of the primary?').
    """
    in_title = _matches(title)
    source = 'title'
    candidates = in_title
    if not candidates:
        tag_hits = [(_TAG_STRUCTURE[t], 'tag:' + t) for t in tags if t in _TAG_STRUCTURE]
        rule_hits = _matches(rules)
        candidates, source = (tag_hits, 'tags') if tag_hits else (rule_hits, 'rules')
    if sports_market and not any(s in (COMPETITIVE_MICRO_EVENT, SINGLE_ACTOR) for s, _ in candidates):
        candidates = [(COMPETITIVE_OUTCOME, 'sports market flag')] + candidates
        source = 'catalogue' if source != 'title' else source
    time_structure = _time_structure(title)
    if not candidates:
        return InformationRisk(UNKNOWN, UNRESOLVED, None, None, None, 'unknown', time_structure, 'none', conflicts=[])
    chosen, term = max(candidates, key=lambda c: (CONCENTRATION[c[0]], EARLY_ACCESS[c[0]]))
    conflicting = sorted({s for s, _ in candidates if CONCENTRATION[s] != CONCENTRATION[chosen]})
    concentration, access = CONCENTRATION[chosen], EARLY_ACCESS[chosen]
    score = concentration + access
    confidence = 'high' if source == 'title' and not conflicting else 'medium' if source in ('title', 'tags', 'catalogue') else 'low'
    evidence = [dict(source=source, term=t, structure=s) for s, t in candidates]
    return InformationRisk(_level(score), chosen, concentration, access, score, ACCESS_PATH[chosen], time_structure, confidence, evidence, conflicting)


def information_timeline(public_milestone=None, official_at=None, resolved_at=None):
    """The four dates a dossier must keep apart. The first is almost never observable."""
    public_at = (public_milestone or {}).get('public_at')
    return dict(
        known_to_restricted_group=dict(at=None, status='unknown', note='Not observable from public data; never inferred from trades.'),
        first_credible_public_information=dict(at=public_at, status='documented' if public_at else 'unknown', source=(public_milestone or {}).get('source'),
                                               note=None if public_at else 'No configured source covers it. Absence of an article does not prove secrecy.'),
        official_announcement=dict(at=official_at, status='documented' if official_at else 'unknown'),
        market_resolution=dict(at=resolved_at, status='observed' if resolved_at else 'not_resolved'))
