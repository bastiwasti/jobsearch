"""Global job filter rules — defines what jobs to exclude.

Applied after parsing, before storage. Edit pattern lists below
to match your job search criteria. All patterns use re.IGNORECASE.

Scraping stage: only EXCLUDE_PATTERNS are applied. All jobs that pass
are saved to the database for later analysis.

Later refinement stages can use INCLUDE_PATTERNS (domain + leadership),
REMOTE_PATTERNS, and LOCAL_PATTERNS to narrow down results.
"""

import re


# ---------------------------------------------------------------------------
# INCLUDE: job must match at least one (title + description + company)
# Bilingual: English + German keywords
# ---------------------------------------------------------------------------
INCLUDE_PATTERNS = [
    # C-level
    re.compile(r"\b(chief\s+(data|ai|analytics)\s+officer|CDO|CAIO)\b", re.IGNORECASE),
    # VP / Director
    re.compile(r"\b(vp|vice\s*president|director|direktor)\b.*\b(data|ai|analytics|ml|bi|machine\s*learning|data\s*science)\b", re.IGNORECASE),
    re.compile(r"\b(data|ai|analytics|ml|bi|machine\s*learning|data\s*science)\b.*\b(vp|vice\s*president|director|direktor)\b", re.IGNORECASE),
    # Head of
    re.compile(r"\bhead\s+of\b.*\b(data|ai|analytics|bi|machine\s*learning|data\s*science|engineering)\b", re.IGNORECASE),
    # Leiter / Bereichsleiter (German — no trailing \b on domain words for compound words like Datenmanagement)
    re.compile(r"\b(leiter|bereichsleiter|abteilungsleiter)\b.*(daten|data|analytics|bi\b|ki\b|ai\b)", re.IGNORECASE),
    re.compile(r"(daten|data|analytics|bi\b|ki\b|ai\b).*\b(leiter|bereichsleiter|abteilungsleiter)\b", re.IGNORECASE),
    # Manager
    re.compile(r"\bmanager\b.*\b(data|analytics|ai|ml|bi|data\s*science)\b", re.IGNORECASE),
    re.compile(r"\b(data|analytics|ai|ml|bi|data\s*science)\b.*\bmanager\b", re.IGNORECASE),
    # Team Lead / Tech Lead
    re.compile(r"\b(team|tech)\s*lead\b.*\b(data|ai|analytics|ml|bi)\b", re.IGNORECASE),
    re.compile(r"\bteamleiter\b.*(daten|data|analytics|bi\b|ki\b|ai\b)", re.IGNORECASE),
    # Lead + domain
    re.compile(r"\blead\b.*\b(data|ai|analytics|ml|engineer|scientist|architect)\b", re.IGNORECASE),
    # Strategy / Governance / Platform
    re.compile(r"\b(data|ai)\s+(strategy|governance|platform)\b", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# EXCLUDE: reject if any match the TITLE (not description, which often
# mentions "junior" in senior role contexts like "mentoring junior staff")
# ---------------------------------------------------------------------------
EXCLUDE_PATTERNS = [
    re.compile(r"\b(internship|praktikum|werkstudent|working\s*student|pflichtpraktikum)\b", re.IGNORECASE),
    re.compile(r"\b(junior|trainee|azubi|ausbildung)\b", re.IGNORECASE),
    re.compile(r"\b(unpaid|volunteer|ehrenamt)\b", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# REMOTE: if any match across all fields → job accepted from anywhere
# ---------------------------------------------------------------------------
REMOTE_PATTERNS = [
    re.compile(r"\b(100|80|90)%?\s*remote\b", re.IGNORECASE),
    re.compile(r"\bfully\s*remote\b", re.IGNORECASE),
    re.compile(r"\bremote\s*(first|only)\b", re.IGNORECASE),
    re.compile(r"\bvollst[äa]ndig\s*remote\b", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# LOCAL: Rheinland core ~50km from Monheim (only checked for non-remote jobs)
# ---------------------------------------------------------------------------
LOCAL_PATTERNS = [
    re.compile(r"\b(d[üu]sseldorf|k[öo]ln|cologne|bonn|leverkusen|wuppertal|solingen)\b", re.IGNORECASE),
    re.compile(r"\b(neuss|dormagen|langenfeld|monheim|hilden|ratingen|mettmann)\b", re.IGNORECASE),
    re.compile(r"\b(bergisch\s*gladbach|erkrath|haan|burscheid|leichlingen)\b", re.IGNORECASE),
    re.compile(r"\bnrw\b|nordrhein|rheinland", re.IGNORECASE),
]


def matches_filters(title: str, description: str, location: str, company: str) -> bool:
    """Return True if a job listing passes EXCLUDE filters (scraping stage).

    Only EXCLUDE_PATTERNS are applied here. All jobs that are not excluded
    are saved to the database. INCLUDE, REMOTE, and LOCAL patterns are
    available for later refinement stages.
    """
    for pattern in EXCLUDE_PATTERNS:
        if pattern.search(title):
            return False

    return True
