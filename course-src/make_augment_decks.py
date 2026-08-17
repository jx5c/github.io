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

def augment(base_path, out_path, fronts, backs):
    z = zipfile.ZipFile(base_path)
    parts = {nm: z.read(nm) for nm in z.namelist()}
    body_ly, section_ly = layout_map(parts)
    if not body_ly:
        raise RuntimeError(f"no title+body layout found in {base_path}")

    # existing slides + numbering
    slide_nums = sorted(int(re.search(r'slide(\d+)\.xml', nm).group(1))
                        for nm in parts if re.match(r'ppt/slides/slide\d+\.xml$', nm))
    next_num = max(slide_nums) + 1

    pres = parts['ppt/presentation.xml'].decode('utf-8')
    rels = parts['ppt/_rels/presentation.xml.rels'].decode('utf-8')
    ct   = parts['[Content_Types].xml'].decode('utf-8')

    existing_sldids = re.findall(r'<p:sldId [^>]*/>', re.search(r'<p:sldIdLst>(.*?)</p:sldIdLst>', pres, re.S).group(1))
    max_sldid = max(int(re.search(r'id="(\d+)"', s).group(1)) for s in existing_sldids)
    max_rid   = max(int(m) for m in re.findall(r'Id="rId(\d+)"', rels))

    def make(dicts, start_num, start_sldid, start_rid):
        new_parts = {}; sldids = []; rel_lines = []; overrides = []
        num, sid, rid = start_num, start_sldid, start_rid
        for s in dicts:
            xml, layout = render(s, body_ly, section_ly)
            new_parts[f'ppt/slides/slide{num}.xml'] = xml.encode('utf-8')
            new_parts[f'ppt/slides/_rels/slide{num}.xml.rels'] = SLIDE_RELS.format(layout=layout).encode('utf-8')
            sldids.append(f'<p:sldId id="{sid}" r:id="rId{rid}"/>')
            rel_lines.append(f'<Relationship Id="rId{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{num}.xml"/>')
            overrides.append(f'<Override PartName="/ppt/slides/slide{num}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')
            num += 1; sid += 1; rid += 1
        return new_parts, sldids, rel_lines, overrides, num, sid, rid

    fp, f_ids, f_rels, f_ov, next_num, nsid, nrid = make(fronts, next_num, max_sldid+1, max_rid+1)
    bp, b_ids, b_rels, b_ov, next_num, nsid, nrid = make(backs, next_num, nsid, nrid)

    new_lst = '<p:sldIdLst>' + ''.join(f_ids) + ''.join(existing_sldids) + ''.join(b_ids) + '</p:sldIdLst>'
    pres = re.sub(r'<p:sldIdLst>.*?</p:sldIdLst>', new_lst, pres, flags=re.S)
    rels = rels.replace('</Relationships>', ''.join(f_rels) + ''.join(b_rels) + '</Relationships>')
    ct   = ct.replace('</Types>', ''.join(f_ov) + ''.join(b_ov) + '</Types>')

    parts['ppt/presentation.xml'] = pres.encode('utf-8')
    parts['ppt/_rels/presentation.xml.rels'] = rels.encode('utf-8')
    parts['[Content_Types].xml'] = ct.encode('utf-8')
    parts.update(fp); parts.update(bp)

    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zo:
        zo.writestr('[Content_Types].xml', parts.pop('[Content_Types].xml'))
        for nm, b in parts.items():
            zo.writestr(nm, b)
    return len(fronts) + len(backs), len(slide_nums)

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
        ins, kept = augment(base, out, front_slides(w, c), back_slides(w, nxt, c))
        note = f"  + merge in PowerPoint: {', '.join(extras)}" if extras else ""
        print(f"  Week {wn:>2}: {os.path.basename(out)}  ({kept} lecture + {ins} scaffold = {kept+ins} slides)  [base: {basefn}]{note}")
        made += 1
    print(f"done: {made} augmented decks -> {OUT}")

if __name__ == '__main__':
    main()
