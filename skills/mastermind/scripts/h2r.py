#!/usr/bin/env python3
"""h2r — HTML mockups -> React/Next components.

Three commands:
  extract  wireframe/ -> .h2r/manifest.md   (small digest + repeat detection; the model reads THIS, not the HTML)
  emit     .h2r/plan.json -> real .tsx      (script does the markup transform; the model never retypes markup)
  verify   sanity-check emitted files

Design: the script does everything mechanical (parse, dedupe, html->jsx, prop extraction,
link rewriting, css wiring). The model only writes plan.json — names, prop names, client flags.

ponytail: stdlib only (html.parser). No bs4/lxml dep for a one-shot codegen tool.
"""
import argparse, collections, html, json, os, re, shutil, sys
from html.parser import HTMLParser
from pathlib import Path

VOID = {"area","base","br","col","embed","hr","img","input","link","meta","param","source","track","wbr"}
INLINE = {"a","b","strong","em","i","span","code","small","sup","sub","u","mark","br","label","abbr","time","kbd"}

# html.parser lowercases everything; SVG needs its case back
TAG_CASE = {"lineargradient":"linearGradient","radialgradient":"radialGradient","clippath":"clipPath",
    "textpath":"textPath","foreignobject":"foreignObject","fecolormatrix":"feColorMatrix",
    "fegaussianblur":"feGaussianBlur","feoffset":"feOffset","feblend":"feBlend","femerge":"feMerge",
    "femergenode":"feMergeNode","fedropshadow":"feDropShadow","feflood":"feFlood","fecomposite":"feComposite",
    "animatetransform":"animateTransform","animatemotion":"animateMotion"}

ATTR = {"class":"className","for":"htmlFor","tabindex":"tabIndex","colspan":"colSpan","rowspan":"rowSpan",
    "maxlength":"maxLength","minlength":"minLength","readonly":"readOnly","autocomplete":"autoComplete",
    "autofocus":"autoFocus","autoplay":"autoPlay","playsinline":"playsInline","srcset":"srcSet",
    "crossorigin":"crossOrigin","datetime":"dateTime","enctype":"encType","novalidate":"noValidate",
    "contenteditable":"contentEditable","spellcheck":"spellCheck","accesskey":"accessKey",
    "allowfullscreen":"allowFullScreen","frameborder":"frameBorder","usemap":"useMap","srclang":"srcLang",
    "http-equiv":"httpEquiv","accept-charset":"acceptCharset","inputmode":"inputMode","itemprop":"itemProp",
    "formaction":"formAction","cellpadding":"cellPadding","cellspacing":"cellSpacing",
    # svg
    "viewbox":"viewBox","preserveaspectratio":"preserveAspectRatio","stroke-width":"strokeWidth",
    "stroke-linecap":"strokeLinecap","stroke-linejoin":"strokeLinejoin","stroke-dasharray":"strokeDasharray",
    "stroke-dashoffset":"strokeDashoffset","stroke-opacity":"strokeOpacity","fill-rule":"fillRule",
    "clip-rule":"clipRule","clip-path":"clipPath","stop-color":"stopColor","stop-opacity":"stopOpacity",
    "fill-opacity":"fillOpacity","stroke-miterlimit":"strokeMiterlimit","text-anchor":"textAnchor",
    "font-family":"fontFamily","font-size":"fontSize","font-weight":"fontWeight","letter-spacing":"letterSpacing",
    "xlink:href":"xlinkHref","gradientunits":"gradientUnits","gradienttransform":"gradientTransform",
    "patternunits":"patternUnits","markerwidth":"markerWidth","markerheight":"markerHeight",
    "maskunits":"maskUnits","dominant-baseline":"dominantBaseline","shape-rendering":"shapeRendering"}

DROP_ATTR_PREFIX = ("on",)          # onclick etc — static mockup JS, not app logic
MARK = "\x00"                       # prop-substitution marker


# ---------------------------------------------------------------- parse

class Node:
    __slots__ = ("tag","attrs","kids","text","parent")
    def __init__(self, tag, attrs=None, text=None):
        self.tag, self.attrs, self.kids, self.text, self.parent = tag, attrs or {}, [], text, None

    @property
    def classes(self):
        return [c for c in (self.attrs.get("class") or "").split() if c]

    def count(self):
        return 1 + sum(k.count() for k in self.kids)


