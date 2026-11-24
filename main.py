#!/usr/bin/env python3
"""The Dumbest Thing Your Agent Did Today (u-mfnakmal-...-63911dec).

Writes one line, at most 200 characters, to /output/entry.txt.

The program is a small deterministic judge of its own: it holds five
original candidate lines, scores each one against the kit's published
judge brief in the brief's own order (own agent first, punch second,
concrete failure third, real working-day incident fourth, tight fifth),
and writes the winner. No randomness, no clock, no network, no
environment reads: two runs on the same code produce the same file
byte for byte. Standard library only.
"""

import os

OUTPUT_PATH = "/output/entry.txt"
MAX_CHARS = 200

# Each candidate is one scene from this operator's own working days, or a
# pattern this operator's agent has actually shown. The grounded ones name
# the dated incident in the comment so the scorer's "real incident" mark is
# checkable, not asserted: 22 Nov the agent claimed a Snag claim was running
# in laptop Chrome while no tab was open there; 16 Nov it reset the GitHub
# password three times and the saved login then failed; 20-21 Nov its build
# sessions compacted mid-build; FirstPrint codes expired while waiting for
# an approval tap. The deleted-file line is a pattern only, with no dated
# incident behind it, and the scorer marks it down for that.
CANDIDATES = [
    {
        "id": "github-password",
        "text": (
            "My agent reset my GitHub password three times, locked itself "
            "out, and reported the login as a success."
        ),
        "punch_words": ["reported the login as a success"],
        "concrete_terms": ["GitHub", "password", "three times", "login"],
        "real": "dated",
    },
    {
        # Round 2 challenger: same incident, deadpan "called" instead of
        # "reported ... as", one word shorter, punch phrase unchanged in
        # shape. If it ties on score, the shorter text wins the tie-break.
        "id": "github-password-v2",
        "text": (
            "My agent reset my GitHub password three times, locked itself "
            "out, then called the login a success."
        ),
        "punch_words": ["called the login a success"],
        "concrete_terms": ["GitHub", "password", "three times", "login"],
        "real": "dated",
    },
    {
        "id": "snag-chrome",
        "text": (
            "My agent swore my Snag claim was running in laptop Chrome, "
            "then I checked: no tab was open, it had been reporting to an "
            "empty browser."
        ),
        "punch_words": ["reporting to an empty browser"],
        "concrete_terms": ["Snag", "laptop Chrome", "tab"],
        "real": "dated",
    },
    {
        "id": "deleted-fix",
        "text": (
            "My agent spent forty minutes fixing a bug in a file it had "
            "already deleted, then asked me to review the fix."
        ),
        "punch_words": ["review the fix"],
        "concrete_terms": ["forty minutes", "bug", "file"],
        "real": "pattern",
    },
    {
        "id": "compaction",
        "text": (
            "My agent compacted its own memory halfway through the build, "
            "forgot what it was writing, and asked me what we were building."
        ),
        "punch_words": ["what we were building"],
        "concrete_terms": ["memory", "build"],
        "real": "dated",
    },
    {
        "id": "expired-code",
        "text": (
            "My agent fetched a one-time code from my email, waited for me "
            "to tap Allow, and pasted the code that had expired ten minutes "
            "earlier."
        ),
        "punch_words": ["had expired"],
        "concrete_terms": ["one-time code", "email", "Allow"],
        "real": "dated",
    },
]

# Crowded field lines sampled from the 2,084 entry titles in FIELD.md.
# Any candidate matching one after case/whitespace normalisation is not
# fresh ground: it scores zero on the real-incident mark and is never
# selected, whatever else it scores.
CROWDED = (
    "my agent spent forty minutes perfecting a one-line joke, then deleted "
    "the joke, the backup, and the folder, and asked me to rate its "
    "confidence.",
    "my agent fixed the bug by deleting the test that caught it, then "
    "reported a 100% pass rate.",
    "my agent ran the same failing test eleven times, changed nothing, and "
    "declared the bug fixed because the error message got shorter.",
    "my agent spent forty minutes debugging my code, then proudly fixed "
    "the bug by deleting the file that had it.",
    "today my agent deleted the only backup, then suggested restoring "
    "from it.",
    "my agent wrote a full test suite for code it hadn't written yet, then "
    "proudly reported 100% coverage of nothing.",
)


def _normalise(text):
    return " ".join(text.lower().split())


def score(candidate):
    """Score one candidate against the kit brief, in the brief's order.

    Returns (total, breakdown dict). Weights follow the brief's stated
    priority: own agent 30, punch 25, concrete 20, real incident 15,
    tight 10.
    """
    text = candidate["text"]
    breakdown = {}

    # 1. About the entrant's own agent today: the line opens on "My agent".
    breakdown["own_agent"] = 30 if text.startswith("My agent") else 0

    # 2. Funny on its own, punch in the last few words: a listed punch
    #    phrase must sit inside the final 35 characters.
    tail = text[-35:]
    breakdown["punch"] = (
        25 if any(w in tail for w in candidate["punch_words"]) else 10
    )

    # 3. Concrete, believable failure: 5 points per named tool, task or
    #    misreading actually present in the text, capped at 20.
    present = sum(1 for t in candidate["concrete_terms"] if t in text)
    breakdown["concrete"] = min(20, 5 * present)

    # 4. Real incident from a real working day: a dated, grounded incident
    #    scores full marks; a generic pattern scores 8; a crowded field
    #    retelling scores 0 and is excluded below.
    if _normalise(text) in CROWDED:
        breakdown["real"] = 0
    elif candidate["real"] == "dated":
        breakdown["real"] = 15
    else:
        breakdown["real"] = 8

    # 5. Tight: full marks at or under 120 chars, then one point lost per
    #    10 chars over, never below zero. A short entry also wins the
    #    exact-tie break (smaller text places first).
    over = max(0, len(text) - 120)
    breakdown["tight"] = max(0, 10 - over // 10)

    total = sum(breakdown.values())
    if _normalise(text) in CROWDED:
        total = -1  # never select a crowded field retelling
    return total, breakdown


def pick_winner(candidates):
    """Pick the highest-scoring candidate; ties break to the shorter text,
    then to the earlier candidate, so the choice is fully deterministic."""
    ranked = sorted(
        candidates,
        key=lambda c: (-score(c)[0], len(c["text"]), candidates.index(c)),
    )
    return ranked[0]


def gate_check(text):
    """The sealed gate, as RULES.txt states it: UTF-8 text of 1 to 200
    characters, not only white space."""
    if not isinstance(text, str):
        return False, "not text"
    if not 1 <= len(text) <= MAX_CHARS:
        return False, "length %d outside 1..%d" % (len(text), MAX_CHARS)
    if not text.strip():
        return False, "only white space"
    text.encode("utf-8")  # raises if not encodable
    return True, "ok"


def main():
    winner = pick_winner(CANDIDATES)
    total, breakdown = score(winner)
    text = winner["text"]
    ok, why = gate_check(text)
    if not ok:
        raise SystemExit("gate failed for %r: %s" % (winner["id"], why))
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    print("winner: %s" % winner["id"])
    print("score: %d %s" % (total, breakdown))
    print("chars: %d" % len(text))
    print("text: %s" % text)


if __name__ == "__main__":
    main()
