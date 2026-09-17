# -*- coding: utf-8 -*-
"""Build the Remi math explainer as EN / KO / bilingual PDFs via Chrome headless."""
import io, os, subprocess, sys
from pypdf import PdfReader, PdfWriter

OUT = sys.argv[1]
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

CSS = """
@page { size: A4; margin: 18mm 16mm 18mm 16mm; }
body { font-family: "Segoe UI", "Malgun Gothic", "Noto Sans KR", sans-serif; font-size: 10.5pt; line-height: 1.55; color: #1f1f1f; margin: 0; }
h1 { font-size: 20pt; font-weight: 600; margin: 0 0 4pt; }
.sub { color: #5f5e5a; font-size: 10pt; margin-bottom: 14pt; }
h2 { font-size: 13.5pt; font-weight: 600; margin: 16pt 0 6pt; border-bottom: 0.5pt solid #d3d1c7; padding-bottom: 3pt; page-break-after: avoid; }
h3 { font-size: 11.5pt; font-weight: 600; margin: 10pt 0 4pt; page-break-after: avoid; }
p { margin: 4pt 0 6pt; }
.step { border: 0.5pt solid #d3d1c7; border-radius: 6pt; padding: 8pt 12pt; margin: 6pt 0 10pt; background: #fafaf8; }
.eq { font-family: Consolas, "Cascadia Mono", "D2Coding", monospace; font-size: 9.2pt; background: #ffffff; border: 0.5pt solid #d3d1c7; border-radius: 4pt; padding: 7pt 9pt; margin: 6pt 0; white-space: pre; line-height: 1.45; page-break-inside: avoid; }
table { border-collapse: collapse; font-size: 9.5pt; margin: 6pt 0; page-break-inside: avoid; }
.grid { page-break-inside: avoid; }
th, td { border: 0.5pt solid #d3d1c7; padding: 3pt 8pt; text-align: center; }
th { background: #f1efe8; font-weight: 600; color: #444441; }
td.h { background: #f1efe8; font-weight: 600; text-align: left; color: #444441; }
.note { font-size: 9.5pt; color: #5f5e5a; }
.tag { display: inline-block; font-size: 8.5pt; padding: 0 6pt; border-radius: 8pt; border: 0.5pt solid #b4b2a9; color: #5f5e5a; margin-right: 4pt; }
.neg { color: #a32d2d; } .pos { color: #3b6d11; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8pt; }
code { font-family: Consolas, "Cascadia Mono", monospace; font-size: 9.2pt; background: #f1efe8; padding: 0 3pt; border-radius: 3pt; }
.fig { page-break-inside: avoid; margin: 8pt 0; }
.t { font-family: "Segoe UI", "Malgun Gothic", sans-serif; font-size: 12px; fill: #1f1f1f; }
.th { font-family: "Segoe UI", "Malgun Gothic", sans-serif; font-size: 12.5px; font-weight: 600; }
.ts { font-family: "Segoe UI", "Malgun Gothic", sans-serif; font-size: 10.5px; }
.arr { stroke: #888780; stroke-width: 1; fill: none; }
"""

# ---------------------------------------------------------------- diagram (light colours only)
def box(x, y, w, h, fill, stroke, t1, t2, title_col, sub_col, dashed=False, t3=None):
    dash = ' stroke-dasharray="4 3"' if dashed else ''
    cx = x + w / 2
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}" stroke="{stroke}" stroke-width="0.7"{dash}/>'
    s += f'<text class="th" x="{cx}" y="{y+24}" text-anchor="middle" fill="{title_col}">{t1}</text>'
    s += f'<text class="ts" x="{cx}" y="{y+42}" text-anchor="middle" fill="{sub_col}">{t2}</text>'
    if t3:
        s += f'<text class="ts" x="{cx}" y="{y+57}" text-anchor="middle" fill="{sub_col}">{t3}</text>'
    return s

PUR = ("#EEEDFE", "#534AB7", "#3C3489", "#534AB7")
TEA = ("#E1F5EE", "#0F6E56", "#085041", "#0F6E56")
COR = ("#FAECE7", "#993C1D", "#712B13", "#993C1D")
GRY = ("#F1EFE8", "#5F5E5A", "#444441", "#5F5E5A")