class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root")
        self.stack = [self.root]

    def _add(self, n):
        n.parent = self.stack[-1]
        self.stack[-1].kids.append(n)
        return n

    def handle_starttag(self, tag, attrs):
        n = self._add(Node(tag, {k: v for k, v in attrs}))
        if tag not in VOID:
            self.stack.append(n)

    def handle_startendtag(self, tag, attrs):
        self._add(Node(tag, {k: v for k, v in attrs}))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return
        # stray close tag: ignore

    def handle_data(self, data):
        if data:
            self._add(Node("#text", text=data))

    def handle_comment(self, data):
        self._add(Node("#comment", text=data))


def parse(path: Path) -> Node:
    p = Parser()
    p.feed(path.read_text(encoding="utf-8", errors="replace"))
    return p.root


def find(root: Node, tag):
    if root.tag == tag:
        return root
    for k in root.kids:
        r = find(k, tag)
        if r:
            return r
    return None


def at(node: Node, relpath: str) -> Node:
    """relpath: '.' or '/2/0'. Attr suffix ('@href') must be stripped by caller."""
    if relpath in (".", ""):
        return node
    for part in relpath.strip("/").split("/"):
        node = node.kids[int(part)]
    return node


def path_of(node: Node, stop: Node) -> str:
    parts = []
    while node is not stop and node.parent is not None:
        parts.append(str(node.parent.kids.index(node)))
        node = node.parent
    return "/" + "/".join(reversed(parts)) if parts else "."


def blank(n: Node) -> bool:
    return n.tag == "#text" and not n.text.strip()


def sig(n: Node) -> str:
    if n.tag == "#text":
        return "" if blank(n) else "t"
    if n.tag == "#comment":
        return ""
    cls = ".".join(sorted(n.classes))
    inner = ",".join(s for s in (sig(k) for k in n.kids) if s)
    return f"{n.tag}.{cls}({inner})"


def text_of(n: Node) -> str:
    if n.tag == "#text":
        return n.text.strip()
    return " ".join(t for t in (text_of(k) for k in n.kids) if t).strip()


# ---------------------------------------------------------------- repeats

def repeat_groups(pages, min_nodes=4, min_count=2):
    """Group structurally identical subtrees across all pages. Outermost wins."""
    buckets = {}
    for name, root in pages:
        body = find(root, "body") or root
        def walk(n):
            if n.tag.startswith("#"):
                return
            if n.count() >= min_nodes:
                buckets.setdefault(sig(n), []).append((name, body, n))
            for k in n.kids:
                walk(k)
        walk(body)

    groups, claimed = [], set()
    for s, inst in sorted(buckets.items(), key=lambda kv: -kv[1][0][2].count()):
        if len(inst) < min_count:
            continue
        ids = [(nm, id(n)) for nm, _, n in inst]
        if any(i in claimed for i in ids):
            continue
        for nm, _, n in inst:
            def mark(x):
                claimed.add((nm, id(x)))
                for k in x.kids:
                    mark(k)
            mark(n)
        groups.append(inst)

    groups.sort(key=lambda g: (-len(g), -g[0][2].count()))
    return {f"R{i+1}": g for i, g in enumerate(groups)}


def varying(inst):
    """Paths (relative to each instance root) whose text/attr differs between instances."""
    roots = [n for _, _, n in inst]
    out = []
    def walk(rel, nodes):
        a = nodes[0]
        if a.tag == "#text":
            vals = [n.text.strip() for n in nodes]
            if len(set(vals)) > 1:
                out.append((rel, "text", vals))
            return
        if a.tag.startswith("#"):
            return
        for k in a.attrs:
            vals = [n.attrs.get(k) or "" for n in nodes]
            if len(set(vals)) > 1:
                out.append((rel + "@" + k, "attr", vals))
        for i in range(len(a.kids)):
            if any(len(n.kids) != len(a.kids) for n in nodes):
                return
            walk(("" if rel == "." else rel) + "/" + str(i), [n.kids[i] for n in nodes])
    walk(".", roots)
    return out


# ---------------------------------------------------------------- extract

def outline(body, root_paths, depth, buf, node=None, d=0, base=None):
    node = node or body
    for k in node.kids:
        if k.tag == "#comment" or blank(k):
            continue
        p = path_of(k, base or body)
        if k.tag == "#text":
            t = k.text.strip()
            if t and d <= depth:
                buf.append(f"{'  '*d}{p} \"{t[:60]}\"")
            continue
        cls = "".join("." + c for c in k.classes[:3])
        rid = root_paths.get(id(k))
        label = f"{'  '*d}{k.tag}{cls} {p}"
        if rid:
            buf.append(label + f"  <= {rid}")
            continue
        if d >= depth:
            if k.count() > 1:
                buf.append(label + f"  [{k.count()} nodes]")
            else:
                buf.append(label)
            continue
        t = text_of(k)
        if t and k.count() <= 3:
            buf.append(f'{label}  "{t[:50]}"')   # leaf-ish: text inline, don't recurse
            continue
        buf.append(label)
        outline(body, root_paths, depth, buf, k, d + 1, base or body)


