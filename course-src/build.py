#!/usr/bin/env python3
"""
Course site generator — single source of truth.

Usage:
    python3 course-src/build.py            # build every course in courses/
    python3 course-src/build.py itis3200-2026fa   # build one

Reads course-src/courses/<name>.toml and writes:
  * public site pages -> teaching/<NUMBER>/<term_slug>/{index,schedule,officehours,resources,nav}.html
  * Canvas paste-HTML -> course-src/canvas-out/<name>/{syllabus,schedule}.html

NOT generated (hand-maintained): policies.html, papers.html, course.css, jquery.
Edit the .toml, rerun this script, commit. One change propagates everywhere.
"""
import sys, os, tomllib, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # repo root
SRC  = os.path.join(ROOT, "course-src")
COURSES = os.path.join(SRC, "courses")
CANVAS_OUT = os.path.join(SRC, "canvas-out")

TEXTBOOKS = [
    ('http://www.cl.cam.ac.uk/~rja14/book.html', 'Security Engineering', 'Ross Anderson'),
    ('https://www.schneier.com/book-ce.html', 'Cryptography Engineering', 'Ferguson, Schneier, and Kohno'),
    ('http://nob.cs.ucdavis.edu/book/book-intro/index.html', 'Introduction to Computer Security', 'Matt Bishop'),
    ('http://williamstallings.com/ComputerSecurity/', 'Computer Security: Principles and Practice', 'William Stallings'),
    ('http://nob.cs.ucdavis.edu/book/book-aands/index.html', 'Computer Security: Art and Science', 'Matt Bishop'),
    ('http://www.amazon.com/Security-Computing-Edition-Charles-Pfleeger/dp/0134085043', 'Security in Computing', 'Charles P. Pfleeger'),
    ('http://www.securitybook.net', 'Introduction to Computer Security', 'Michael Goodrich and Roberto Tamassia'),
    ('https://textbook.cs161.org', 'Computer Security', ', a freely available course textbook from UC Berkeley'),
]

def book_li(u, t, a):
    """Author starting with ', ' is a descriptor (comma), else 'by ...'."""
    tail = a if a.startswith(',') else f' by {a}'
    return f'<a href="{u}">{t}</a>{tail}'

def cal_iframe(cal, width='96%'):
    return (f'<iframe src="https://calendar.google.com/calendar/embed?src={cal}'
            f'%40group.calendar.google.com&ctz=America%2FNew_York" style="border: 0" '
            f'width="{width}" height="600" frameborder="0" scrolling="no"></iframe>')

def course_dir(c):
    return c['dir_slug']            # e.g. "ITIS6200"

def full_title(c):
    return f"{c['number']}: {c['title']}"

# ---------------------------------------------------------------- public pages
def head(course, css=('course',), title=None):
    links = ['<link href="../../../homepage.css" rel="stylesheet" type="text/css" />']
    if 'course' in css:
        links.insert(0, '<link href="./course.css" rel="stylesheet" type="text/css" />')
    links.append('<link rel="stylesheet" type="text/css" href="../../../smartphone.css" media="(max-width: 900px)"/>')
    return f'''<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
\t<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
\t<title>{title or course['number']+' UNC Charlotte'}</title>
\t{chr(10).join(chr(9)+l for l in links)}
\t<script src="jquery-3.2.1.min.js" type="text/javascript"></script>
\t<script>$(function(){{ $('#nav').load('./nav.html'); }});</script>
</head>
<body>
<div class="container">
   <div class="content">
\t\t<div class="contentinner">
\t<h1>{full_title(course)}</h1>
\t<div id="nav"></div>
'''

FOOT = '''\t<br><br><br><br>
\t<div id="footer"></div>
\t</div>
</div>
</div>
</body>
</html>
'''

def render_nav(c):
    items = [('./index.html','Home'), ('./policies.html','Policies'),
             ('./schedule.html','Lectures / Schedule')]
    if c.get('has_papers'): items.append(('./papers.html','Paper Reading'))
    items.append(('./resources.html','Resources'))
    w = 100 // len(items)
    cells = '\n'.join(f'          <td width="{w}%"><a href="{h}">{t}</a></td>' for h,t in items)
    return f'''<div class="navbar">
  <hr style="height: 2px; width: 100%;">
  <table style="text-align: left; margin-left: auto; margin-right: auto;" border="0" cellpadding="0" cellspacing="0">
<tbody><tr align="center">
{cells}
</tr>
</tbody>
</table>
<hr style="height: 2px; width: 100%;">
</div>
'''

