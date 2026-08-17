#!/usr/bin/env python3
"""
Generate one lecture deck per teaching week for a research course (ITIS 6200),
aligned to the schedule in the course TOML. Each deck is a talk-light,
discussion-centred SCAFFOLD for a 150-minute session:

  Title -> Agenda (timed, 150 min) -> Objectives -> Recap & Quiz
  -> [Core Concepts] concept stubs you fill in
  -> [Paper Discussion] auto-filled from the TOML reading data
  -> [Additional / Backup] optional deep-dive readings + backup stubs
  -> Wrap & next week

The paper-discussion slides are fully populated from the reading list; the
core-concept slides are titled stubs for you to author. Built on the course
template (lec01.pptx) so it matches your other decks.

  * Core slides   = the essential, in-class path (lean, to cut talking time).
  * Additional    = optional deep-dives / backup, shown only if time allows.

Usage:
    python3 course-src/make_lecture_decks.py [course] [outdir] [--force]
Defaults: course=itis6200-2026fa, outdir=<6200 Dropbox>/Fall26
By default existing decks are NOT overwritten (protects your edits); use --force.
"""
import sys, os, re, html, tomllib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_logistics_pptx import write_deck, DEFAULT_TEMPLATE

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUTDIR = "/Users/jxiang1/Library/CloudStorage/Dropbox-UNCCharlotte/Jian Xiang/Teaching/ITIS6200/Fall26"

U = html.unescape          # TOML text is HTML-authored; decode entities for pptx
STUB = "[ add content ]"

# 150-minute, talk-light agenda (instructor solo-talk ~70 min of 150)
AGENDA = [
    ("Quiz + recap of last week", "10 min"),
    ("Core concepts — part I", "25 min"),
    ("Core concepts — part II", "25 min"),
    ("Break", "10 min"),
    ("Paper discussion (student-led)", "45 min"),
    ("Synthesis — connect paper ↔ concepts", "15 min"),
    ("Hands-on / worked example / activity", "15 min"),
    ("Wrap + next week's reading", "5 min"),
]

def concepts_from_topic(topic):
    t = U(topic)
    parts = re.split(r'\s*(?:&|,|\+|/| and )\s*', t)
    parts = [p.strip() for p in parts if p.strip() and 'continue' not in p.lower()]
    return parts or [t]

def week_slug(w):
    base = concepts_from_topic(w['topic'])[0]
    return re.sub(r'[^A-Za-z0-9]+', '', base.title())[:24] or f"Week{w['n']}"

