#!/usr/bin/env python3
"""
Generate a first-class "logistics" slide deck from a course TOML, reusing an
existing deck's master / layouts / theme so it matches the course template.

Usage:
    python3 course-src/make_logistics_pptx.py <course> <out.pptx> [template.pptx]

If no template is given, uses the ITIS 3200 lec01.pptx template. The template's
slides are dropped; its slideMaster, slideLayouts and theme are kept, and the
logistics slides are built with title/body placeholders so they inherit the
template's fonts, colours, bullets and slide size.
Stdlib only (zipfile + tomllib).
"""
import sys, os, re, tomllib, zipfile
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TEMPLATE = "/Users/jxiang1/Library/CloudStorage/Dropbox-UNCCharlotte/Jian Xiang/Teaching/ITIS3200/lectures/lec01.pptx"
TITLE_LAYOUT   = "slideLayout1.xml"   # type=title  (ctrTitle + subTitle)
CONTENT_LAYOUT = "slideLayout3.xml"   # type=tx     (title + body idx1)

# ---- slide content (from TOML) ---------------------------------------------
def build_slides(c):
    ins = c['instructor']; site = f"https://jianxiang.info/teaching/{c['dir_slug']}/{c['term_slug']}/index.html"
    S = []
    S.append({'title': f"{c['number']}", 'subtitle': [
        c['title'], c['term'], f"Prof. {ins['name']}", "First class — Logistics"]})
    S.append({'title': "When & Where", 'bul': [
        (0, f"Lectures: {c['meeting']}", 1),
        (0, f"Location: {c['location']}", 0),
        (0, f"Credit hours: {c['credit']}", 0),
        (0, "In-person class — you are expected to be here", 0),
        (0, f"Course website: {site}", 0),
        (1, "Syllabus, schedule, policies, office-hours calendar", 0),
        (0, "Canvas: assignments, quizzes, grades", 0)]})
    staff = [(0, f"Instructor: {ins['name']}", 1),
             (1, f"Office hours: {ins['office_hours']}", 0),
             (0, "Teaching Assistants:", 1)]
    for t in c.get('ta', []):
        staff.append((1, f"{t['name']} — {t['email']}", 0))
        staff.append((2, f"Office hours: {t['office_hours']}", 0))
    staff.append((0, "Office hours start in week 2; check the Google calendar (Canvas)", 0))
    S.append({'title': "Course Staff & Office Hours", 'bul': staff})
    g = [(0, w['label'], 1) for w in c['weight']]
    g.append((0, "Grading scale: A 90+, B 80s, C 70s, D 60s, F <60", 0))
    S.append({'title': "Grading", 'bul': g})
    S.append({'title': "Exams", 'bul': [
        (0, f"Midterm: {c['exams']['midterm']}", 1),
        (0, f"Final: {c['exams']['final']}", 1),
        (0, f"Format: {c['exams']['rules']}", 0),
        (0, "Make-up exams are not guaranteed; follow university policy", 0)]})
    if c.get('has_papers'):
        purl = f"https://jianxiang.info/teaching/{c['dir_slug']}/{c['term_slug']}/papers.html"
        S.append({'title': "Weekly Paper Discussions", 'bul': [
            (0, "Everyone reads one required paper each week (~17 pp)", 1),
            (0, "Each group leads one discussion (25–30 min); some weeks two groups", 0),
            (1, "Facilitate discussion — don't just summarize", 0),
            (1, "Leading group reads both papers; present the contrast", 0),
            (0, "Sign up for a week via Canvas by 11:59pm Friday of week 1", 0),
            (0, "Graded: understanding, clarity, critical analysis, leadership (10%)", 0),
            (0, f"Full reading list & background: {purl}", 0)]})
    S.append({'title': "Key Policies", 'bul': [
        (0, "AI use", 1),
        (1, "You MUST disclose how you used AI in each submission", 0),
        (1, "Do not copy/paste AI output as your answer", 0),
        (0, "In-class quizzes", 1),
        (1, "Start of most lectures; cover the previous lecture", 0),
        (1, "No late submissions; lowest two scores dropped", 0),
        (0, "Homework", 1),
        (1, "Late accepted up to 48 hours, 10% per-day penalty", 0),
        (0, "Read the full syllabus & policies on the course website", 0)]})
    wtf = [(0, "Course website (public)", 1), (1, site, 0),
           (1, "Syllabus, lecture schedule, policies, resources", 0)]
    if c.get('has_papers'): wtf.append((1, "Paper Reading Schedule (weekly readings)", 0))
    wtf += [(0, "Canvas (login required)", 1),
            (1, "Assignments, quizzes, grades, announcements", 0),
            (0, "Office-hours Google calendar (linked on both)", 1),
            (0, "Questions → course staff (allow up to 48 hours)", 0)]
    S.append({'title': "Where to Find Everything", 'bul': wtf})
    return S

# ---- slide XML (placeholder-based, inherits template styling) ---------------
def _p(text, bold=False, lvl=None):
    ppr = f'<a:pPr lvl="{lvl}"/>' if lvl else ''
    rpr = f'<a:rPr lang="en-US"{" b=\"1\"" if bold else ""} dirty="0"/>'
    return f'<a:p>{ppr}<a:r>{rpr}<a:t>{escape(text)}</a:t></a:r></a:p>'

def _ph_sp(cid, name, ph_attr, paras):
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{cid}" name="{name}"/>'
            f'<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            f'<p:nvPr>{ph_attr}</p:nvPr></p:nvSpPr>'
            f'<p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/>{paras}</p:txBody></p:sp>')

def _wrap(shapes):
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
            'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree>'
            '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/>'
            + shapes + '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')