def cmd_extract(a):
    src = Path(a.src)
    files = sorted(p for p in src.glob("*.html"))
    if not files:
        sys.exit(f"no .html in {src}")
    pages = [(p.stem, parse(p)) for p in files]
    groups = repeat_groups(pages, a.min_nodes, a.min_count)
    root_paths = {}
    for gid, inst in groups.items():
        for _, _, n in inst:
            root_paths[id(n)] = gid

    L = [f"# h2r manifest — {len(pages)} pages, {sum(r.count() for _, r in pages)} nodes",
         "", "paths are child indices from <body>. use them in plan.json.", ""]

    css = sorted(p.name for p in src.glob("*.css"))
    L.append("## assets")
    L.append("css: " + (", ".join(css) or "none"))
    tok = src / "tokens.css"
    if tok.exists():
        v = sorted(set(re.findall(r"(--[\w-]+)\s*:", tok.read_text(encoding="utf-8", errors="replace"))))
        L.append(f"tokens.css vars ({len(v)}): " + ", ".join(v[:40]) + (" ..." if len(v) > 40 else ""))
    head = find(pages[0][1], "head")
    if head:
        links = [jsx_attrs_str(k) for k in head.kids if k.tag == "link"]
        if links:
            L.append("head links: " + " | ".join(links[:6]))
    scripts = sum(1 for _, r in pages for _ in iter_tag(r, "script"))
    if scripts:
        L.append(f"note: {scripts} <script> tag(s) present — dropped on emit, reported by verify")
    L.append("")

    L.append("## repeat groups (component candidates)")
    if not groups:
        L.append("none")
    for gid, inst in groups.items():
        n0 = inst[0][2]
        cls = "".join("." + c for c in n0.classes[:3])
        L.append(f"\n{gid}  {n0.tag}{cls}  x{len(inst)}  ({n0.count()} nodes)")
        L.append("  at: " + ", ".join(f"{nm}:{path_of(n, b)}" for nm, b, n in inst[:6])
                 + (" ..." if len(inst) > 6 else ""))
        var = varying(inst)
        if var:
            L.append("  varies (prop candidates):")
            for rel, kind, vals in var[:12]:
                s = " | ".join((v or "")[:28] for v in vals[:3])
                L.append(f"    {rel}  {kind}  [{s}]")
        else:
            L.append("  varies: nothing — identical everywhere (static component, no props)")
        L.append("  text: " + text_of(n0)[:110])
    L.append("")

    for name, root in pages:
        body = find(root, "body") or root
        L.append(f"## page: {name}.html  ({body.count()} nodes)")
        buf = []
        outline(body, root_paths, a.depth, buf)
        L += buf
        L.append("")

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.md").write_text("\n".join(L), encoding="utf-8")
    (out / "plan.schema.json").write_text(PLAN_SCHEMA, encoding="utf-8")
    print(f"wrote {out/'manifest.md'} ({len(L)} lines) - {len(groups)} repeat groups, {len(pages)} pages")
    print(f"next: write {out/'plan.json'} (schema: {out/'plan.schema.json'}), then: h2r.py emit")


def iter_tag(n, tag):
    if n.tag == tag:
        yield n
    for k in n.kids:
        yield from iter_tag(k, tag)


# ---------------------------------------------------------------- html -> jsx

def jsx_attr_pair(k, v):
    if k.lower().startswith(DROP_ATTR_PREFIX) and k.lower() not in ("only",):
        return None
    if k == "style":
        obj = style_obj(v)
        # TS rejects CSS custom properties in a CSSProperties literal without a cast
        cast = " as React.CSSProperties" if '"--' in obj else ""
        return "style={{" + obj + "}" + cast + "}"
    name = ATTR.get(k, k)
    if not (name.startswith("data-") or name.startswith("aria-")) and "-" in name and name not in ATTR.values():
        name = ATTR.get(k, name)
    if v is None:
        # bare attr is `true` in JSX — only correct for the real boolean attributes;
        # everything else (crossOrigin, download…) is typed string and needs ""
        return name if name.lower() in BOOL_ATTR else f'{name}=""'
    if MARK in v:
        return f"{name}={{{v.replace(MARK,'')}}}"
    if name in NUM_ATTR and v.lstrip("-").isdigit():
        return f"{name}={{{v}}}"
    return f'{name}="{v}"' if '"' not in v else f"{name}={{{json.dumps(v)}}}"


