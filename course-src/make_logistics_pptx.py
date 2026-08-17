#!/usr/bin/env python3
"""
Generate a first-class "logistics" slide deck from a course TOML.
Stdlib only (zipfile + tomllib). Emits a minimal, valid .pptx.

Usage:
    python3 course-src/make_logistics_pptx.py itis3200-2026fa /path/to/logistics.pptx
"""
import sys, os, tomllib, zipfile
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ACCENT = "2F5F8F"; INK = "16191D"; MUTED = "6B7278"

# ---- slide content (list of {title, bullets:[(level,text,bold?)]}) ----------
def build_slides(c):
    ins = c['instructor']; site = f"https://jianxiang.info/teaching/{c['dir_slug']}/{c['term_slug']}/index.html"
    S = []
    # 1 title
    S.append({'title': f"{c['number']}", 'subtitle': [
        c['title'], c['term'], f"Prof. {ins['name']}", "First class — Logistics"]})
    # 2 meeting
    S.append({'title': "When & Where", 'bul': [
        (0, f"Lectures: {c['meeting']}", 1),
        (0, f"Location: {c['location']}", 0),
        (0, f"Credit hours: {c['credit']}", 0),
        (0, "This is an in-person class — you are expected to be here", 0),
        (0, f"Course website: {site}", 0),
        (1, "Syllabus, schedule, policies, office-hours calendar", 0),
        (0, "Canvas: assignments, quizzes, grades", 0)]})
    # 3 staff
    staff = [(0, f"Instructor: {ins['name']}", 1),
             (1, f"Office hours: {ins['office_hours']}", 0),
             (0, "Teaching Assistants:", 1)]
    for t in c.get('ta', []):
        staff.append((1, f"{t['name']} — {t['email']}", 0))
        staff.append((2, f"Office hours: {t['office_hours']}", 0))
    staff.append((0, "Office hours start in week 2; check the Google calendar (Canvas)", 0))
    S.append({'title': "Course Staff & Office Hours", 'bul': staff})
    # 4 grading
    g = [(0, w['label'], 1) for w in c['weight']]
    g.append((0, "Grading scale: A 90+, B 80s, C 70s, D 60s, F <60", 0))
    S.append({'title': "Grading", 'bul': g})
    # 5 exams
    S.append({'title': "Exams", 'bul': [
        (0, f"Midterm: {c['exams']['midterm']}", 1),
        (0, f"Final: {c['exams']['final']}", 1),
        (0, f"Format: {c['exams']['rules']}", 0),
        (0, "Make-up exams are not guaranteed; follow university policy", 0)]})
    # 5b weekly paper discussions (research course only)
    if c.get('has_papers'):
        papers_url = f"https://jianxiang.info/teaching/{c['dir_slug']}/{c['term_slug']}/papers.html"
        S.append({'title': "Weekly Paper Discussions", 'bul': [
            (0, "Everyone reads one required paper each week (~17 pp)", 1),
            (0, "Each group leads one discussion (25–30 min); some weeks two groups", 0),
            (1, "Facilitate discussion — don't just summarize", 0),
            (1, "Leading group reads both papers; present the contrast", 0),
            (0, "Sign up for a week via Canvas by 11:59pm Friday of week 1", 0),
            (1, "First-come, first-served; unclaimed weeks are assigned", 0),
            (0, "Graded: understanding, clarity, critical analysis, leadership (10%)", 0),
            (0, f"Full reading list & background: {papers_url}", 0)]})
    # 6 policies
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
    # 7 where to find
    wtf_web = [(0, "Course website (public)", 1), (1, site, 0),
               (1, "Syllabus, lecture schedule, policies, resources", 0)]
    if c.get('has_papers'):
        wtf_web.append((1, "Paper Reading Schedule (weekly readings)", 0))
    S.append({'title': "Where to Find Everything", 'bul': wtf_web + [
        (0, "Canvas (login required)", 1),
        (1, "Assignments, quizzes, grades, announcements", 0),
        (0, "Office-hours Google calendar (linked on both)", 1),
        (0, "Questions → course staff (allow up to 48 hours)", 0)]})
    return S

# ---- OOXML parts ------------------------------------------------------------
CT = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
{slide_overrides}
</Types>'''

RELS_ROOT = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>'''

def presentation_xml(n):
    sldids = ''.join(f'<p:sldId id="{256+i}" r:id="rId{i+2}"/>' for i in range(n))
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>
<p:sldIdLst>{sldids}</p:sldIdLst>
<p:sldSz cx="9144000" cy="6858000" type="screen4x3"/>
<p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>'''

def presentation_rels(n):
    rels = ['<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>']
    for i in range(n):
        rels.append(f'<Relationship Id="rId{i+2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i+1}.xml"/>')
    rels.append(f'<Relationship Id="rId{n+2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>')
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + ''.join(rels) + '</Relationships>'

THEME = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Logistics">
<a:themeElements>
<a:clrScheme name="Logistics">
<a:dk1><a:srgbClr val="16191D"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>
<a:dk2><a:srgbClr val="2F5F8F"/></a:dk2><a:lt2><a:srgbClr val="EEF1F4"/></a:lt2>
<a:accent1><a:srgbClr val="2F5F8F"/></a:accent1><a:accent2><a:srgbClr val="2F6B45"/></a:accent2>
<a:accent3><a:srgbClr val="8A5A12"/></a:accent3><a:accent4><a:srgbClr val="6B7278"/></a:accent4>
<a:accent5><a:srgbClr val="4A83C4"/></a:accent5><a:accent6><a:srgbClr val="8A3A3A"/></a:accent6>
<a:hlink><a:srgbClr val="2F5F8F"/></a:hlink><a:folHlink><a:srgbClr val="1F4467"/></a:folHlink>
</a:clrScheme>
<a:fontScheme name="Logistics">
<a:majorFont><a:latin typeface="Helvetica Neue"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>
<a:minorFont><a:latin typeface="Helvetica Neue"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont>
</a:fontScheme>
<a:fmtScheme name="Logistics">
<a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>
<a:lnStyleLst><a:ln><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>
<a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>
<a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>
</a:fmtScheme>
</a:themeElements>
</a:theme>'''