def title_slide(s):
    title = _ph_sp(2, "Title", '<p:ph type="ctrTitle"/>', _p(s['title']))
    subs = ''.join(_p(t) for t in s['subtitle'])
    sub = _ph_sp(3, "Subtitle", '<p:ph type="subTitle" idx="1"/>', subs)
    return _wrap(title + sub)

def content_slide(s):
    title = _ph_sp(2, "Title", '<p:ph type="title"/>', _p(s['title']))
    body_paras = ''.join(_p(text, bold, lvl if lvl else None) for lvl, text, bold in s.get('bul', []))
    body = _ph_sp(3, "Body", '<p:ph type="body" idx="1"/>', body_paras)
    return _wrap(title + body)

def section_slide(s):
    """Title-only divider slide (uses the section-header layout)."""
    title = _ph_sp(2, "Title", '<p:ph type="title"/>', _p(s['section']))
    return _wrap(title)

def slide_to_xml(s):
    if 'subtitle' in s: return title_slide(s), TITLE_LAYOUT
    if 'section'  in s: return section_slide(s), "slideLayout2.xml"   # SECTION_HEADER
    return content_slide(s), CONTENT_LAYOUT

def write_deck(slide_dicts, outpath, template, master_label=None):
    """Package a list of slide dicts onto a template deck (keeps master/layouts/theme).
    master_label: if set, replace the template's baked-in course banner text
    ("ITIS 3200") in the slide master, so decks for another course brand correctly."""
    n = len(slide_dicts)
    rendered = [slide_to_xml(s) for s in slide_dicts]
    slide_xmls = [x for x, _ in rendered]
    layouts    = [ly for _, ly in rendered]

    tz = zipfile.ZipFile(template)
    keep = {}
    for nm in tz.namelist():
        if nm.startswith('ppt/slides/') or nm.startswith('ppt/notesSlides/'): continue
        if nm in ('[Content_Types].xml', 'ppt/presentation.xml', 'ppt/_rels/presentation.xml.rels'): continue
        keep[nm] = tz.read(nm)
    if master_label and master_label != "ITIS 3200":
        for nm in list(keep):
            if nm.startswith('ppt/slideMasters/') and nm.endswith('.xml'):
                keep[nm] = keep[nm].replace(b"ITIS 3200", master_label.encode('utf-8'))
    needed = set()
    for nm, b in keep.items():
        if nm.endswith('.rels'):
            for m in re.findall(r'media/([^"\\]+)', b.decode('utf-8', 'ignore')):
                needed.add('ppt/media/' + m)
    keep = {nm: b for nm, b in keep.items() if not (nm.startswith('ppt/media/') and nm not in needed)}

    pres = tz.read('ppt/presentation.xml').decode('utf-8')
    rels = tz.read('ppt/_rels/presentation.xml.rels').decode('utf-8')
    kept_rels, maxid = [], 0
    for it in re.findall(r'<Relationship [^>]*/>', rels):
        rid = int(re.search(r'Id="rId(\d+)"', it).group(1)); maxid = max(maxid, rid)
        if 'relationships/slide"' in it: continue
        kept_rels.append(it)
    base = maxid + 1
    sldids = ''.join(f'<p:sldId id="{256+i}" r:id="rId{base+i}"/>' for i in range(n))
    if '<p:sldIdLst>' in pres:
        pres = re.sub(r'<p:sldIdLst>.*?</p:sldIdLst>', f'<p:sldIdLst>{sldids}</p:sldIdLst>', pres, flags=re.S)
    else:
        pres = pres.replace('</p:sldMasterIdLst>', f'</p:sldMasterIdLst><p:sldIdLst>{sldids}</p:sldIdLst>')
    slide_rels = [f'<Relationship Id="rId{base+i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i+1}.xml"/>' for i in range(n)]
    new_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                + ''.join(kept_rels) + ''.join(slide_rels) + '</Relationships>')
    ct = tz.read('[Content_Types].xml').decode('utf-8')
    ct = re.sub(r'<Override PartName="/ppt/slides/slide\d+\.xml"[^>]*/>', '', ct)
    ct = re.sub(r'<Override PartName="/ppt/notesSlides/[^"]*"[^>]*/>', '', ct)
    new_ov = ''.join(f'<Override PartName="/ppt/slides/slide{i+1}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>' for i in range(n))
    ct = ct.replace('</Types>', new_ov + '</Types>')

    os.makedirs(os.path.dirname(outpath) or '.', exist_ok=True)
    with zipfile.ZipFile(outpath, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', ct)
        z.writestr('ppt/presentation.xml', pres)
        z.writestr('ppt/_rels/presentation.xml.rels', new_rels)
        for nm, b in keep.items(): z.writestr(nm, b)
        for i, (xml, layout) in enumerate(zip(slide_xmls, layouts)):
            z.writestr(f'ppt/slides/slide{i+1}.xml', xml)
            z.writestr(f'ppt/slides/_rels/slide{i+1}.xml.rels', SLIDE_RELS.format(layout=layout))
    return n

SLIDE_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
              '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
              '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/{layout}"/>'
              '</Relationships>')

# ---- build from template ----------------------------------------------------
def build(name, outpath, template):
    with open(os.path.join(HERE, 'courses', name + '.toml'), 'rb') as fh:
        data = tomllib.load(fh)
    c = {**data.pop('course'), **data}
    n = write_deck(build_slides(c), outpath, template, master_label=c['number'])
    print(f"wrote {outpath} ({n} slides) from {name}, template={os.path.basename(template)}")

if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'itis3200-2026fa'
    out  = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'logistics.pptx')
    tmpl = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_TEMPLATE
    build(name, out, tmpl)