def diagram(L):
    a = []
    a.append('<svg width="100%" viewBox="0 0 680 560" xmlns="http://www.w3.org/2000/svg">')
    a.append('<defs><marker id="ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M2 1L8 5L2 9" fill="none" stroke="#888780" stroke-width="1.5" stroke-linecap="round"/></marker></defs>')
    def B(x, y, w, h, c, t1, t2, dashed=False, t3=None):
        a.append(box(x, y, w, h, c[0], c[1], t1, t2, c[2], c[3], dashed, t3))
    def A(x, y1, y2):
        a.append(f'<line class="arr" x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" marker-end="url(#ar)"/>')
    # row labels
    B(20, 40, 100, 60, GRY, L["nodes"], L["idonly"]);   B(20, 150, 100, 70, GRY, L["vectors"], L["inL"])
    B(20, 270, 100, 70, GRY, L["matrices"], L["stacked"]); B(20, 390, 100, 80, GRY, L["model"], L["three"])
    xs = [130, 234, 338, 442, 546]; cs = [177, 281, 385, 489, 593]
    for x, t1, t2 in zip(xs, ["FT", "ING", "P", "IN", "DC"], [L["role"], L["ingredient"], L["parameter"], L["interaction"], L["idiom"]]):
        B(x, 40, 94, 60, PUR, t1, t2)
    for c in cs: A(c, 100, 150)
    for x, t1, t2 in zip(xs, ["v(FT)", "v(ING)", "v(P)", "M[from,to]", "v(DC)"], [L["shared"], "Σ w·v(FT) + own", "P.axes", L["onescalar"], L["idiomL"]]):
        B(x, 150, 94, 70, TEA, t1, t2)
    for c in cs[1:4]: A(c, 220, 270)
    B(130, 270, 94, 70, GRY, L["tuple"], "[SC, APP, ST]", dashed=True)
    B(234, 270, 94, 70, COR, "Γ", "ING × L"); B(338, 270, 94, 70, COR, "Π", "P × L"); B(442, 270, 94, 70, COR, "M", "L × L")
    a.append('<line class="arr" x1="224" y1="305" x2="234" y2="305" marker-end="url(#ar)"/>')
    for c in cs[1:4]: A(c, 340, 390)
    B(130, 390, 94, 80, GRY, L["scope"], L["scope2"], dashed=True, t3=L["scope3"])
    B(234, 390, 94, 80, GRY, "Δs = xᵀΓ", L["predict"], t3=L["d1"])
    B(338, 390, 94, 80, GRY, "m = Π s", L["measure"], t3=L["e1"])
    B(442, 390, 94, 80, GRY, "s′ = s + Ms", L["interact"], t3=L["r3"])
    B(546, 390, 94, 80, GRY, L["product"], L["origin"], dashed=True, t3=L["target"])
    a.append(f'<rect x="20" y="500" width="620" height="40" rx="4" fill="#F1EFE8" stroke="#5F5E5A" stroke-width="0.7"/>')
    a.append(f'<text class="ts" x="330" y="517" text-anchor="middle" fill="#444441">{L["legend1"]}</text>')
    a.append(f'<text class="ts" x="330" y="532" text-anchor="middle" fill="#444441">{L["legend2"]}</text>')
    a.append('</svg>')
    return "\n".join(a)

# ---------------------------------------------------------------- content
EN = dict(
    title="How Remi's terms relate mathematically",
    sub="A walkthrough with a three-axis toy example · S1 ONTOLOGY · 2026-09-16",
    nodes="Nodes", idonly="id only", vectors="Vectors", inL="in L-space R²¹⁶", matrices="Matrices", stacked="vectors stacked",
    model="Model", three="three products", role="role", ingredient="ingredient", parameter="parameter", interaction="interaction",
    idiom="idiom", shared="shared effects", onescalar="one scalar", idiomL="idiom over L", tuple="tuple t",
    scope="scope σ", scope2="turns Γ entries", scope3="on or off (B5)", predict="predict", d1="stage D1", measure="measure",
    e1="stage E1", interact="interact", r3="R-3 shift", product="product", origin="origin o = 0", target="target g",
    legend1="x = recipe (dose per ING) · s = ±3 scores over L · m = lab readings · Δs = predicted score shift",
    legend2="purple = node · teal = vector or scalar · coral = matrix · dashed = selector, not a number",
)
KO = dict(
    title="Remi 용어의 수학적 관계",
    sub="세 축 예제로 따라가는 설명 · S1 ONTOLOGY · 2026-09-16",
    nodes="노드", idonly="id 만", vectors="벡터", inL="L-공간 R²¹⁶", matrices="행렬", stacked="벡터를 쌓음",
    model="모형", three="곱셈 셋", role="역할", ingredient="재료", parameter="측정 지표", interaction="상호작용",
    idiom="관용어", shared="공유 효과", onescalar="스칼라 하나", idiomL="L 위의 관용어", tuple="튜플 t",
    scope="스코프 σ", scope2="Γ 성분을", scope3="켜고 끈다 (B5)", predict="예측", d1="D1 단계", measure="측정",
    e1="E1 단계", interact="상호작용", r3="R-3 이동", product="제품", origin="원점 o = 0", target="목표 g",
    legend1="x = 배합 (재료별 투입량) · s = L 위의 ±3 점수 · m = 실험실 측정값 · Δs = 예측된 점수 이동",
    legend2="보라 = 노드 · 청록 = 벡터·스칼라 · 산호 = 행렬 · 점선 = 숫자가 아닌 선택자",
)

