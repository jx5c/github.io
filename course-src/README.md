# Course site — single source of truth

Course logistics (term, meeting time, room, staff, office hours, exam dates,
grading weights, and the ITIS 3200 schedule) live in **one file per offering**
under `courses/`. Edit that file, run the build, commit. One change propagates
to every page — no more hunting through many HTML files.

## Edit → build → commit

```bash
# 1. edit the data
$EDITOR course-src/courses/itis3200-2026fa.toml

# 2. regenerate (all courses, or name one)
python3 course-src/build.py
python3 course-src/build.py itis3200-2026fa

# 3. review + commit
git diff teaching/ course-src/
git add -A && git commit -m "…" && git push
```

`build.py` needs only Python 3.11+ (uses the stdlib `tomllib`). No pip installs.

## What is generated vs hand-maintained

For each course the build **overwrites**:

| Output | Path |
|---|---|
| Public site pages | `teaching/<DIR>/<term>/{index, schedule, officehours, resources, nav}.html` |
| Public paper-reading page (6200) | `teaching/<DIR>/<term>/papers.html` |
| Canvas paste HTML | `course-src/canvas-out/<course>/{syllabus, schedule or paper_reading_schedule}.html` |

**Never edit those by hand** — your edits are lost on the next build. Edit the
`.toml` instead. The ITIS 6200 schedule + reading list come from the `[[week]]`
blocks in its `.toml`.

**Hand-maintained** (the build leaves them alone — rich, low-churn content):

- `policies.html` — course policies (both courses)
- `course.css`, `jquery-*.js`
- The ITIS 6200 Canvas **paper-discussion policy** page (stable prose) in
  `Teaching/ITIS6200/Canvas_pages/`

## Common edits

| Change | Where in the `.toml` |
|---|---|
| Office-hour room / hours | `[[ta]].office_hours`, `[instructor].office_hours` |
| Meeting time / room | `meeting`, `meeting_long`, `location` |
| Exam dates | `[exams]` **and** the matching `[[weight]]` lines |
| Grading weights | `[[weight]]` blocks |
| Add/drop a TA | add/remove a `[[ta]]` block |
| Schedule (3200) | `[[row]]` blocks — `section` = grey topic band, `holiday = true` = grey row |

## New semester

1. Copy `courses/itis3200-2026fa.toml` → `courses/itis3200-2027sp.toml`.
2. Update `term`, `term_slug`, dates, staff, rooms, schedule.
3. `python3 course-src/build.py itis3200-2027sp` → creates `teaching/ITIS3200/2027sp/`.
4. Copy `policies.html` (and for 6200 `papers.html`, `schedule.html`) from the
   previous term's folder and update.
5. Add the offering to `../teaching.html`.

## Paste to Canvas

Open `course-src/canvas-out/<course>/syllabus.html` (or `schedule.html`), copy
all, and in Canvas: **Edit page → HTML editor (`</>`) → paste**.

## Weekly lecture decks (ITIS 6200)

`make_lecture_decks.py` builds one **discussion-centred scaffold deck per
teaching week** from the `[[week]]` data, aligned to the schedule, on the
lec01 template:

```bash
python3 course-src/make_lecture_decks.py            # itis6200-2026fa -> <6200>/Fall26/
python3 course-src/make_lecture_decks.py itis6200-2026fa "<outdir>" --force
```

Each deck (150-min, talk-light) has: title, timed agenda, objectives,
recap+quiz, **[Core concepts]** stubs *you fill in*, **[Paper discussion]**
slides *auto-filled from the TOML* (paper, why-it-matters, background, the 3
discussion questions, and the both-required contrast), **[Additional / backup]**
optional deep-dive readings, and a wrap/next-week slide.

**These are one-time scaffolds — existing decks are NOT overwritten** (so your
authored content is safe). Re-run with `--force` only to regenerate from
scratch. The decks live in the course Dropbox `Fall26/` folder, not in git.

## Logistics decks

`make_logistics_pptx.py <course> <out.pptx> [template.pptx]` builds a
first-class logistics deck from the same TOML, on the course template.