BOOL_ATTR = {"required", "disabled", "checked", "selected", "open", "hidden", "multiple",
             "readonly", "readOnly", "autofocus", "autoFocus", "novalidate", "noValidate",
             "defer", "async", "reversed", "loop", "muted", "controls", "autoplay", "autoPlay",
             "default", "ismap", "isMap", "playsinline", "playsInline", "itemscope", "itemScope"}
NUM_ATTR = {"rows", "cols", "size", "maxLength", "minLength", "tabIndex",
            "colSpan", "rowSpan", "span", "start"}


def style_obj(v):
    out = []
    for decl in (v or "").split(";"):
        if ":" not in decl:
            continue
        k, val = decl.split(":", 1)
        k, val = k.strip(), val.strip()
        key = k if k.startswith("--") else re.sub(r"-(\w)", lambda m: m.group(1).upper(), k)
        out.append(f"{json.dumps(key) if not key.isidentifier() else key}: {json.dumps(val)}")
    return ", ".join(out)


# HTML's value/checked ARE the initial value; React's same-named props mean "controlled",
# which warns and renders read-only until Phase 8 attaches a handler.
UNCONTROLLED = {("input", "value"): "defaultValue", ("textarea", "value"): "defaultValue",
                ("input", "checked"): "defaultChecked"}


def jsx_attrs_str(n):
    parts = [p for p in (jsx_attr_pair(UNCONTROLLED.get((n.tag, k), k), v)
                         for k, v in n.attrs.items() if not (n.tag == "option" and k == "selected")) if p]
    if n.tag == "select":
        # React wants the initial selection on the <select>, not as `selected` on an <option>
        sel = next((o for o in iter_tag(n, "option") if "selected" in o.attrs), None)
        if sel is not None:
            parts.append(f'defaultValue="{sel.attrs.get("value") or text_of(sel).strip()}"')
    return (" " + " ".join(parts)) if parts else ""


def esc_text(t):
    # '<' and '>' must go back to entities: the parser decoded them out of the source,
    # and raw ones in JSX text are parsed as tags (e.g. <code>&lt;dialog&gt;</code>).
    return (t.replace("{", "{'{'}").replace("}", "{'}'}")
             .replace("<", "&lt;").replace(">", "&gt;"))


def render(n, ind, usage=None, body=None, out=None, ctx=None):
    """usage: {path -> callsite_string} replaces whole subtrees with component calls."""
    pad = "  " * ind
    if usage is not None and body is not None:
        p = path_of(n, body)
        if p in usage:
            return "\n".join(pad + l for l in usage[p].split("\n"))
    if n.tag == "#text":
        t = n.text
        if MARK in t:
            return pad + t.replace(MARK, "")
        t = t.strip()
        return pad + esc_text(t) if t else ""
    if n.tag == "#comment":
        return pad + "{/*" + n.text.replace("*/", "* /") + "*/}"
    if n.tag in ("script",):
        return ""
    tag = TAG_CASE.get(n.tag, n.tag)
    attrs = jsx_attrs_str(n)
    if ctx and tag == "a":
        attrs = ctx.rewrite_link(n, attrs)
        tag = ctx.link_tag(n, tag)
    if "data-h2r-link" in attrs:            # href became a prop but points at an internal route
        attrs = attrs.replace(' data-h2r-link="1"', "")
        if ctx and ctx.framework == "next":
            ctx.used_link, tag = True, "Link"
    if n.tag in VOID or (not n.kids and n.tag not in ("div","span","p","script","textarea")):
        return f"{pad}<{tag}{attrs} />"
    keep_ws = any(k.tag in INLINE for k in n.kids)
    kids = [k for k in n.kids if not (blank(k) and not keep_ws)]
    if len(kids) == 1 and kids[0].tag == "#text":
        t = kids[0].text
        t = t.replace(MARK, "") if MARK in t else esc_text(t.strip())
        return f"{pad}<{tag}{attrs}>{t}</{tag}>"
    inner = [s for s in (render(k, ind + 1, usage, body, out, ctx) for k in kids) if s.strip()]
    return f"{pad}<{tag}{attrs}>\n" + "\n".join(inner) + f"\n{pad}</{tag}>"


# ---------------------------------------------------------------- emit

class Ctx:
    def __init__(self, framework, routes):
        self.framework, self.routes, self.used_link = framework, routes, False

    def link_tag(self, n, tag):
        if self.framework == "next" and self._route(n) is not None:
            self.used_link = True
            return "Link"
        return tag

    def _route(self, n):
        href, _ = split_href(n.attrs.get("href") or "")
        return self.routes.get(Path(href).stem) if href.endswith(".html") else None

    def rewrite_link(self, n, attrs):
        r = self._route(n)
        if r is None:
            return attrs
        _, suffix = split_href(n.attrs.get("href") or "")
        return re.sub(r'href="[^"]*"', f'href="{r}{suffix}"', attrs)