def body_en(D):
    return f"""
<h1>{EN['title']}</h1><div class="sub">{EN['sub']}</div>

<h2>0. The one idea everything rests on</h2>
<div class="step">
<p><b>Every sensory word is a coordinate axis.</b> Remi has 216 lexicon words, so a product's sensory state is a point in a 216-dimensional space. To keep the example readable we use <b>three axes</b>:</p>
<div class="eq">L-space (toy)   axis 1 = L.ta.sweet     axis 2 = L.tx.thickness     axis 3 = L.ta.sour

a score vector   s = ( s_sweet , s_thick , s_sour )        each entry is a ±3 panel score
the origin       o = ( 0 , 0 , 0 )                          = the benchmark: "same as reference"</div>
<p class="note">That is why the field is called <code>axis</code>: an <code>L</code> id names one coordinate.</p>
</div>

<h2>1. Node → vector: what one ingredient "is" to the model</h2>
<div class="step">
<p>An ingredient node has an id and nothing else. What the model uses is its <b>vector</b>: one number per axis, "how far a typical dose moves the score". In YAML we store only the non-zero entries, each as a <b>component</b> record:</p>
<div class="grid">
<div class="eq">ING.xanthan_gum
  effects:
  - {{axis: L.tx.thickness, direction: increase,
     magnitude: strong}}          # +1.0
  - {{axis: L.ta.sweet,     direction: decrease,
     magnitude: weak}}            # −0.3  (gum masks sweetness)</div>
<div class="eq">the same thing as a vector

v(xanthan) = ( −0.3 , +1.0 , 0 )
               sweet   thick   sour

words → numbers (loader):
weak 0.3 · medium 0.6 · strong 1.0
decrease → minus sign</div>
</div>
<p class="note"><span class="tag">component</span> one entry, e.g. "+1.0 on thickness" — the record carries its axis, sign, size, scope, confidence. <span class="tag">vector</span> the whole list = the ingredient's row of numbers. A zero is simply an axis that is not listed.</p>
</div>

<h2>2. Roles: where most of an ingredient's vector comes from</h2>
<div class="step">
<p>Ingredients rarely list all their effects themselves. They inherit the vector of each <b>role</b> (<code>FT</code>) they belong to, scaled by the role weight, and then override what is special to them:</p>
<div class="eq">v(ING) = Σ over roles  w_role · v(FT_role)   +  overrides

sugar   : roles = [ FT.sweetener (strong) ]
          v(FT.sweetener) = ( +1.0 , +0.3 , 0 )        sweeteners add sweetness and a little body
          v(sugar)        = 1.0 · ( +1.0 , +0.3 , 0 ) = ( +1.0 , +0.3 , 0 )

xanthan : roles = [ FT.thickener (strong) ]
          v(FT.thickener) = ( 0 , +1.0 , 0 )
          override on sweet: −0.3
          v(xanthan)      = ( −0.3 , +1.0 , 0 )</div>
<p class="note">This is the INGREDIENT layer's 2-tier design: shared numbers live on the role, exceptions on the ingredient. Role weights stay words (weak/medium/strong); learned numbers land on the ingredient's own components (rule A10).</p>
</div>

<h2>3. Vectors stacked = the matrix Γ</h2>
<div class="step">
<p>Put one ingredient per row and one axis per column. That table is Γ — the thing the model actually multiplies.</p>
<table><tr><th>Γ</th><th>sweet</th><th>thick</th><th>sour</th></tr>
<tr><td class="h">sugar</td><td class="pos">+1.0</td><td class="pos">+0.3</td><td>0</td></tr>
<tr><td class="h">xanthan</td><td class="neg">−0.3</td><td class="pos">+1.0</td><td>0</td></tr></table>
<p class="note"><span class="tag">matrix</span> is never written in YAML. It is what you get by stacking every ingredient's vector; the loader builds it. Real size: ~118 ingredients × 216 axes.</p>
</div>

<h2>4. The three multiplications</h2>
<div class="step">
<h3>4a. Predict — stage D1: "if I change the recipe, how do the scores move?"</h3>
<p>The recipe change is a vector <code>x</code> with one entry per ingredient, in units of "typical doses added". Add one dose of sugar and half a dose of xanthan:</p>
<div class="eq">x  = ( +1.0 , +0.5 )              (sugar, xanthan)

Δs = xᵀ Γ                          row-vector × matrix

Δs_sweet = 1.0·(+1.0) + 0.5·(−0.3) = +0.85
Δs_thick = 1.0·(+0.3) + 0.5·(+1.0) = +0.80
Δs_sour  = 1.0·( 0 )  + 0.5·( 0 )  =  0

Δs = ( +0.85 , +0.80 , 0 )         "a bit sweeter, noticeably thicker, sourness unchanged"</div>
<p class="note">Each score is a sum down one column: every ingredient's contribution to that axis, weighted by how much of it you added. This is the whole of "build a theoretical recipe" — the optimiser just searches for the <code>x</code> whose Δs is closest to the target.</p>

<h3>4b. Interact — R-3: "perceptions also shift each other"</h3>
<p>Some axes change other axes on their own — sweetness suppresses sourness. Those are the <code>IN</code> scalars, entries of an axis-by-axis matrix M. Our toy has one:</p>
<div class="grid">
<div><table><tr><th>M</th><th>→ sweet</th><th>→ thick</th><th>→ sour</th></tr>
<tr><td class="h">sweet →</td><td>0</td><td>0</td><td class="neg">−0.6</td></tr>
<tr><td class="h">thick →</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td class="h">sour →</td><td>0</td><td>0</td><td>0</td></tr></table></div>
<div class="eq">s′ = s + M s

sour′ = 0 + (−0.6)·(+0.85) = −0.51

s′ = ( +0.85 , +0.80 , −0.51 )
"…and it will taste a little less sour"</div>
</div>
<p class="note"><span class="tag">scalar</span> one <code>IN</code> record = one cell of M. The matrix is almost empty on purpose (rule C4: only well-established causal interactions).</p>

<h3>4c. Measure — stage E1: "what would the lab see, and does it agree?"</h3>
<p>A parameter is a lab reading that stands in for some axes. Its <code>axes</code> list is a vector over L; stacked, they form Π. Viscosity stands in for thickness:</p>
<div class="grid">
<div><table><tr><th>Π</th><th>sweet</th><th>thick</th><th>sour</th></tr>
<tr><td class="h">P.apparent_viscosity</td><td>0</td><td class="pos">+1.0</td><td>0</td></tr>
<tr><td class="h">P.pH</td><td>0</td><td>0</td><td class="neg">−1.0</td></tr></table></div>
<div class="eq">m = Π s

m_viscosity = +0.80   (expected reading, scaled)
m_pH        = +0.51   (less sour → higher pH)

if the lab reads viscosity ≈ +0.8:
  confidence in s_thick goes up   (rule A4)
if it reads something else:
  the xanthan→thick component is corrected (E1)</div>
</div>
<p class="note">The model runs on Δs alone; Π is only used when a reading exists. That is what "P is auxiliary" means in equations.</p>
</div>

<h2>5. The tuple switches components on and off</h2>
<div class="step">
<p>The same ingredient does not behave the same in every product. Each component carries a <b>scope</b>; the profile tuple decides which components are active, so Γ is really Γ(t):</p>
<div class="eq">xanthan → thickness :  {{scope: SC.emulsion.ow|APP.sauce,     magnitude: strong}}   → +1.0
                       {{scope: SC.emulsion.ow|APP.beverage,  magnitude: medium}}   → +0.6

t = [SC.emulsion.ow, APP.sauce,    ST.ambient]  →  Γ_t[xanthan, thick] = +1.0
t = [SC.emulsion.ow, APP.beverage, ST.ambient]  →  Γ_t[xanthan, thick] = +0.6

matching rule (B5): a scope is "on" when every part it writes equals the profile's part;
a blank part matches anything. If two scopes match, the one with more parts written wins (B6).</div>
<p class="note"><span class="tag">tuple</span> the profile <code>[SC, APP, ST]</code> is not a number — it is a selector. It never enters the multiplication; it chooses which numbers do.</p>
</div>

<h2>6. Where the product sits</h2>
<div class="step">
<div class="eq">product = ( t , key ingredients , identity axes I ⊂ L , origin o )

o  = the reference sample; all scores are 0 there
g  = the goal vector the user asked for, e.g. g = ( −1 , +1 , 0 )  "less sweet, thicker"
D1 searches for x such that  Δs(x) ≈ g   subject to ranges and the palette</div>
<p class="note">Two products with the same tuple but different key ingredients have different Γ rows in play and different origins — that is the "same ruler" rule (B9): scores are only comparable when t, key ingredients and o all match.</p>
</div>

<h2>7. The map</h2>
<div class="fig">{D}</div>
<p class="note">Read one column at a time: <code>ING</code> owns <code>v(ING)</code>; those vectors stacked are Γ; Γ is what the model multiplies by the recipe. <code>FT</code> and <code>DC</code> stop at the vector row — a role's vector is only inherited, an idiom's vector is a target direction. Dashed boxes are selectors, not numbers.</p>

<h2>8. Glossary, tied to the example</h2>
<table>
<tr><th>Word</th><th>In the example</th><th>In the files</th></tr>
<tr><td class="h">node</td><td>"sugar", "thickness", "viscosity" — names</td><td>an id line: <code>ING.sucrose</code>, <code>L.tx.thickness</code>, <code>P.apparent_viscosity</code></td></tr>
<tr><td class="h">component</td><td>+1.0 on thickness</td><td>one <code>{{axis, direction, magnitude, …}}</code> record</td></tr>
<tr><td class="h">vector</td><td>v(xanthan) = (−0.3, +1.0, 0)</td><td>the <code>effects</code> list of one ingredient (or <code>axes</code> of one P, one DC)</td></tr>
<tr><td class="h">scalar</td><td>M[sweet, sour] = −0.6</td><td>one <code>IN</code> record</td></tr>
<tr><td class="h">matrix</td><td>Γ, M, Π tables above</td><td>not stored; built by the loader from all vectors</td></tr>
<tr><td class="h">tuple</td><td>[SC.emulsion.ow, APP.sauce, ST.ambient]</td><td>a profile entry; a scope string on a component</td></tr>
<tr><td class="h">sentence</td><td>"gum masks sweetness — measured 2026-08"</td><td>a <code>LESSON</code> (observation) or <code>RP</code> (prescription)</td></tr>
</table>
"""