SLIDE_MASTER = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>
<p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld>
<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
</p:sldMaster>'''

SLIDE_MASTER_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>'''

SLIDE_LAYOUT = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">
<p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld>
<p:clrMapOvr><a:overrideClrMapping bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/></p:clrMapOvr>
</p:sldLayout>'''

SLIDE_LAYOUT_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>'''

SLIDE_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>'''

def _run(text, sz, color, bold):
    return (f'<a:r><a:rPr lang="en-US" sz="{sz}" b="{1 if bold else 0}" dirty="0">'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:rPr>'
            f'<a:t>{escape(text)}</a:t></a:r>')

def _accent_bar():
    # thin slate bar across the top
    return ('<p:sp><p:nvSpPr><p:cNvPr id="9" name="bar"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            '<p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="9144000" cy="72000"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val="{ACCENT}"/></a:solidFill></p:spPr>'
            '<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>')

def title_slide_xml(s):
    body = _run(s['title'], 4000, INK, True)
    subs = ''.join(f'<a:p><a:pPr algn="l"/>{_run(t, 2000 if i==0 else 1600, ACCENT if i==0 else MUTED, i==0)}</a:p>'
                   for i, t in enumerate(s['subtitle']))
    return _slide_wrap(
        f'<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="686000" y="1900000"/><a:ext cx="7772000" cy="900000"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>'
        f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p>{body}</a:p></p:txBody></p:sp>'
        f'<p:sp><p:nvSpPr><p:cNvPr id="3" name="Sub"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="700000" y="2950000"/><a:ext cx="7772000" cy="1800000"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>'
        f'<p:txBody><a:bodyPr/><a:lstStyle/>{subs}</p:txBody></p:sp>')

def content_slide_xml(s):
    title = (f'<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
             f'<p:spPr><a:xfrm><a:off x="500000" y="280000"/><a:ext cx="8144000" cy="700000"/></a:xfrm>'
             f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>'
             f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p>{_run(s["title"], 2800, ACCENT, True)}</a:p></p:txBody></p:sp>')
    paras = []
    for level, text, bold in s['bul']:
        sz = 2000 if level == 0 else (1700 if level == 1 else 1500)
        color = INK if level == 0 else (MUTED if level == 2 else INK)
        bullet = ('<a:buChar char="•"/>' if level == 0 else
                  '<a:buChar char="–"/>')
        paras.append(f'<a:p><a:pPr marL="{342900*(level+1)}" indent="-228600" lvl="{level}">'
                     f'<a:buFont typeface="Arial"/>{bullet}</a:pPr>{_run(text, sz, color, bold)}</a:p>')
    body = (f'<p:sp><p:nvSpPr><p:cNvPr id="3" name="Body"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="560000" y="1120000"/><a:ext cx="8080000" cy="5300000"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>'
            f'<p:txBody><a:bodyPr><a:normAutofit/></a:bodyPr><a:lstStyle/>{"".join(paras)}</p:txBody></p:sp>')
    return _slide_wrap(_accent_bar() + title + body)

def _slide_wrap(shapes):
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
            'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree>'
            '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/>'
            + shapes + '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')

def build(name, outpath):
    with open(os.path.join(HERE, 'courses', name + '.toml'), 'rb') as fh:
        data = tomllib.load(fh)
    c = {**data.pop('course'), **data}
    slides = build_slides(c)
    n = len(slides)
    slide_xmls = [title_slide_xml(slides[0])] + [content_slide_xml(s) for s in slides[1:]]
    overrides = '\n'.join(
        f'<Override PartName="/ppt/slides/slide{i+1}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(n))
    parts = {
        '[Content_Types].xml': CT.format(slide_overrides=overrides),
        '_rels/.rels': RELS_ROOT,
        'ppt/presentation.xml': presentation_xml(n),
        'ppt/_rels/presentation.xml.rels': presentation_rels(n),
        'ppt/theme/theme1.xml': THEME,
        'ppt/slideMasters/slideMaster1.xml': SLIDE_MASTER,
        'ppt/slideMasters/_rels/slideMaster1.xml.rels': SLIDE_MASTER_RELS,
        'ppt/slideLayouts/slideLayout1.xml': SLIDE_LAYOUT,
        'ppt/slideLayouts/_rels/slideLayout1.xml.rels': SLIDE_LAYOUT_RELS,
    }
    for i, x in enumerate(slide_xmls):
        parts[f'ppt/slides/slide{i+1}.xml'] = x
        parts[f'ppt/slides/_rels/slide{i+1}.xml.rels'] = SLIDE_RELS
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with zipfile.ZipFile(outpath, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', parts.pop('[Content_Types].xml'))
        for pn, x in parts.items():
            z.writestr(pn, x)
    print(f"wrote {outpath} ({n} slides) from {name}")

if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'itis3200-2026fa'
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'logistics.pptx')
    build(name, out)