def split_href(href):
    """('book.html?tier=x#y') -> ('book.html', '?tier=x#y'). Query counts, not just the anchor."""
    i = min((href.find(c) for c in "?#" if c in href), default=-1)
    return (href, "") if i < 0 else (href[:i], href[i:])


def sub_props(root, props, ctx):
    """Insert markers for props into a deep-copied instance."""
    import copy
    root = copy.deepcopy(root)
    root.parent = None
    for p in props:
        ref, _, attr = p["path"].partition("@")
        node = at(root, ref or ".")
        if p.get("kind") == "children":
            node.kids = [Node("#text", text=MARK + "{children}" + MARK)]
        elif attr:
            if node.tag == "a" and attr == "href" and ctx._route(node) is not None:
                node.attrs["data-h2r-link"] = "1"     # value became a prop; still an internal route
            node.attrs[attr] = MARK + p["name"] + MARK
        else:
            node.text = MARK + "{" + p["name"] + "}" + MARK
    return root


def prop_value(inst, p, ctx):
    ref, _, attr = p["path"].partition("@")
    node = at(inst, ref or ".")
    if not attr:
        return text_of(node)
    v = node.attrs.get(attr) or ""
    if attr in ("href", "action"):
        base, suffix = split_href(v)
        if base.endswith(".html"):
            r = ctx.routes.get(Path(base).stem)
            if r is not None:
                v = r + suffix
    return v


def callsite(name, props, inst, ctx):
    parts = []
    child = None
    for p in props:
        if p.get("kind") == "children":
            ref, _, _ = p["path"].partition("@")
            child = at(inst, ref or ".")
            continue
        v = prop_value(inst, p, ctx)
        parts.append(f'{p["name"]}="{v}"' if '"' not in v and "\n" not in v else f'{p["name"]}={{{json.dumps(v)}}}')
    a = (" " + " ".join(parts)) if parts else ""
    if child is None:
        return f"<{name}{a} />"
    inner = "\n".join(s for s in (render(k, 0, ctx=ctx) for k in child.kids if not blank(k)) if s.strip())
    return f"<{name}{a}>\n{inner}\n</{name}>"


def inline_css(style_node):
    return "".join(k.text or "" for k in style_node.kids if k.tag == "#text").strip()


# ---------------------------------------------------------------- css hoisting
# Mockup pages carry the whole stylesheet inline, reset and all, repeated on every page.
# Emitting that per route gives you N copies of :root/body fighting each other. Split it:
# document-scope and repeated rules go to one global.css, only the residue stays per page.

# a selector is document-scope when the WHOLE of it is the root/element/universal target
# (`body`, `body.dark`, `:root`, `*::before`) - `body > .nav` is ordinary page styling.
DOC_SEL = re.compile(r"^(:root|html|body|\*)([.#:\[][^\s>+~,]*)*$", re.I)
DOC_AT = ("@font-face", "@import", "@keyframes", "@charset", "@page")


def css_rules(css):
    """Split a stylesheet into top-level rules. Brace-aware, comment- and string-safe."""
    out, buf, depth, i, n = [], [], 0, 0, len(css)
    while i < n:
        ch = css[i]
        if css.startswith("/*", i):
            j = css.find("*/", i + 2)
            j = n if j < 0 else j + 2
            buf.append(css[i:j]); i = j; continue
        if ch in "\"'":
            j = i + 1
            while j < n and css[j] != ch:
                j += 2 if css[j] == "\\" else 1
            buf.append(css[i:j + 1]); i = j + 1; continue
        buf.append(ch)
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth <= 0:
                out.append("".join(buf).strip()); buf, depth = [], 0
        elif ch == ";" and depth == 0:      # @import / @charset end at the semicolon
            out.append("".join(buf).strip()); buf = []
        i += 1
    out.append("".join(buf).strip())
    return [r for r in out if r.strip(" \t\r\n;")]


def doc_scope(rule):
    """Does this rule style the document itself (so it belongs in global.css)?"""
    sel = rule.split("{", 1)[0].strip()
    if sel.startswith(("@media", "@supports", "@layer", "@container")):
        inner = rule.split("{", 1)[1].rsplit("}", 1)[0] if "{" in rule else ""
        return any(doc_scope(r) for r in css_rules(inner))
    if sel.startswith("@"):
        return sel.split()[0].lower().startswith(DOC_AT)
    return any(DOC_SEL.match(s.strip()) for s in sel.split(",") if s.strip())