def staff_block(c):
    tas = ''.join(
        f'''\t\t\t<li>{t['name']} (<a href="mailto:{t['email']}">{t['email']}</a>)
\t\t\t\t<ul><li>Office Hours: {t['office_hours']} (check the calendar before you go)</li></ul>
\t\t\t</li>\n''' for t in c.get('ta', []))
    ta_label = "Teaching Assistants" if len(c.get('ta', [])) != 1 else "Teaching Assistant"
    return f'''\t<h3>Course staff</h3>
\t<ul>
\t  <li>Instructor:  <a href="{c['instructor']['url']}">{c['instructor']['name']}</a>
\t\t<ul><li>Office Hours: {c['instructor']['office_hours']}</li></ul>
\t  </li>
\t  <li>{ta_label}:
\t    <ul>
{tas}\t\t</ul>
\t  </li>
\t</ul>
'''

def render_index(c):
    papers_ann = ('\n\t\t<li>We do weekly paper reading. Students form groups and lead one '
                  'paper discussion &mdash; see the <a href="papers.html">Paper Reading Schedule</a>.</li>'
                  if c.get('has_papers') else '')
    weights = '\n'.join(f'\t\t\t<li>{w["label"]}: {w["text"]}</li>' for w in c['weight'])
    books = '\n'.join(f'\t\t\t<li>{book_li(u,t,a)}</li>' for u,t,a in TEXTBOOKS)
    papers_ptr = (' and the <a href="papers.html">Paper Reading Schedule</a> for the full reading list'
                  if c.get('has_papers') else '')
    return head(c) + f'''
<center>
\t<b><a href="{c['instructor']['url']}">Prof. {c['instructor']['name']}</a></b>
\t<br>
\t{c['term']}
\t<p>
\t  <b>Lectures: {c['meeting']}</b>
\t\t<br>
\t  Location: {c['location']}
\t</p>
</center>

  <div>
\t<h3><a name="description"></a>Announcements</h3>
\t<ul>
\t\t<li>We follow this <a href="schedule.html">schedule</a> of teaching and assignments.</li>{papers_ann}
\t\t<li><b>AI use policy:</b> you must <b>disclose</b> how you used AI in your submissions, and you may not copy/paste AI output as your answer. See the <a href="policies.html">policies</a> for details.</li>
\t</ul>

\t<h3>Syllabus:
\t\t<a href="#basic">Course Information</a> |
\t\t<a href="#grading">Grading</a> |
\t\t<a href="#textbook">Textbook</a> |
\t\t<a href="#schedule">Schedule</a> |
\t\t<a href="#policies">Policies</a>
\t</h3>

\t<hr>
\t<h2><a id="basic" name="description"></a>Course information</h2>
\t<p>{c['description']}</p>
\t<p>Credit hours: {c['credit']}</p>
\t<p>See the <a href="schedule.html">lecture schedule</a> for more detailed information on topics covered.</p>

{staff_block(c)}
\t<p>See <a href="#officehours">below for a calendar of Office Hours</a>. Office hours may change due to unexpected conflicts, so double check the calendar before you go.</p>
\t<p>All questions and issues related to assignments, course content, etc., should be sent to the course staff. Questions related to grades, special consideration, etc. can be sent directly to Prof. {c['instructor']['name'].split()[-1]}. Note that course staff may take up to 48 hours to respond.</p>

\t<h3>Time and place</h3>
\t<p>{c['meeting_long']}</p>

\t<hr>
\t<h2 id="grading">Homework, exams, and grading</h2>
\t<p>There will be an in-class <b>open-book</b> midterm and final exam ({c['exams']['rules']}). Your grade is determined by a weighted average of the components below. (The percentage breakdown is subject to change with reasonable notice.)</p>
\t<ul>
{weights}
\t</ul>
\t<p><b>Grading scale:</b> A: 90-100, B: 80-89, C: 70-79, D: 60-69, F: below 60.</p>

\t<hr>
\t<h2 id="textbook">Textbooks</h2>
\t<p>No textbook is required, but if you would like additional references, we recommend:</p>
\t<ul>
{books}
\t</ul>
\t<p>See the <a href="resources.html">Resources</a> page for additional material.</p>

\t<hr>
\t<h2 id="schedule">Schedule</h2>
\t<h3>Lecture schedule</h3>
\t<p>See <a href="schedule.html">here</a> for a detailed schedule of lectures{papers_ptr}.</p>
\tCheck <a href="https://registrar.charlotte.edu/printable-calendar?field_semester_tid=3&field_school_year_tid=73">University Academic Calendar</a> for other important dates and deadlines.

\t<h3>Office hours</h3><a id="officehours"></a>
\t<p>Office hours will start in the second week of classes. We will use this Google calendar for office hour times:</p>
\t{cal_iframe(c['oh_calendar'])}

\t<hr>
\t<h2 id="policies">Course Policies</h2>
\t<p>See the <a href="policies.html">Course Policies page</a> for more information about course policies, including Late/Extension policy, Exams, Diversity and Inclusion, Inclusive Learning and Accessibility, Mental Health, and Collaboration and Academic Integrity.</p>

\t<h3>Syllabus Revisions</h3>
\t<p>The instructor may modify standards and requirements set forth in this syllabus at any time. Notice of such changes will be by announcement to the class.</p>
  </div>
''' + FOOT

