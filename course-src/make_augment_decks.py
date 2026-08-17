#!/usr/bin/env python3
"""
Layer the discussion scaffold onto EXISTING lecture decks.

For each teaching week we take an existing lecture deck as the base (its slides,
master, theme, layouts and media stay native and untouched) and INSERT:
  * front: agenda, objectives, recap+quiz, and a "Core concepts" section divider
  * back:  a "Paper discussion" section with the auto-filled paper / questions /
           contrast, synthesis, an "Additional / backup" section, and wrap.
The inserted slides use the BASE deck's own layouts, so they match its look.
Originals in lectures/ are never modified; output goes to Fall26/.

Usage: python3 course-src/make_augment_decks.py [--force]
"""
import sys, os, re, html, tomllib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zipfile
from make_logistics_pptx import content_slide, section_slide, SLIDE_RELS

HERE = os.path.dirname(os.path.abspath(__file__))
LECT = "/Users/jxiang1/Library/CloudStorage/Dropbox-UNCCharlotte/Jian Xiang/Teaching/ITIS6200/lectures"
OUT  = "/Users/jxiang1/Library/CloudStorage/Dropbox-UNCCharlotte/Jian Xiang/Teaching/ITIS6200/Fall26"
U = html.unescape
STUB = "[ add content ]"

# week number -> (base deck filename, [extra decks to merge in PowerPoint])
MAPPING = {
    1:  ("Properties, policies, and mechanisms.pptx", ["lec02.pptx"]),
    2:  ("lec03.pptx", []),
    3:  ("lec04.pptx", []),
    4:  ("lec04.pptx", []),
    5:  ("lec05.pptx", []),
    6:  ("lec06.pptx", ["lec07.pptx"]),
    8:  ("lec08.pptx", []),
    9:  ("lec09.preliminary.pptx", ["lec09.pptx", "lec10.cookies.CSRF.pptx"]),
    10: ("lec10.cookies.CSRF.pptx", ["Slide.XSS.pptx", "Slide.SQL.injection.pptx"]),
    11: ("Slide.intro.network.pptx", ["Slide.ARP.pptx", "Slide.TCP.pptx", "TCP.UDP.pptx", "Low.level.network.pptx"]),
    12: ("Slide.DoS and Firewall.pptx", []),
    13: ("Slide.x86 Assembly and Call Stack.pptx", []),
    14: ("Slide.Memory Safety Vulnerabilities.pptx", []),
    15: ("Slide.Mitigating Memory Safety Vulnerabilities.pptx", []),
}
AGENDA = [("Quiz + recap of last week","10 min"),("Core concepts — part I","25 min"),
          ("Core concepts — part II","25 min"),("Break","10 min"),
          ("Paper discussion (student-led)","45 min"),("Synthesis — connect paper ↔ concepts","15 min"),
          ("Hands-on / worked example / activity","15 min"),("Wrap + next week's reading","5 min")]

def front_slides(w, c):
    S = []
    S.append({'title': "Today — 150 minutes",
              'bul': [(0, f"{label} — {mins}", 0) for label, mins in AGENDA]
                     + [(0, "Most of today is discussion and activity, not lecture", 0)]})
    S.append({'title': "Learning objectives",
              'bul': [(0, f"{STUB}: objective 1", 0), (0, f"{STUB}: objective 2", 0),
                      (0, "By the end you can explain the core idea and critique the paper", 0)]})
    S.append({'title': "Recap & quiz",
              'bul': [(0, "In-class quiz on last lecture (opens ~10:02, 2–3 min)", 1),
                      (0, f"{STUB}: 2–3 key points from last week", 0)]})
    S.append({'section': "Core concepts  (the lecture slides below)"})
    return S