def css_key(rule):
    return re.sub(r"\s+", " ", rule).strip()


def split_css(page_css):
    """{stem: css} -> (global_rules, {stem: residue_rules}).

    Hoisted: document-scope rules, and any rule appearing verbatim on 2+ pages. One page in
    the set means there is no per-route CSS to speak of — all of it is global."""
    parsed = {stem: css_rules(t) for stem, t in page_css.items()}
    seen = collections.Counter(css_key(r) for rules in parsed.values() for r in set_ord(rules))
    hoist = (lambda r: True) if len(parsed) < 2 else \
        (lambda r: doc_scope(r) or seen[css_key(r)] > 1)
    glob, taken, residue = [], set(), {}
    for stem, rules in parsed.items():
        keep = []
        for r in rules:
            if hoist(r):
                if css_key(r) not in taken:
                    taken.add(css_key(r)); glob.append(r)
            else:
                keep.append(r)
        residue[stem] = keep
    return glob, residue


def set_ord(rules):
    """Unique rules, source order — a page repeating a rule twice must not look like two pages."""
    seen, out = set(), []
    for r in rules:
        if css_key(r) not in seen:
            seen.add(css_key(r)); out.append(r)
    return out


def ts_type(p):
    return "ReactNode" if p.get("kind") == "children" else p.get("type", "string")