def schedule_rows_html(c, cols):
    """cols = number of columns (5 for 3200, 6 for 6200 with Reading)."""
    out = []
    for r in c['row']:
        if 'section' in r:
            out.append(f'\t\t<tr><td class="topicheading" colspan="{cols}"><strong>{r["section"]}</strong></td></tr>')
            continue
        cls = ' class="holiday"' if r.get('holiday') else ''
        wk = f'<td>{r.get("week","")}</td>'
        if r.get('finalexam'):
            out.append(f'\t\t<tr>{wk}<td>{r.get("date","")}</td><td colspan="{cols-2}">{r.get("topic","")}</td></tr>')
            continue
        tds = [wk, f'<td{cls}>{r.get("date","")}</td>', f'<td{cls}>{r.get("topic","")}</td>']
        if cols == 6:
            tds.append(f'<td{cls}>{r.get("reading","")}</td>')
        tds.append(f'<td{cls}>{r.get("note","")}</td>')
        tds.append(f'<td{cls}>{r.get("assign","")}</td>')
        out.append('\t\t<tr>' + ''.join(tds) + '</tr>')
    return '\n'.join(out)

def render_schedule(c):
    cols = 6 if c.get('has_papers') else 5
    extra_head = '<th style="width: 28%;">Reading (required)</th>' if cols == 6 else ''
    seed = "ITIS 3200/6200" if not c.get('has_papers') else "ITIS 6200"
    return head(c, title=c['number']+' UNC Charlotte') + f'''\t<div>
\t<h2>Schedule</h2>
\t<p><b>NOTE: The current schedule is tentative and subject to change. Nonetheless it gives an idea of the material to be covered in this course.</b> The lecture notes are seeded from previous years' {seed}, and will be updated immediately before and after each lecture. Some course materials are brought from the course <a href="https://sp23.cs161.org/">CS161: Computer Security</a> at UC Berkeley.</p>
\t<table class="schedule">
\t\t<tr>
\t\t\t<th>Wk.</th><th>Date</th><th>Topic</th>{extra_head}<th>Notes</th><th>Assignments</th>
\t\t</tr>
{schedule_rows_html(c, cols)}
\t</table>
\t</div>
''' + FOOT

def render_officehours(c):
    rows = [f'\t\t<li>Instructor ({c["instructor"]["name"]}): {c["instructor"]["office_hours"]}</li>']
    for t in c.get('ta', []):
        rows.append(f'\t\t<li>{t["name"]}: {t["office_hours"]}</li>')
    return head(c) + f'''\t<h2>Office hours</h2>
\t<a id="officehours"></a>
\t<p>Office hours will start in the second week of classes.</p>
\t<ul>
{chr(10).join(rows)}
\t</ul>
\t<p>Office hours may change due to unexpected conflicts. We use this Google calendar for office hour times &mdash; double check it before you go:</p>
\t{cal_iframe(c['oh_calendar'])}
''' + FOOT