def back_slides(w, nxt, c):
    S = []
    S.append({'section': "Paper discussion  (~45 min, student-led)"})
    reqs = [p for p in w.get('paper', []) if p['role'] == 'Required']
    if reqs:
        bul = []
        for p in reqs:
            bul += [(0, U(p['title']), 1), (1, U(p['cite']), 0),
                    (1, f"Why it matters: {U(p['blurb'])}", 0),
                    (1, f"Background you need: {U(p['background'])}", 0)]
        S.append({'title': "This week's paper" + ("s" if len(reqs) > 1 else ""), 'bul': bul})
    lead = "instructor (Week 1)" if w.get('led_in_class') else "[ sign-up group ]"
    disc = [(0, f"Leading group: {lead}", 1),
            (0, "Leaders facilitate — do not just summarize", 0),
            (0, "Rubric: understanding, clarity, critical analysis, leadership", 0),
            (0, "Discussion questions:", 1)]
    for q in w.get('q', []): disc.append((1, U(q), 0))
    S.append({'title': "Discussion — facilitate, don't summarize", 'bul': disc})
    if w.get('both_required'):
        shorts = [re.sub(r'<[^>]+>', '', U(p.get('short', p['title']))) for p in reqs]
        S.append({'title': "The contrast (present this)",
                  'bul': [(0, U(w.get('why_both', 'Present how the two papers relate.')), 0)]
                          + [(1, s, 0) for s in shorts]})
    S.append({'title': "Synthesis — connect back",
              'bul': [(0, f"{STUB}: how the paper reinforces today's concept", 0),
                      (0, f"{STUB}: one real-world consequence / lesson", 0)]})
    S.append({'section': "Additional / backup  (only if time allows)"})
    extra = [p for p in w.get('paper', []) if p['role'] in ('Recommended', 'Reference')]
    if extra:
        bul = []
        for p in extra:
            bul += [(0, f"{p['role']}: {U(p['title'])}", 1), (1, U(p['cite']), 0), (1, U(p['blurb']), 0)]
        S.append({'title': "Optional deep-dive readings", 'bul': bul})
    wrap = [(0, "Sign up for a discussion week if you haven't (Canvas)", 0)]
    if nxt and not nxt.get('no_reading'):
        nreq = [p for p in nxt.get('paper', []) if p['role'] == 'Required']
        nshort = re.sub(r'<[^>]+>', '', U(nreq[0].get('short', nreq[0]['title']))) if nreq else ''
        wrap.append((0, f"Next week (Week {nxt['n']}): {U(nxt['topic'])}", 1))
        if nshort: wrap.append((1, f"Read before class: {nshort}", 0))
    S.append({'title': "Wrap & next week", 'bul': wrap})
    return S

# ---- layout detection in a base deck ----------------------------------------
def layout_map(parts):
    body = section = titleonly = None
    for nm, b in parts.items():
        m = re.match(r'ppt/slideLayouts/slideLayout\d+\.xml$', nm)
        if not m: continue
        x = b.decode('utf-8', 'ignore')
        typ = (re.search(r'<p:sldLayout[^>]*\btype="([^"]+)"', x) or [None, ''])
        typ = typ.group(1) if hasattr(typ, 'group') else ''
        phs = re.findall(r'<p:ph type="([a-zA-Z]+)"', x)
        fn = os.path.basename(nm)
        has_body = 'body' in phs; has_title = 'title' in phs
        if has_title and has_body and body is None and typ in ('tx', 'obj', ''):
            body = fn
        if typ == 'secHead' and section is None:
            section = fn
        if has_title and not has_body and titleonly is None:
            titleonly = fn
    if body is None:                                # fallback: any layout with title+body
        for nm, b in parts.items():
            if re.match(r'ppt/slideLayouts/slideLayout\d+\.xml$', nm) and 'type="body"' in b.decode('utf-8','ignore'):
                body = os.path.basename(nm); break
    return body, (section or titleonly or body)

def render(slide, body_ly, section_ly):
    if 'section' in slide: return section_slide(slide), section_ly
    return content_slide(slide), body_ly

CORE_CAP = 20    # target lean core (~50 min at ~2.5 min/slide)
# slides whose title matches these are non-core -> Appendix (admin, drills, filler)
DROP_RE = re.compile(
    r'announc|assignment|\bdue\b|logistic|administr|syllabus|enrol|grading|'
    r"today.?s|agenda|outline|roadmap|table of contents|"
    r'\bquiz\b|poll|\bbreak\b|backup|appendix|acknowledg|thank|references?\s*$|'
    r'any questions|questions\??\s*$|feedback|survey', re.I)