def body_ko(D):
    return f"""
<h1>{KO['title']}</h1><div class="sub">{KO['sub']}</div>

<h2>0. 모든 것이 서 있는 한 가지 생각</h2>
<div class="step">
<p><b>감각 낱말 하나가 좌표축 하나다.</b> Remi 의 렉시콘 낱말은 216개이므로, 한 제품의 감각 상태는 216차원 공간의 한 점이다. 읽기 쉽게 예제는 <b>축 세 개</b>만 쓴다:</p>
<div class="eq">L-공간 (예제)   축 1 = L.ta.sweet (단맛)   축 2 = L.tx.thickness (걸쭉함)   축 3 = L.ta.sour (신맛)

점수 벡터   s = ( s_sweet , s_thick , s_sour )        각 성분은 패널의 ±3 점수
원점       o = ( 0 , 0 , 0 )                          = 기준 제품: "기준과 같다"</div>
<p class="note">필드 이름이 <code>axis</code> 인 이유가 이것이다: <code>L</code> id 하나가 좌표축 하나를 가리킨다.</p>
</div>

<h2>1. 노드 → 벡터: 모형에게 재료 하나는 무엇인가</h2>
<div class="step">
<p>재료 노드는 id 만 가진다. 모형이 쓰는 것은 그 재료의 <b>벡터</b>다: 축마다 숫자 하나, "통상량을 넣으면 점수가 얼마나 움직이나". YAML 에는 0 이 아닌 성분만 <b>성분(component)</b> 레코드로 적는다:</p>
<div class="grid">
<div class="eq">ING.xanthan_gum
  effects:
  - {{axis: L.tx.thickness, direction: increase,
     magnitude: strong}}          # +1.0
  - {{axis: L.ta.sweet,     direction: decrease,
     magnitude: weak}}            # −0.3  (검이 단맛을 가린다)</div>
<div class="eq">같은 것을 벡터로 쓰면

v(잔탄) = ( −0.3 , +1.0 , 0 )
            단맛   걸쭉함  신맛

낱말 → 숫자 (로더):
weak 0.3 · medium 0.6 · strong 1.0
decrease → 음의 부호</div>
</div>
<p class="note"><span class="tag">성분</span> 항목 하나, 예: "걸쭉함에 +1.0" — 레코드는 축·부호·크기·스코프·확신도를 함께 든다. <span class="tag">벡터</span> 목록 전체 = 그 재료의 숫자 한 줄. 0 은 적히지 않은 축일 뿐이다.</p>
</div>

<h2>2. 역할: 재료 벡터의 대부분이 오는 곳</h2>
<div class="step">
<p>재료가 효과를 전부 스스로 적는 일은 드물다. 속한 <b>역할</b>(<code>FT</code>)의 벡터를 역할 무게만큼 물려받고, 자기만 다른 것을 덮어쓴다:</p>
<div class="eq">v(ING) = Σ 역할마다  w_역할 · v(FT_역할)   +  overrides

설탕   : 역할 = [ FT.sweetener (strong) ]
         v(FT.sweetener) = ( +1.0 , +0.3 , 0 )        감미료는 단맛과 약간의 바디를 더한다
         v(설탕)          = 1.0 · ( +1.0 , +0.3 , 0 ) = ( +1.0 , +0.3 , 0 )

잔탄   : 역할 = [ FT.thickener (strong) ]
         v(FT.thickener) = ( 0 , +1.0 , 0 )
         단맛 override: −0.3
         v(잔탄)          = ( −0.3 , +1.0 , 0 )</div>
<p class="note">INGREDIENT 층의 2단 설계가 이것이다: 공통 숫자는 역할에, 예외는 재료에. 역할 무게는 낱말(weak/medium/strong)로 두고, 학습된 숫자는 재료 자신의 성분에 쌓인다(규칙 A10).</p>
</div>

<h2>3. 벡터를 쌓으면 = 행렬 Γ</h2>
<div class="step">
<p>한 행에 재료 하나, 한 열에 축 하나. 그 표가 Γ — 모형이 실제로 곱하는 것이다.</p>
<table><tr><th>Γ</th><th>단맛</th><th>걸쭉함</th><th>신맛</th></tr>
<tr><td class="h">설탕</td><td class="pos">+1.0</td><td class="pos">+0.3</td><td>0</td></tr>
<tr><td class="h">잔탄</td><td class="neg">−0.3</td><td class="pos">+1.0</td><td>0</td></tr></table>
<p class="note"><span class="tag">행렬</span>은 YAML 에 적히지 않는다. 모든 재료의 벡터를 쌓으면 나오는 것이고, 로더가 만든다. 실제 크기: 재료 약 118 × 축 216.</p>
</div>

<h2>4. 곱셈 셋</h2>
<div class="step">
<h3>4a. 예측 — D1 단계: "배합을 바꾸면 점수가 어떻게 움직이나?"</h3>
<p>배합 변화는 재료마다 성분 하나인 벡터 <code>x</code> 이고 단위는 "통상량 몇 배를 더 넣었나". 설탕 한 배, 잔탄 반 배를 더 넣으면:</p>
<div class="eq">x  = ( +1.0 , +0.5 )              (설탕, 잔탄)

Δs = xᵀ Γ                          행벡터 × 행렬

Δs_단맛   = 1.0·(+1.0) + 0.5·(−0.3) = +0.85
Δs_걸쭉함 = 1.0·(+0.3) + 0.5·(+1.0) = +0.80
Δs_신맛   = 1.0·( 0 )  + 0.5·( 0 )  =  0

Δs = ( +0.85 , +0.80 , 0 )         "조금 더 달고, 뚜렷이 더 걸쭉하고, 신맛은 그대로"</div>
<p class="note">점수 하나는 열 하나를 세로로 더한 것이다: 그 축에 대한 모든 재료의 기여를 넣은 양만큼 가중해 더한다. "이론 배합을 만든다" 는 것이 이것의 전부다 — 최적화기는 Δs 가 목표에 가장 가까운 <code>x</code> 를 찾을 뿐이다.</p>

<h3>4b. 상호작용 — R-3: "느낌은 서로도 움직인다"</h3>
<p>어떤 축은 다른 축을 스스로 바꾼다 — 단맛은 신맛을 누른다. 그것이 <code>IN</code> 스칼라이고, 축×축 행렬 M 의 칸이다. 예제에는 하나만 있다:</p>
<div class="grid">
<div><table><tr><th>M</th><th>→ 단맛</th><th>→ 걸쭉함</th><th>→ 신맛</th></tr>
<tr><td class="h">단맛 →</td><td>0</td><td>0</td><td class="neg">−0.6</td></tr>
<tr><td class="h">걸쭉함 →</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td class="h">신맛 →</td><td>0</td><td>0</td><td>0</td></tr></table></div>
<div class="eq">s′ = s + M s

신맛′ = 0 + (−0.6)·(+0.85) = −0.51

s′ = ( +0.85 , +0.80 , −0.51 )
"…그리고 조금 덜 시게 느껴진다"</div>
</div>
<p class="note"><span class="tag">스칼라</span> <code>IN</code> 레코드 하나 = M 의 칸 하나. 이 행렬은 일부러 거의 비어 있다(규칙 C4: 확립된 인과 상호작용만).</p>

<h3>4c. 측정 — E1 단계: "실험실은 무엇을 보고, 그것이 맞나?"</h3>
<p>측정 지표는 어떤 축들을 대신하는 실험실 측정값이다. 그 <code>axes</code> 목록이 L 위의 벡터이고, 쌓으면 Π 가 된다. 점도는 걸쭉함을 대신한다:</p>
<div class="grid">
<div><table><tr><th>Π</th><th>단맛</th><th>걸쭉함</th><th>신맛</th></tr>
<tr><td class="h">P.apparent_viscosity</td><td>0</td><td class="pos">+1.0</td><td>0</td></tr>
<tr><td class="h">P.pH</td><td>0</td><td>0</td><td class="neg">−1.0</td></tr></table></div>
<div class="eq">m = Π s

m_점도 = +0.80   (기대 측정값, 척도 맞춤)
m_pH   = +0.51   (덜 시다 → pH 높다)

실험실 점도가 ≈ +0.8 이면:
  s_걸쭉함 의 확신도가 오른다   (규칙 A4)
다른 값이 나오면:
  잔탄→걸쭉함 성분을 고친다 (E1)</div>
</div>
<p class="note">모형은 Δs 만으로 돈다; Π 는 측정값이 있을 때만 쓴다. "P 는 보조" 라는 말을 식으로 쓰면 이것이다.</p>
</div>

<h2>5. 튜플이 성분을 켜고 끈다</h2>
<div class="step">
<p>같은 재료가 모든 제품에서 같게 행동하지는 않는다. 성분마다 <b>스코프</b>가 있고, 제형 튜플이 어느 성분이 켜지는지 정한다. 그래서 Γ 는 사실 Γ(t) 다:</p>
<div class="eq">잔탄 → 걸쭉함 :  {{scope: SC.emulsion.ow|APP.sauce,     magnitude: strong}}   → +1.0
                  {{scope: SC.emulsion.ow|APP.beverage,  magnitude: medium}}   → +0.6

t = [SC.emulsion.ow, APP.sauce,    ST.ambient]  →  Γ_t[잔탄, 걸쭉함] = +1.0
t = [SC.emulsion.ow, APP.beverage, ST.ambient]  →  Γ_t[잔탄, 걸쭉함] = +0.6

맞춤 규칙 (B5): 스코프에 적힌 칸마다 제형의 그 칸과 같으면 "켜짐";
비운 칸은 무엇이든 맞는다. 둘이 맞으면 더 많은 칸을 적은 쪽이 이긴다 (B6).</div>
<p class="note"><span class="tag">튜플</span> 제형 <code>[SC, APP, ST]</code> 은 숫자가 아니라 선택자다. 곱셈에 들어가지 않고, 어느 숫자가 들어갈지를 고른다.</p>
</div>

<h2>6. 제품은 어디 있나</h2>
<div class="step">
<div class="eq">제품 = ( t , 핵심 재료 , 정체성 축 I ⊂ L , 원점 o )

o  = 기준 시료; 거기서 모든 점수는 0
g  = 사용자가 원한 목표 벡터, 예: g = ( −1 , +1 , 0 )  "덜 달게, 더 걸쭉하게"
D1 은 범위와 팔레트 안에서  Δs(x) ≈ g  인 x 를 찾는다</div>
<p class="note">튜플은 같고 핵심 재료가 다른 두 제품은 쓰이는 Γ 행이 다르고 원점도 다르다 — "같은 자" 규칙(B9)이 이것이다: t · 핵심 재료 · o 가 모두 같을 때만 점수를 비교할 수 있다.</p>
</div>

<h2>7. 지도</h2>
<div class="fig">{D}</div>
<p class="note">한 번에 한 열씩 읽는다: <code>ING</code> 는 <code>v(ING)</code> 를 가지고, 그 벡터들을 쌓으면 Γ, Γ 는 모형이 배합과 곱하는 것이다. <code>FT</code> 와 <code>DC</code> 는 벡터 줄에서 멈춘다 — 역할의 벡터는 물려줄 뿐이고, 관용어의 벡터는 목표 방향이다. 점선 상자는 숫자가 아니라 선택자다.</p>

<h2>8. 용어 — 예제와 붙여서</h2>
<table>
<tr><th>낱말</th><th>예제에서</th><th>파일에서</th></tr>
<tr><td class="h">노드 (node)</td><td>"설탕", "걸쭉함", "점도" — 이름</td><td>id 한 줄: <code>ING.sucrose</code>, <code>L.tx.thickness</code>, <code>P.apparent_viscosity</code></td></tr>
<tr><td class="h">성분 (component)</td><td>걸쭉함에 +1.0</td><td><code>{{axis, direction, magnitude, …}}</code> 레코드 하나</td></tr>
<tr><td class="h">벡터 (vector)</td><td>v(잔탄) = (−0.3, +1.0, 0)</td><td>재료 하나의 <code>effects</code> 목록 (또는 P 하나의 <code>axes</code>, DC 하나)</td></tr>
<tr><td class="h">스칼라 (scalar)</td><td>M[단맛, 신맛] = −0.6</td><td><code>IN</code> 레코드 하나</td></tr>
<tr><td class="h">행렬 (matrix)</td><td>위의 Γ, M, Π 표</td><td>저장하지 않는다; 로더가 모든 벡터에서 만든다</td></tr>
<tr><td class="h">튜플 (tuple)</td><td>[SC.emulsion.ow, APP.sauce, ST.ambient]</td><td>제형 항목 하나; 성분에 붙는 스코프 문자열</td></tr>
<tr><td class="h">문장 (sentence)</td><td>"검이 단맛을 가린다 — 2026-08 관찰"</td><td><code>LESSON</code>(관찰) 또는 <code>RP</code>(처방)</td></tr>
</table>
"""