def render_resources(c):
    books = '\n'.join(f'\t\t<li>{book_li(u,t,a)}</li>' for u,t,a in TEXTBOOKS)
    papers = ('\n\t<h3>Reading research papers</h3>\n\t<p>The weekly paper reading list is on the '
              '<a href="papers.html">Paper Reading Schedule</a>; how the discussions are run is on the '
              '<a href="policies.html">Policies</a> page.</p>' if c.get('has_papers') else '')
    return head(c, css=()) + f'''\t<h2>Resources</h2>
\t<h3>Text books</h3>
\t<p>A number of excellent books and on-line resources overlap with the course's content and can provide alternate explanations despite differences in notation and approach.</p>
\t<ul>
{books}
\t</ul>{papers}
\t<h3>Pointers of online security courses</h3>
\t<ul>
\t<li>Course materials (slides, HW, projects) of <a href="https://sp23.cs161.org/">CS161: Computer Security</a> from UC Berkeley. Its textbook is also available <a href="https://textbook.cs161.org/">online</a>.</li>
\t<li>Video lectures on <a href="https://www.youtube.com/playlist?list=PL1y1iaEtjSYiiSGVlL1cHsXN_kvJOOhu-">CS253: Web Security</a> from Stanford.</li>
\t<li>Video lectures on <a href="https://ocw.mit.edu/courses/6-858-computer-systems-security-fall-2014/video_galleries/video-lectures/">6.858: System Security</a> from MIT.</li>
\t</ul>
''' + FOOT

# ---------------------------------------------------------------- Canvas paste
def canvas_url(c, page): return f"https://instructure.charlotte.edu/courses/{c['canvas_id']}/pages/{page}"

def render_canvas_syllabus(c):
    S = lambda t: f'<span style="font-size: 14pt;">{t}</span>'
    tas = ''
    for t in c.get('ta', []):
        tas += (f'            <li>{S(t["name"])}\n                <ul>\n'
                f'                    <li>{S(f"""Email: <a href="mailto:{t["email"]}">{t["email"]}</a>""")}</li>\n'
                f'                    <li>{S(f"Office hours: {t['office_hours']} (check the calendar before you go)")}</li>\n'
                f'                </ul>\n            </li>\n')
    weights = '\n'.join(f'    <li>{S(f"<strong>{w['label']}</strong>: {w['text']}")}</li>' for w in c['weight'])
    books = '\n'.join(f'    <li>{S(book_li(u,t,a))}</li>' for u,t,a in TEXTBOOKS)
    return f'''<!--
================================================================================
  {c['number']} SYLLABUS ({c['term']}) — Canvas Home Page source  [GENERATED]
  Do NOT edit by hand. Edit course-src/courses/{c['_name']}.toml and rerun build.py.
  Paste into Canvas: Edit page > HTML editor (</>) > paste.
================================================================================
-->
<p style="text-align: center;">{S(f"""<strong><a href="{c['instructor']['url']}">Prof. {c['instructor']['name']}</a></strong> """)}<br />{S(c['term'])}</p>
<p style="text-align: center;">{S(f"<strong>Lectures: {c['meeting']}</strong> ")}<br />{S(f"Location: {c['location']}")}</p>
<h2><span style="font-size: 18pt;"><strong>Course information</strong></span></h2>
<p>{S(c['description'])}</p>
<p>{S(f"Credit hours: {c['credit']}")}</p>
<h3>{S("Course staff")}</h3>
<ul>
    <li>{S(f"""Instructor: <a href="{c['instructor']['url']}">{c['instructor']['name']}</a>""")}
        <ul><li>{S(f"Office Hours: {c['instructor']['office_hours']}")}</li></ul>
    </li>
</ul>
<ul>
    <li>{S("Teaching Assistants:")}
        <ul>
{tas}        </ul>
    </li>
</ul>
<h2><strong>{S("Time and place")}</strong></h2>
<p>{S(c['meeting_long'])}</p>
<hr />
<h2>{S("<strong>Grading</strong>")}</h2>
<ul>
{weights}
</ul>
<p>{S("<strong>Grading scale:</strong> A: 90&ndash;100, B: 80&ndash;89, C: 70&ndash;79, D: 60&ndash;69, F: below 60.")}</p>
<hr />
<h2>{S("<strong>Textbooks</strong>")}</h2>
<p>{S("<strong>No textbook is required</strong>, but if you would like additional references, we recommend:")}</p>
<ul>
{books}
</ul>
<hr />
<h2>{S("<strong>Schedule &amp; Office hours</strong>")}</h2>
<p>{S(f"""See the <a href="{canvas_url(c,'schedule')}">schedule</a> page. Office hours start in week 2; we use a Google calendar (embedded on the Canvas home page).""")}</p>
'''