def cmd_emit(a):
    plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
    src = Path(plan.get("wireframe", "wireframe"))
    outdir = Path(plan.get("outDir", "."))
    fw = plan.get("framework", "next")
    files = sorted(src.glob("*.html"))
    pages = [(p.stem, parse(p)) for p in files]
    groups = repeat_groups(pages, plan.get("minNodes", 4), plan.get("minCount", 2))

    routes = {p["src"].replace(".html", ""): p.get("route", "/" + p["src"].replace(".html", ""))
              for p in plan.get("pages", [])}
    ctx = Ctx(fw, routes)
    comp_dir = plan.get("componentsDir", "components")

    written, usage_by_page = [], {}
    for c in plan.get("components", []):
        props = c.get("props", [])
        if "repeat" in c:
            inst = groups.get(c["repeat"])
            if not inst:
                sys.exit(f"plan references {c['repeat']} which no longer exists - re-run extract")
            root = inst[0][2]
            for nm, body, n in inst:
                usage_by_page.setdefault(nm, {})[path_of(n, body)] = callsite(c["name"], props, n, ctx)
        else:  # explicit source "page:/0/1"
            pg, _, rel = c["source"].partition(":")
            body = find(dict(pages)[pg], "body")
            root = at(body, rel)
            usage_by_page.setdefault(pg, {})[rel] = callsite(c["name"], props, root, ctx)

        ctx.used_link = False
        body_jsx = render(sub_props(root, props, ctx), 2, ctx=ctx)
        sig_ = ", ".join(p["name"] for p in props)
        types = "; ".join(f'{p["name"]}: {ts_type(p)}' for p in props)
        head = f"export default function {c['name']}({{ {sig_} }}: {{ {types} }}) {{" if props \
            else f"export default function {c['name']}() {{"
        pre = "'use client'\n\n" if c.get("client") else ""
        if any(p.get("kind") == "children" for p in props):
            pre += "import type { ReactNode } from 'react'\n\n"
        if ctx.used_link and fw == "next":
            pre += "import Link from 'next/link'\n\n"
            ctx.used_link = False
        code = f"{pre}{head}\n  return (\n{body_jsx}\n  )\n}}\n"
        written.append(write(outdir / comp_dir / f"{c['name']}.tsx", code, a.dry))

    # a mockup with no build step keeps its page CSS in an inline <style>; that is most of the
    # styling. Drop it and the page renders naked. Split it once, up front: shared rules to
    # global.css (imported by the layout), only what is genuinely page-local stays per route.
    styles_rel = "app/styles" if fw == "next" else "src/styles"
    styles = outdir / styles_rel
    page_css = {}
    for pg in plan.get("pages", []):
        stem = pg["src"].replace(".html", "")
        t = "\n".join(x for x in (inline_css(n) for n in iter_tag(dict(pages)[stem], "style")) if x)
        if t:
            page_css[stem] = t
    global_rules, residue = split_css(page_css) if page_css else ([], {})

    imports_all = sorted({c["name"] for c in plan.get("components", [])})
    for pg in plan.get("pages", []):
        stem = pg["src"].replace(".html", "")
        body = find(dict(pages)[stem], "body")
        usage = usage_by_page.get(stem, {})
        ctx.used_link = False
        kids = [render(k, 3, usage, body, ctx=ctx) for k in body.kids
                if not blank(k) and k.tag not in ("script", "style")]
        jsx = "\n".join(s for s in kids if s.strip())
        used = [n for n in imports_all if re.search(rf"<{n}[\s/>]", jsx)]
        imp = "".join(f"import {n} from '@/{comp_dir}/{n}'\n" for n in used) if fw == "next" \
            else "".join(f"import {n} from '../{comp_dir}/{n}'\n" for n in used)
        if ctx.used_link and fw == "next":
            imp = "import Link from 'next/link'\n" + imp
        name = pg.get("name") or stem.title().replace("-", "")
        head = find(dict(pages)[stem], "head")
        if residue.get(stem):
            css_name = f"page-{stem}.css"
            written.append(write(styles / css_name, "\n\n".join(residue[stem]) + "\n", a.dry))
            imp = (f"import '@/app/styles/{css_name}'\n" if fw == "next"
                   else f"import '../styles/{css_name}'\n") + imp
        title = text_of(find(head, "title")) if head and find(head, "title") else None
        meta = f"\nexport const metadata = {{ title: {json.dumps(title)} }}\n" if title and fw == "next" else ""
        code = f"{imp}{meta}\nexport default function {name}() {{\n  return (\n    <>\n{jsx}\n    </>\n  )\n}}\n"
        if fw == "next":
            r = pg.get("route", "/" + stem).strip("/")
            dest = outdir / "app" / (r + "/page.tsx" if r else "page.tsx")
        else:
            dest = outdir / "src" / "pages" / f"{name}.tsx"
        written.append(write(dest, code, a.dry))

    # css — mockup stylesheets copied as-is, then the hoisted global last (it came from the
    # inline <style>, which in the mockup's head sits after the <link>s, so it wins the same way)
    css_names = []
    for c in sorted(src.glob("*.css"), key=lambda p: (p.name != "tokens.css", p.name)):
        if not a.dry:
            styles.mkdir(parents=True, exist_ok=True)
            shutil.copy2(c, styles / c.name)
        written.append(str(styles / c.name)); css_names.append(c.name)
    if global_rules:
        hdr = f"/* hoisted by h2r from the inline <style> of {len(page_css)} mockup page(s) */\n\n"
        written.append(write(styles / "global.css", hdr + "\n\n".join(global_rules) + "\n", a.dry))
        css_names.append("global.css")
    imports_css = "".join(f"import './styles/{n}'\n" for n in css_names)

    if plan.get("layout", True) and fw == "next":
        head = find(pages[0][1], "head")
        # keep remote <link>s (fonts); local stylesheets are copied to styles/ and imported above
        links = "\n        ".join(render(k, 0).strip() for k in (head.kids if head else [])
                                  if k.tag == "link" and "//" in (k.attrs.get("href") or ""))
        title = text_of(find(head, "title")) if head and find(head, "title") else plan.get("title", "App")
        code = (f"{imports_css}\nexport const metadata = {{ title: {json.dumps(title)} }}\n\n"
                f"export default function RootLayout({{ children }}: {{ children: React.ReactNode }}) {{\n"
                f"  return (\n    <html lang=\"en\">\n      <head>\n        {links}\n      </head>\n"
                f"      <body>{{children}}</body>\n    </html>\n  )\n}}\n")
        written.append(write(outdir / "app/layout.tsx", code, a.dry))
    elif fw != "next":
        written.append(write(outdir / "src/styles.ts", "// import these in your entry:\n" + imports_css, a.dry))

    print(("DRY RUN - would write:\n" if a.dry else "wrote:\n") + "\n".join("  " + w for w in written))


def write(path: Path, code: str, dry: bool):
    if not dry:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(code, encoding="utf-8")
    return str(path)


# ---------------------------------------------------------------- verify