def html(lang_body, L, lang):
    return f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><title>{L["title"]}</title><style>{CSS}</style></head><body>{lang_body(diagram(L))}</body></html>'

def to_pdf(html_path, pdf_path):
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf_path}", "file:///" + html_path.replace("\\", "/")],
                   check=True, capture_output=True)

os.makedirs(OUT, exist_ok=True)
paths = {}
for lang, body, L in (("en", body_en, EN), ("ko", body_ko, KO)):
    hp = os.path.join(OUT, f"remi_math_explainer_{lang}.html")
    pp = os.path.join(OUT, f"remi_math_explainer_{lang}.pdf")
    io.open(hp, "w", encoding="utf-8").write(html(body, L, lang))
    to_pdf(hp, pp); paths[lang] = pp
    print(lang, "pages:", len(PdfReader(pp).pages))
w = PdfWriter()
for lang in ("en", "ko"):
    for p in PdfReader(paths[lang]).pages: w.add_page(p)
w.add_metadata({"/Title": "Remi — how the terms relate mathematically (EN + KO)", "/Author": "Remi S1 ONTOLOGY"})
bp = os.path.join(OUT, "remi_math_explainer_en_ko.pdf")
with open(bp, "wb") as f: w.write(f)
print("bilingual pages:", len(PdfReader(bp).pages))