def build_week_slides(w, nxt, c):
    n = w['n']; topic = U(w['topic'])
    S = []
    # 1 title
    S.append({'title': f"Week {n} — {topic}",
              'subtitle': [w['date_long'], c['number'], c['term'],
                           "Principles of Information Security and Privacy"]})
    # 2 agenda
    S.append({'title': "Today — 150 minutes",
              'bul': [(0, f"{label}", 1) if False else (0, f"{label} — {mins}", 0) for label, mins in AGENDA]
                     + [(0, "Most of today is discussion and activity, not lecture", 0)]})
    # 3 objectives
    S.append({'title': "Learning objectives",
              'bul': [(0, f"{STUB}: objective 1", 0), (0, f"{STUB}: objective 2", 0),
                      (0, f"{STUB}: objective 3", 0),
                      (0, "By the end you can explain the week's core idea and critique the paper", 0)]})
    # 4 recap + quiz
    S.append({'title': "Recap & quiz",
              'bul': [(0, "In-class quiz on last lecture (opens ~10:02, 2–3 min)", 1),
                      (0, f"{STUB}: 2–3 key points from last week", 0),
                      (0, f"{STUB}: where today connects to them", 0)]})
    # ---- CORE ----
    S.append({'section': "Core concepts  (~50 min, keep it lean)"})
    for concept in concepts_from_topic(topic):
        S.append({'title': concept,
                  'bul': [(0, f"{STUB}: key idea / definition", 0),
                          (1, f"{STUB}: one worked example or diagram", 0),
                          (0, f"{STUB}: why it matters / common pitfall", 0),
                          (0, f"{STUB}: quick check-for-understanding question", 0)]})
    S.append({'title': "Worked example / short activity",
              'bul': [(0, f"{STUB}: one concrete example students work through", 0),
                      (0, "Prefer a 3–5 min pair activity over another explanation", 0)]})
    # ---- PAPER DISCUSSION ----
    S.append({'section': "Paper discussion  (~45 min, student-led)"})
    reqs = [p for p in w.get('paper', []) if p['role'] == 'Required']
    if reqs:
        bul = []
        for p in reqs:
            bul += [(0, U(p['title']), 1),
                    (1, U(p['cite']), 0),
                    (1, f"Why it matters: {U(p['blurb'])}", 0),
                    (1, f"Background you need: {U(p['background'])}", 0)]
        S.append({'title': "This week's paper" + ("s" if len(reqs) > 1 else ""), 'bul': bul})
    lead = "instructor (Week 1)" if w.get('led_in_class') else "[ sign-up group ]"
    disc = [(0, f"Leading group: {lead}", 1),
            (0, "Leaders facilitate the discussion — do not just summarize", 0),
            (0, "Rubric: understanding, clarity, critical analysis, leadership (Policies page)", 0),
            (0, "Discussion questions:", 1)]
    for q in w.get('q', []):
        disc.append((1, U(q), 0))
    S.append({'title': "Discussion — facilitate, don't summarize", 'bul': disc})
    if w.get('both_required'):
        shorts = [re.sub(r'<[^>]+>', '', U(p.get('short', p['title']))) for p in reqs]
        S.append({'title': "The contrast (present this)",
                  'bul': [(0, U(w.get('why_both', 'Present how the two papers relate.')), 0)]
                          + [(1, s, 0) for s in shorts]
                          + [(0, "Everyone read both this week — the comparison is the lesson", 0)]})
    # ---- SYNTHESIS ----
    S.append({'title': "Synthesis — connect back",
              'bul': [(0, f"{STUB}: how the paper reinforces today's core concept", 0),
                      (0, f"{STUB}: one real-world consequence / lesson", 0),
                      (0, f"{STUB}: what to remember for the exam / project", 0)]})
    # ---- ADDITIONAL / BACKUP ----
    S.append({'section': "Additional / backup  (only if time allows)"})
    extra = [p for p in w.get('paper', []) if p['role'] in ('Recommended', 'Reference')]
    if extra:
        bul = []
        for p in extra:
            bul += [(0, f"{p['role']}: {U(p['title'])}", 1),
                    (1, U(p['cite']), 0),
                    (1, U(p['blurb']), 0)]
        S.append({'title': "Optional deep-dive readings", 'bul': bul})
    S.append({'title': "Backup slides",
              'bul': [(0, f"{STUB}: extra examples, proofs, or diagrams", 0),
                      (0, f"{STUB}: answers to anticipated questions", 0)]})
    # ---- WRAP ----
    wrap = [(0, "Before you leave:", 1),
            (0, "Sign up for a discussion week if you haven't (Canvas, by Fri wk1)", 0)]
    if nxt and not nxt.get('no_reading'):
        nreq = [p for p in nxt.get('paper', []) if p['role'] == 'Required']
        nshort = re.sub(r'<[^>]+>', '', U(nreq[0]['short'])) if nreq and nreq[0].get('short') else (U(nreq[0]['title']) if nreq else '')
        wrap.append((0, f"Next week (Week {nxt['n']}): {U(nxt['topic'])}", 1))
        if nshort: wrap.append((1, f"Read before class: {nshort}", 0))
    elif nxt:
        wrap.append((0, f"Next week (Week {nxt['n']}): {U(nxt['topic'])}", 1))
    S.append({'title': "Wrap & next week", 'bul': wrap})
    return S

def main():
    args = [a for a in sys.argv[1:] if a != '--force']
    force = '--force' in sys.argv[1:]
    name   = args[0] if len(args) > 0 else 'itis6200-2026fa'
    outdir = args[1] if len(args) > 1 else DEFAULT_OUTDIR
    with open(os.path.join(HERE, 'courses', name + '.toml'), 'rb') as fh:
        data = tomllib.load(fh)
    c = {**data.pop('course'), **data}
    weeks = c['week']
    os.makedirs(outdir, exist_ok=True)
    made = skipped = 0
    for i, w in enumerate(weeks):
        if w.get('no_reading'):
            continue                                   # skip midterm / presentations / final
        nxt = weeks[i+1] if i+1 < len(weeks) else None
        fn = f"Week{w['n']:02d}_{week_slug(w)}.pptx"
        path = os.path.join(outdir, fn)
        if os.path.exists(path) and not force:
            print(f"  skip (exists): {fn}"); skipped += 1; continue
        slides = build_week_slides(w, nxt, c)
        nsl = write_deck(slides, path, DEFAULT_TEMPLATE, master_label=c['number'])
        print(f"  wrote {fn}  ({nsl} slides)"); made += 1
    print(f"done: {made} decks written, {skipped} skipped -> {outdir}")
    if skipped and not force:
        print("  (use --force to overwrite existing decks)")

if __name__ == '__main__':
    main()