def base_title(xml):
    for sp in re.findall(r'<p:sp>.*?</p:sp>', xml, re.S):
        if re.search(r'<p:ph type="(?:ctrTitle|title)"', sp):
            ts = re.findall(r'<a:t>([^<]*)</a:t>', sp)
            if ts: return " ".join(ts).strip()
    ts = re.findall(r'<a:t>([^<]*)</a:t>', xml)
    return (ts[0].strip() if ts else "")

STOP = {'the','and','for','with','your','you','how','what','are','its','via','from','that',
        'this','into','not','model','models','system','systems','using','use','intro',
        'introduction','based','ways','method','methods','without','other','obtaining','their'}
def _norm(s): return re.sub(r'[^a-z0-9]', '', s.lower())
def week_keywords(w):
    """Topic + paper titles/shorts -> relevance tokens for this week."""
    txt = [U(w['topic'])]
    for p in w.get('paper', []):
        txt.append(U(p.get('title', '')))
        txt.append(re.sub(r'<[^>]+>', '', U(p.get('short', ''))))
    toks = set()
    for s in txt:
        for tk in re.findall(r'[A-Za-z]+', s.lower()):
            if len(tk) >= 3 and tk not in STOP:
                toks.add(tk)
    return toks

def classify_base(parts, order_slidenums, w):
    """Core = concept slides most relevant to the week's topic + paper (capped);
    everything else (admin + off-topic depth) -> Appendix. Order preserved."""
    kws = week_keywords(w)
    scored = []                     # (slide_num, relevance) for non-admin slides
    for sn in order_slidenums:
        title = base_title(parts[f'ppt/slides/slide{sn}.xml'].decode('utf-8', 'ignore'))
        if (not title) or DROP_RE.search(title):
            continue                # admin/filler -> not core
        nt = _norm(title)
        scored.append((sn, sum(1 for tk in kws if tk in nt)))
    order_idx = {sn: i for i, (sn, _) in enumerate(scored)}
    rel = dict(scored)
    matched   = [sn for sn, sc in scored if sc > 0]
    unmatched = [sn for sn, sc in scored if sc == 0]
    # fill core: paper/topic-relevant first (by relevance, then order), then remaining concept slides
    core = sorted(matched, key=lambda sn: (-rel[sn], order_idx[sn]))[:CORE_CAP]
    if len(core) < CORE_CAP:
        core += unmatched[:CORE_CAP - len(core)]
    core_set = set(core)
    core_nums     = [sn for sn in order_slidenums if sn in core_set]         # original order
    appendix_nums = [sn for sn in order_slidenums if sn not in core_set]     # everything else
    return core_nums, appendix_nums