def render_canvas_schedule(c):
    cols = 6 if c.get('has_papers') else 5
    extra = '<th style="width: 28%;" scope="col">Reading (required)</th>' if cols==6 else ''
    return f'''<!--
================================================================================
  {c['number']} SCHEDULE ({c['term']}) — Canvas "schedule" page source  [GENERATED]
  Do NOT edit by hand. Edit course-src/courses/{c['_name']}.toml and rerun build.py.
================================================================================
-->
<p><strong>NOTE: The current schedule is tentative and subject to change.</strong> Some course materials are brought from <a href="https://sp23.cs161.org/">CS161: Computer Security</a> at UC Berkeley.</p>
<table class="schedule" style="border-collapse: collapse; width: 100%;" border="1">
    <tbody>
        <tr><th>Wk.</th><th>Date</th><th>Topic</th>{extra}<th>Notes</th><th>Assignments</th></tr>
{schedule_rows_html(c, cols)}
    </tbody>
</table>
'''

# ---------------------------------------------------------------- driver
def build_one(name):
    path = os.path.join(COURSES, name + '.toml')
    with open(path, 'rb') as fh: data = tomllib.load(fh)
    c = {**data.pop('course'), **data}   # flatten [course] scalars to top level
    c['_name'] = name
    cdir = course_dir(c); term = c['term_slug']
    outdir = os.path.join(ROOT, 'teaching', cdir, term)
    os.makedirs(outdir, exist_ok=True)
    # shared assets: ensure course.css + jquery exist (copy from any sibling term if missing)
    for asset in ('course.css', 'jquery-3.2.1.min.js'):
        dst = os.path.join(outdir, asset)
        if not os.path.exists(dst):
            for sib in sorted(os.listdir(os.path.join(ROOT,'teaching',cdir))):
                cand = os.path.join(ROOT,'teaching',cdir,sib,asset)
                if os.path.exists(cand): shutil.copy(cand, dst); break
    gen_sched = c.get('gen_schedule', True)   # 6200 keeps its rich reading schedule static
    writes = {
        'index.html': render_index(c),
        'officehours.html': render_officehours(c),
        'resources.html': render_resources(c),
        'nav.html': render_nav(c),
    }
    if gen_sched:
        writes['schedule.html'] = render_schedule(c)
    for fn, html in writes.items():
        with open(os.path.join(outdir, fn), 'w', encoding='utf-8') as fh: fh.write(html)
    # Canvas paste files
    cout = os.path.join(CANVAS_OUT, name); os.makedirs(cout, exist_ok=True)
    with open(os.path.join(cout,'syllabus.html'),'w',encoding='utf-8') as fh: fh.write(render_canvas_syllabus(c))
    if gen_sched:
        with open(os.path.join(cout,'schedule.html'),'w',encoding='utf-8') as fh: fh.write(render_canvas_schedule(c))
    static = ['policies.html'] + (['papers.html','schedule.html'] if not gen_sched else [])
    print(f"built {name}: public -> teaching/{cdir}/{term}/ ({len(writes)} pages), canvas -> course-src/canvas-out/{name}/")
    print(f"   NOT generated (hand-maintained): {', '.join(static)}")

def main():
    names = sys.argv[1:] or [f[:-5] for f in os.listdir(COURSES) if f.endswith('.toml')]
    for n in names: build_one(n)

if __name__ == '__main__':
    main()