def cmd_verify(a):
    bad = []
    files = [p for p in Path(a.dir).rglob("*.tsx")]
    for f in files:
        t = f.read_text(encoding="utf-8", errors="replace")
        for pat, msg in ((r'\sclass="', "raw class= (should be className)"),
                         (r'\sfor="', "raw for= (should be htmlFor)"),
                         (r"\son[a-z]+=\"", "inline html handler left behind"),
                         (r"<script", "<script> in JSX")):
            for m in re.finditer(pat, t):
                bad.append(f"{f}:{t[:m.start()].count(chr(10))+1}  {msg}")
        if t.count("{") != t.count("}"):
            bad.append(f"{f}  unbalanced braces ({t.count('{')} vs {t.count('}')})")
        if t.count("(") != t.count(")"):
            bad.append(f"{f}  unbalanced parens")

    # route-scoped CSS must not style the document or repeat another route's rules — that is
    # the same stylesheet emitted N times, and the last route loaded wins.
    css = [p for p in Path(a.dir).rglob("page-*.css") if p.parent.name == "styles"]
    where = collections.defaultdict(list)
    for f in css:
        for r in css_rules(f.read_text(encoding="utf-8", errors="replace")):
            if doc_scope(r):
                bad.append(f"{f}  document-scope rule in route CSS: {css_key(r)[:60]}"
                           f"  -> belongs in styles/global.css (re-run emit)")
            where[css_key(r)].append(f.name)
    for k, fs in where.items():
        if len(fs) > 1:
            bad.append(f"{', '.join(sorted(set(fs)))}  same rule in {len(set(fs))} route files: "
                       f"{k[:60]}  -> hoist to styles/global.css (re-run emit)")

    print(f"{len(files)} tsx files, {sum(len(p.read_text(encoding='utf-8',errors='replace').splitlines()) for p in files)} lines"
          + (f", {len(css)} route css files" if css else ""))
    if bad:
        print("ISSUES:\n" + "\n".join("  " + b for b in bad))
        sys.exit(1)
    print("clean - now run the real typecheck/build (tsc --noEmit / next build)")


def cmd_selftest(a):
    """The css splitter is the only parser here that can silently emit wrong output."""
    r = css_rules('@import "x.css";\n:root{--a:1}\n/* c } */\n.a{content:"}"}\n@media(w:1px){body{m:0}}')
    assert r == ['@import "x.css";', ':root{--a:1}', '/* c } */\n.a{content:"}"}',
                 '@media(w:1px){body{m:0}}'], r
    assert [doc_scope(x) for x in r] == [True, True, False, True], [doc_scope(x) for x in r]
    assert doc_scope("body.dark{a:1}") and doc_scope("*,*::before{b:2}")
    assert not doc_scope("body > .nav{c:3}") and not doc_scope(".card{d:4}")

    g, res = split_css({"a": ":root{--x:1}\n.hero{a:1}\n.btn{b:2}",
                        "b": ":root{--x:1}\n.list{c:3}\n.btn{b:2}"})
    assert [css_key(x) for x in g] == [":root{--x:1}", ".btn{b:2}"], g   # shared + doc-scope
    assert [css_key(x) for x in res["a"]] == [".hero{a:1}"], res         # residue only
    assert [css_key(x) for x in res["b"]] == [".list{c:3}"], res
    assert split_css({"only": ".hero{a:1}"})[1]["only"] == []            # 1 page -> all global
    assert split_css({"a": ".x{a:1}\n.x{a:1}", "b": ".y{b:2}"})[0] == [] # dup within a page ≠ shared
    print("selftest ok")


PLAN_SCHEMA = json.dumps({
    "framework": "next | react",
    "wireframe": "wireframe",
    "outDir": ".",
    "componentsDir": "components",
    "layout": True,
    "components": [{
        "name": "FeatureCard",
        "repeat": "R1  (id from manifest; or use 'source':'index:/1/3' for a one-off)",
        "client": False,
        "props": [
            {"name": "title", "path": "/1/0", "_": "path to a #text node -> string prop"},
            {"name": "href", "path": ".@href", "_": "@attr -> attribute prop"},
            {"name": "children", "path": "/3", "kind": "children", "_": "subtree -> slot"}
        ]
    }],
    "pages": [{"src": "index.html", "route": "/", "name": "Home"}]
}, indent=2)


def main():
    ap = argparse.ArgumentParser(prog="h2r", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("extract", help="html -> manifest.md (read this, not the html)")
    e.add_argument("src", nargs="?", default="wireframe")
    e.add_argument("--out", default=".h2r")
    e.add_argument("--depth", type=int, default=4)
    e.add_argument("--min-nodes", type=int, default=4)
    e.add_argument("--min-count", type=int, default=2)
    e.set_defaults(fn=cmd_extract)

    m = sub.add_parser("emit", help="plan.json -> .tsx")
    m.add_argument("--plan", default=".h2r/plan.json")
    m.add_argument("--dry", action="store_true")
    m.set_defaults(fn=cmd_emit)

    v = sub.add_parser("verify", help="sanity-check emitted tsx + route css")
    v.add_argument("dir", nargs="?", default=".")
    v.set_defaults(fn=cmd_verify)

    sub.add_parser("selftest", help="check the css splitter").set_defaults(fn=cmd_selftest)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