def augment(base_path, out_path, fronts, backs, w):
    z = zipfile.ZipFile(base_path)
    parts = {nm: z.read(nm) for nm in z.namelist()}
    body_ly, section_ly = layout_map(parts)
    if not body_ly:
        raise RuntimeError(f"no title+body layout found in {base_path}")

    slide_nums = [int(re.search(r'slide(\d+)\.xml', nm).group(1))
                  for nm in parts if re.match(r'ppt/slides/slide\d+\.xml$', nm)]
    next_num = max(slide_nums) + 1
    pres = parts['ppt/presentation.xml'].decode('utf-8')
    rels = parts['ppt/_rels/presentation.xml.rels'].decode('utf-8')
    ct   = parts['[Content_Types].xml'].decode('utf-8')

    # map existing sldId entries (in presentation order) -> their base slide number
    rid2slide = {m.group(1): int(m.group(2)) for m in
                 re.finditer(r'Id="(rId\d+)"[^>]*Target="slides/slide(\d+)\.xml"', rels)}
    lst_inner = re.search(r'<p:sldIdLst>(.*?)</p:sldIdLst>', pres, re.S).group(1)
    entries = []                                   # (sldId_str, slide_num) in presentation order
    for s in re.findall(r'<p:sldId [^>]*/>', lst_inner):
        rid = re.search(r'r:id="(rId\d+)"', s).group(1)
        entries.append((s, rid2slide.get(rid)))
    ordered_nums = [n for _, n in entries if n is not None]
    core_nums, appendix_nums = classify_base(parts, ordered_nums, w)
    sldid_of = {n: s for s, n in entries}

    max_sldid = max(int(re.search(r'id="(\d+)"', s).group(1)) for s, _ in entries)
    max_rid   = max(int(m) for m in re.findall(r'Id="rId(\d+)"', rels))

    def make(dicts, start_num, start_sldid, start_rid):
        np_, sldids, rl, ov = {}, [], [], []
        num, sid, rid = start_num, start_sldid, start_rid
        for s in dicts:
            xml, layout = render(s, body_ly, section_ly)
            np_[f'ppt/slides/slide{num}.xml'] = xml.encode('utf-8')
            np_[f'ppt/slides/_rels/slide{num}.xml.rels'] = SLIDE_RELS.format(layout=layout).encode('utf-8')
            sldids.append(f'<p:sldId id="{sid}" r:id="rId{rid}"/>')
            rl.append(f'<Relationship Id="rId{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{num}.xml"/>')
            ov.append(f'<Override PartName="/ppt/slides/slide{num}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')
            num += 1; sid += 1; rid += 1
        return np_, sldids, rl, ov, num, sid, rid

    fp, f_ids, f_rels, f_ov, next_num, nsid, nrid = make(fronts, next_num, max_sldid+1, max_rid+1)
    bp, b_ids, b_rels, b_ov, next_num, nsid, nrid = make(backs, next_num, nsid, nrid)
    ap, ap_ids, ap_rels, ap_ov = {}, [], [], []
    if appendix_nums:
        ap, ap_ids, ap_rels, ap_ov, next_num, nsid, nrid = make(
            [{'section': "Appendix — extra depth (cover only if time)"}], next_num, nsid, nrid)

    order = (''.join(f_ids)
             + ''.join(sldid_of[n] for n in core_nums)
             + ''.join(b_ids)
             + ''.join(ap_ids)
             + ''.join(sldid_of[n] for n in appendix_nums))
    pres = re.sub(r'<p:sldIdLst>.*?</p:sldIdLst>', f'<p:sldIdLst>{order}</p:sldIdLst>', pres, flags=re.S)
    rels = rels.replace('</Relationships>', ''.join(f_rels + b_rels + ap_rels) + '</Relationships>')
    ct   = ct.replace('</Types>', ''.join(f_ov + b_ov + ap_ov) + '</Types>')

    parts['ppt/presentation.xml'] = pres.encode('utf-8')
    parts['ppt/_rels/presentation.xml.rels'] = rels.encode('utf-8')
    parts['[Content_Types].xml'] = ct.encode('utf-8')
    parts.update(fp); parts.update(bp); parts.update(ap)

    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zo:
        zo.writestr('[Content_Types].xml', parts.pop('[Content_Types].xml'))
        for nm, b in parts.items():
            zo.writestr(nm, b)
    return len(core_nums), len(appendix_nums), len(fronts) + len(backs) + (1 if appendix_nums else 0)

def slugify(topic):
    base = re.split(r'\s*(?:&|,|\+|/| and )\s*', U(topic))[0]
    return re.sub(r'[^A-Za-z0-9]+', '', base.title())[:24]

def main():
    force = '--force' in sys.argv[1:]
    data = tomllib.load(open(os.path.join(HERE, 'courses', 'itis6200-2026fa.toml'), 'rb'))
    c = {**data.pop('course'), **data}
    weeks = {w['n']: w for w in c['week']}
    order = [w['n'] for w in c['week']]
    made = 0
    for wn, (basefn, extras) in MAPPING.items():
        w = weeks[wn]
        nxt = None
        idx = order.index(wn)
        if idx + 1 < len(order): nxt = weeks[order[idx + 1]]
        base = os.path.join(LECT, basefn)
        if not os.path.exists(base):
            print(f"  Week {wn}: BASE MISSING: {basefn}"); continue
        out = os.path.join(OUT, f"Week{wn:02d}_{slugify(w['topic'])}.pptx")
        if os.path.exists(out) and not force:
            print(f"  Week {wn}: skip (exists)"); continue
        core, appx, scaf = augment(base, out, front_slides(w, c), back_slides(w, nxt, c), w)
        note = f"  +merge: {', '.join(extras)}" if extras else ""
        print(f"  Week {wn:>2}: {os.path.basename(out):<34} core={core:>2} (~{round(core*2.5)}min) | appendix={appx:>3} | +{scaf} scaffold  [base:{basefn}]{note}")
        made += 1
    print(f"done: {made} augmented decks -> {OUT}")

if __name__ == '__main__':
    main()
