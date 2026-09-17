# Remi Rulebook — one set of rules every session reads

2026-09-17 (S1), revision 5 — reviewed by the user; every rule is **fixed** except E5 (draft) and the two deferred items (B4 sub-levels, C8). English edition; **this file is the reference**. The Korean `RULES.md` is generated from it.

How to read: rules are numbered and the numbers never change (a dropped rule stays listed as
*retired*). Chapters `01`–`06` explain *why*; this file states *what*. A session that reads only this
file must be able to read and write the ontology correctly. Any name or record shape not in this file
is not allowed — add it here first.

Status: **fixed** = decided by the user · **draft** = proposed by S1, awaiting review · **deferred** =
discussion postponed (the *Deferred* section says where) · **retired** = dropped, number kept.

---

## 0. Mathematical vocabulary

The ontology is a graph, and the model reads it as matrices. Every record in this rulebook is one of the
objects below, and each word is used in exactly this sense everywhere in the file.

| Word | Meaning in Remi | What it applies to |
|---|---|---|
| **node** | a named thing; a vertex of the graph. It has an id and describes nothing but itself | `L` `P` `SC` `APP` `ST` `ING` `FT` |
| **tuple** | one value taken from each of several fixed lists, in a fixed order | a profile `[SC, APP, ST]`; a scope, which is a tuple with blanks |
| **component** | one entry `{axis, direction, magnitude, …}`: how much one thing moves one `L` | an ingredient edge; one entry of `P.axes`; one entry of a `DC`; one entry of `LESSON.observed` |
| **vector** | one record's list of components over the `L` axes | an `ING`'s effects; a `P`'s `axes`; one `DC`; one `LESSON.observed`; one `RP.compensate` |
| **scalar** | one signed magnitude between two `L` | one `IN` record |
| **matrix** | vectors stacked into a table | all ingredient effects = ING × L (this is Γ₀ in the model); all `IN` = L × L; all `P.axes` = P × L |
| **sentence** | a record meant for people and the API, with a structured half and a prose half | `LESSON` `RP` |

Two further words are not mathematical but recur: **scope** = a tuple with blanks that says *where a
component is true* (B5); **card** = the view of one axis in one product, assembled from stored pieces (D1).

---

## A. Vocabulary

### A0. Namespaces at a glance

| Prefix | Full name | Object | What one record is | Example | Owner | File |
|---|---|---|---|---|---|---|
| `L` | **Lexicon** | node | one word for something a person perceives — taste, aroma, texture, appearance, chemesthesis | `L.tx.creaminess` | S1 | `layerL_lexicon.yaml` |
| `P` | **Parameter** | node + vector | a lab-measurable indicator that stands in for one or more `L` — name, unit, method, and `axes` (its vector over `L`) | `P.apparent_viscosity` | S1 | `layerA_parameters.yaml` |
| `SC` | **Structure Class** | node | the physical arrangement of the product — what is dispersed in what | `SC.emulsion.ow` | S1 | `structure_taxonomy.yaml` (new) |
| `APP` | **Application** | node | the use context — how the finished product is used or served | `APP.beverage` | S1 | `structure_taxonomy.yaml` |
| `ST` | **State** | node | the temperature state in which the product is stored and consumed | `ST.frozen` | S1 | `structure_taxonomy.yaml` |
| `ING` | **Ingredient** | node + vector | one ingredient, with its roles and its effects (a vector over `L`) | `ING.xanthan_gum` | S2 | `layerC2_*.yaml` |
| `FT` | **Function Tag** | node + vector | a role — the set of ingredients that do the same job — with the effects they share | `FT.thickener` | S2 | `layerC2_*.yaml` |
| `IN` | **Interaction** | scalar | one `L` changes another `L` | `IN.0001` | S1 | `layerR_seed.yaml` |
| `DC` | **Decomposition** | vector | an idiom expressed over `L` ("depth of flavor" = [+umami, +kokumi, …]) | `DC.0001` | S1 (content: S4) | `layerR_seed.yaml` |
| `KN` | **Kinetics** | — | how a `P` or `L` changes over time (shelf life) | `KN.0001` | S1 | `layerR_seed.yaml` — deferred |
| `LESSON` | **Lesson** | sentence | an observation: what was seen, in which profile, about which ingredient — structured *and* in prose | `LESSON.sugar_triple_role` | S1 | `layerS2_profiles.yaml` |
| `RP` | **Reformulation Pattern** | sentence | a prescription: reduce X, keep Y, compensate with Z — cites `LESSON`s as evidence | `RP.low_sugar_ice_cream` | S2 | `layerC2_ext_reformulation.yaml` |

Ingredient edges (the components of an `ING`'s or `FT`'s vector) have no prefix; they live inside the
`ING`/`FT` record.

Retired prefixes: `PO` (folded into `P.axes`), `SA` (v1 name for `L`), `IX` (v1 name for `IN`).

### A1–A11. Rules

| # | Rule | Status |
|---|---|---|
| A1 | The ten namespaces above are the only ones. `PO`, `SA`, `IX` are retired and must not appear in new records. | fixed |   
| A2 | An id is `PREFIX.lower_snake_case`. Words are joined by `_`, levels by `.`. `IN` `DC` `KN` `LESSON` `RP` are numbered `PREFIX.NNNN`; nodes are named. No Korean in ids. | fixed |
| A3 | `L` covers everything a person perceives. The second segment is the modality: `ta` taste · `tx` texture · `ap` appearance · `ar` aroma · `ch` chemesthesis. Texture words (thickness, creaminess) are `L`, not `P`. | fixed |
| A4 | `P` is a lab-measurable stand-in for some `L`. A `P` record carries name, unit, method and `axes` (its vector over `L`). The system runs without any measured `P`; a measured `P` raises confidence. A product is never described by `P` alone. | fixed |
| A5 | `FT` is a role, not a class tree. The only hierarchy is `specializes`, one level (`FT.milk_protein specializes FT.protein`). | fixed |
| A6 | An `ING` lists its roles with a weight: `functions: [{function: FT.*, weight}]`. Weight is one of three words (A9). | fixed |
| A7 | A field that points to another node is named after what it points to: `axis` → `L`, `parameter` → `P`, `ingredient` → `ING`, `function` → `FT`. `from`/`to` are used only in `IN`, where direction matters. **Such a field holds the target's id, never its label** (`derived_from: sauce`, not `derived_from: Oil-in-water emulsion sauce`). | fixed |
| A8 | **The ontology is written in English.** Every node carries `label` (a short English name) and, where the name alone is ambiguous, `definition` (one English sentence). No other natural-language field is stored on ontology records — no `ko`, no localized anchors or notes. Localized text is S4's: a translation table per locale, keyed by id (`lexicon_map_<locale>`), produced from the English `label`/`definition`. User sentences are data, not vocabulary: they are recorded verbatim in the product card (`intake`, `unresolved`) and mapped to ids by S4. | fixed |
| A9 | Controlled vocabulary — `direction {increase, decrease}` · `magnitude` and `weight {weak, medium, strong}` · `confidence {draft, low, medium, high}` · `functional_form {linear, threshold, saturating, non_monotonic}` · `tier {core, monitored}` · `goal {maintain, increase, decrease, minimize, maximize, target}` · `method benchmark_difference` · `scale_type diff_7` · `evidence_required {sample, sample_aged}` · `source {kind: literature\|expert\|prior\|measured\|user, date}`. | fixed |
| A10 | `magnitude` is one of the three words **or a number**. Words map to numbers in the loader (weak 0.3 · medium 0.6 · strong 1.0). Numbers appear **only on ingredient edges**, written back by learning (E1). Role weights (A6) stay words. | fixed |
| A11 | **Every component of a vector over `L` has one shape**: `{axis, direction, magnitude, scope?, functional_form?, confidence, source}` — ingredient effects, `P.axes`, `DC`, `LESSON.observed`. (`RP.compensate` is a vector over `ING`, not `L`, and is shaped by C7.) Cost: none — optional fields stay optional. Benefit: one parser and one validator serve all four, and C6/C9 can compare a lesson with an edge field by field. | fixed |

---

## B. Profiles and products

### B0. Terms`

| Term | Meaning |
|---|---|
| **structure** (`SC`) | what is dispersed in what. Physics decides it. |
| **application** (`APP`) | the *use context*: how the finished product is used or served — drunk (beverage), poured over or tossed with food (sauce, dressing), dipped into (dip), added in small amounts as seasoning (condiment), eaten as a dessert (dessert). It comes from the noun the user says. |
| **state** (`ST`) | the temperature at which the product is stored and consumed: `frozen` · `chilled` · `ambient` · `hot`. |
| **profile** | one tuple `[SC, APP, ST]`, **all three written**. A profile owns parameter ranges, an axis list, and a filler. In Korean: 제형. |
| **scope** | a tuple with the same three parts where parts may be left blank; it says *where a component is true* (B5). |
| **product** | a user's project: a profile **plus** key ingredients, identity axes and an origin (benchmark). In Korean: 제품. Lives in `projects/<id>/`. |
| **short key** | a file-safe alias for a profile, generated by rule (B8). |

### B1–B15. Rules

| # | Rule | Status |
|---|---|---|
| B1 | A profile is one tuple `[SC, APP, ST]`. Its canonical name is the scope string of that tuple, e.g. `SC.emulsion.ow\|APP.beverage\|ST.ambient`. | fixed |
| B2 | `APP` never encodes an ingredient, a brand or a product. Test for a new `APP` node: it must answer *"how is the product used?"* — never *"what is it made of?"* (`APP.beverage.milk` ✗: milk is an ingredient, not a way of using). | fixed |
| B3 | `SC` names structure only. Application and state are never appended with dots (`SC.emulsion.ow.beverage` ✗ — that is a scope, written per C1). | fixed |
| B4 | `SC`, `APP`, `ST` are three lists of allowed values. Today no list has sub-levels. `SC`: `emulsion.ow` `suspension`. `APP`: `beverage` `sauce` `dressing` `dip` `condiment` `dessert`. `ST`: `frozen` `chilled` `ambient` `hot`. Adding a value to `SC` or `APP`, or placing one value under another (is dressing a kind of sauce?), is decided case by case → *Deferred #1*. | fixed (lists) · deferred (new values, sub-levels) |
| B5 | **Matching.** A profile has **no blank part** — all three of `[SC, APP, ST]` are written. A scope writes some parts and leaves the others blank. A scope **matches** a profile when every part *written* in the scope equals the same part of the profile; a blank part matches any value; `any` is the scope with all parts blank. (Examples below.) | fixed |
| B5-1 | **Fallback by characteristics.** When a profile has *no* matching component for an axis (the name does not match but the physics does — e.g. a dip behaves like a sauce), the loader may borrow the component from the **nearest profile**: the one with the same `SC` whose defining parameter ranges (the profile's `discriminators`) overlap most with this profile's ranges. A borrowed component is used at confidence one step lower, and the scope index (C9) lists every borrow. Borrowing never overrides an exact match. | fixed |
| B6 | The set of scopes a profile accepts is **computed** from B5, never listed by hand. When the same component exists under several matching scopes, the one with more parts written wins. (Known exposure: a scope written too broadly applies silently; see chapter 02.) | fixed |
| B7 | The three lists and the dotted-alias table live in one file, `structure_taxonomy.yaml`. The profiles file holds only tuples. | fixed |
| B8 | **Short key**, generated: (1) the last segment of `APP`; (2) if there is no `APP`, the last segment of `SC`; (3) if `ST` is not `ambient`, append `_<ST>`; (4) if the same `APP` exists under two `SC`, prefix `<SC last segment>_`. Keys are aliases, never canonical. Because every profile now writes `ST`, rule (3) is what keeps keys short: `ST.ambient` is the default and is *not* appended, so `[SC.emulsion.ow, APP.beverage, ST.ambient]` → `beverage`, while `[…, ST.frozen]` → `dessert_frozen`. Today: `beverage` `sauce` `dressing` `dip` `suspension` `condiment` `dessert_frozen` (two renames: `sauce_ow→sauce`, `icecream→dessert_frozen`, at migration). | fixed |
| B9 | A product is defined by **four profiles**: structure (the profile tuple), ingredients (key ingredients), sensory (2–3 identity axes with goals), origin (benchmark). The structure profile is only one of the four. | fixed |
| B10 | One product, one card: `projects/<id>/product_card.yaml`. The product refers to its profile by short key (`profile: beverage`). | fixed |
| B11 | Identity axes belong to the product, not the profile: `identity: [{axis: L.*, …}]`, two or three of them. | fixed |
| B12 | User-private labels (project name, customer, internal code) live only under `private:` in the product card. They never enter the ontology, learning, prompts, or other users' data. | fixed |
| B13 | A derived profile names its parent by short key (`derived_from: sauce`) and is born with `confidence: draft`. After review it carries `status: reviewed <date>`. | fixed |
| B14 | **Which `SC`.** When a product contains several dispersed phases (fat droplets *and* protein particles, ice *and* air), the `SC` is the phase that governs texture. Drinkable yogurt is `SC.suspension` (casein aggregates), not `SC.emulsion.ow`, although it contains fat droplets. Test: *remove the phase — does the texture class change?* **One `SC` per profile, no weights**: the tuple is a selector, and a weighted pair would turn Γ(t) into a blend of two profiles' components, break short keys and blur the scope invariants. The secondary phase is expressed through the profile's parameters instead (e.g. a small `P.oil_phase_fraction` range on a drinkable-yogurt profile), so fat-related components scoped `any` still apply via `P.axes`. Parent values such as `SC.dispersion` (true of both emulsions and suspensions) are hierarchy → *Deferred #1*. | fixed |  
| B15 | **Three storage levels.** *Shared ontology* — priors; applied to every project; **classified**, never shown to users. *User-private layer* — this user's learned edge values, `private` labels, card snapshots; readable by this user only. *Product folder* — the four profiles, scores, recipes; this user only. A new product that shares profile and key ingredients with an earlier product of the same user takes that user's learned values as priors (confidence lowered one step). Nothing moves from the private layer to the shared ontology unless the 09-10 rule holds (≥ 2 products used the ingredient) **and** the user releases it. | fixed | 
| B16 | **Variants — the same product with a constraint.** "The same product without sugar" or "with 30 % less fat" is not a new product: it is a new **version** of the same product. Origin `o` = the current product (all scores 0 there); goal `g` = *maintain* every core and identity axis (g = 0); the constraint enters as bounds on `x` (C1 stage: `ING.sucrose` excluded, or an upper bound on the fat role). This is exactly the case `RP` is written for (reduce X, keep Y). If the constraint removes a **key ingredient** (dairy-free version of a milk drink), the result is a *sibling* product: the old product is its reference for flavor and structure, but not its origin — scores are not on the same ruler. | fixed |

**B5 examples.** Profile `[SC.emulsion.ow, APP.dessert, ST.frozen]` (ice cream):

| Scope | Matches? | Why |
|---|---|---|
| `any` | yes | all parts blank |
| `SC.emulsion.ow` | yes | only SC is written, and it equals the profile's SC |
| `SC.emulsion.ow\|APP.dessert` | yes | SC and APP written, both equal; ST blank |
| `SC.emulsion.ow\|APP.dessert\|ST.frozen` | yes | all three written and equal |
| `SC.emulsion.ow\|APP.dessert\|ST.ambient` | **no** | ST is written and differs — `ambient` is a value, not a blank |
| `SC.emulsion.ow\|APP.sauce` | **no** | APP differs |
| `SC.suspension` | **no** | SC differs |

A component scoped `SC.emulsion.ow|APP.dessert` is therefore claimed true for the frozen dessert *and*
for an ambient or chilled emulsion dessert. If it is true only when frozen, the author writes `ST.frozen`.

**Worked tuples** (test cases for Deferred #1):

| Product | SC | APP | ST | Note |
|---|---|---|---|---|
| ice cream | `emulsion.ow` | `dessert` | `frozen` | exists |
| slush | `suspension` (ice crystals in syrup) | `beverage` | `frozen` | needs no new value |
| sorbet | `suspension` | `dessert` | `frozen` | needs no new value |
| drinkable yogurt | `suspension` (B14) | `beverage` | `chilled` | needs no new value |
| set / Greek yogurt | `gel` | `dessert` | `chilled` | needs `SC.gel` — first real case for a new `SC` |

**Product identity (B9, three viewpoints).** A user calls the same project the same product even after
reformulation (versions). An expert calls two products the same *category* when structure and key
ingredients match (soy drink ≠ milk; two brands of soy drink = same category). **The model** calls two
samples the same product only when their ±3 scores can be put on the same ruler: same profile, same
key ingredients, same origin. The rulebook uses the model's definition; changing identity axes starts a
new *version* (new origin). Products that share only a profile are *siblings*. Learning across a user's
own products is governed by B15; constrained variants of one product by B16.
---

## C. Components and vectors

| # | Rule | Status |
|---|---|---|
| C1 | Scope attaches **only to components** — ingredient edges, entries of `P.axes`, `IN` scalars. Nodes (`L P ING FT`) and cards carry no scope. Field name `scope`; absent means `any`; one notation: `SC[\|APP[\|ST]]`. | fixed |
| C2 | An ingredient edge is "this ingredient (or role) moves this `L`". Components written on an `FT` are inherited by its `ING`s; `overrides` on the `ING` win. Negative effects (`direction: decrease`) belong here too. | fixed |
| C3 | `P.axes` is the vector of `L` a parameter stands in for (former `PO`). Every `P` must have it; an empty `axes` is flagged as *to be filled* → *Deferred #3*. | fixed |
| C4 | `IN` is two lists: `interactions` (causal scalars, `from → to`, used by R-3 to shift targets) and `overlaps` (`axes: [a, b]`, "never both core", used by B1 SCOPE). Uncertain relations are not recorded. | fixed |
| C5 | `DC` maps an idiom to a vector over `L`; each component has `direction`. Content is locale-specific → S4. | fixed |
| C6 | `LESSON` is an observation: `type` `scope` `about` `observed` (a vector, A11 components) `when?` `statement` (prose) `source` `confidence`. Every `observed` component must have a matching ingredient edge; if not, the lesson is flagged for promotion. | fixed |
| C7 | `RP` is a prescription: `scope` `reduce` `keep` `compensate: [{ingredient, restores}]` `why` `evidence: [LESSON.*]`. Gap-fill (C4 stage) must work without `RP`; when present, `RP` is preferred. Numbers never live in `RP`. | fixed |
| C8 | `KN` is unchanged for now. | deferred → *Deferred #4* |
| C9 | **Scope index.** A tool lists every component in one table and checks five invariants: (i) every scope segment is a value in its list; (ii) every component matches at least one profile; (iii) if the same `(from, to)` has opposite signs under overlapping scopes, the narrower one must carry `why`; (iv) every core axis of every profile is reached by at least one ingredient edge; (v) `(owner, to, scope)` is unique. | fixed |

---

## D. Cards

| # | Rule | Status |
|---|---|---|
| D1 | A card is a **view**, not a stored record. It is assembled when loaded from three stored pieces, each overriding the previous: lexicon defaults ← profile axis list ← product card. (Worked example: chapter 01 §8.) | fixed |
| D2 | What each piece stores — **lexicon** (`L`): anchor template, `tier: monitored`, `goal: maintain`. **Profile axis list**: `tier`, `goal`, `evidence_required`, `evaluation_note`, `pitfalls`. **Product card**: `identity`, changed tier/goal, `drop`, `legacy_column`, product-specific notes. | fixed |
| D3 | The universal-card file and the per-profile card files are removed. No card has `active_in`. | fixed |
| D4 | One fact, one place. If `tier` for an axis is stored in two places, that is a rule violation. | fixed |
| D5 | Anchor sentence format and the unit of numeric magnitudes (Δ on the ±3 scale per typical dose). | → chapter 04 |
| D6 | **Snapshots.** The assembled card may be saved in the product folder as a dated snapshot ("what the panel saw on this date"), for reproducibility. A snapshot is a copy; the three pieces remain the source, so D1 and D3 are unchanged. | fixed | 

---

## E. Files, names, visibility

| # | Rule | Status |
|---|---|---|
| E1 | Layers are named by words: LEXICON · PARAMETER · STRUCTURE · INGREDIENT · RELATION · PRODUCT_CARD. New files use the word (`structure_taxonomy.yaml`). Legacy `layer<letter>_*.yaml` file names are renamed to words at the 1.1 migration; until then the letters survive only in those file names. | fixed |
| E2 | *(merged into E1)* | retired |
| E4 | **Three visibility classes.** *(1) Vocabulary* — what a user may pick from: `L` labels and definitions, `ING` and `FT` names, profile names, `APP`/`ST` values. Visible as lists, searchable. *(2) Derived views* — the assembled card, the recipe, the feasibility verdict, explanation sentences. Visible. *(3) Classified* — components and their magnitudes, `P.axes`, `IN`, parameter ranges, the taxonomy's structure, `LESSON`/`RP` records, and every file. Never shown, exported or returned by an API. An explanation quotes a lesson's `statement` in prose and never the record. | fixed |
| E5 | **"Related nodes" boundary.** When a user is not satisfied with the nodes Remi suggests, the system may return more nodes from class (1) only, related by **category membership**: for `L`, same modality or subcategory; for `ING`, same role (`FT`); for profiles, same `SC`. A related-nodes answer never uses, ranks by, or reveals a magnitude, an edge, a range or a scope — those are class (3). Chat explanations follow the same line: they may say *that* an ingredient affects an axis, never *how much*. | draft |

---

## F. Change

| # | Rule | Status |
|---|---|---|
| F1 | *(`--check` / `--write` — already in `CLAUDE.md` and each session prompt)* | retired |
| F2 | Edit YAML as text (preserve `&id` anchors and comments). Never round-trip a whole file through `safe_dump`. | fixed |
| F3 | New values are born `confidence: draft`; a person promotes them to `low/medium/high`. | fixed |
| F4 | Old names and shapes are changed **once**, at the 1.1 migration. Until then they are read-only aliases, listed in chapter 00's migration table. | fixed |
| F5 | Decisions are written into this file and the chapters. A decision that exists only in chat does not exist. | fixed |

---

## Deferred — what, and which session decides

| # | Item | Where it is decided |
|---|---|---|
| 1 | New `SC`/`APP` values and sub-levels: `SC.gel` (set yogurt), dressing/dip under sauce?, the width of `APP.sauce`. Test cases: the worked tuples above | S1 with the user, value by value, after this rulebook is fixed |
| 2 | Sign conflicts (17 components with opposite signs across scopes) | S1, chapter 03, after C4/C9 exist |
| 3 | `P.axes` for the 8 parameters that have none today (aw, salt-in-water, solids fraction, SFC37, Tg, Δρ, flocculation, Ostwald) | S1, chapter 03, when `PO` is folded into `P` |
| 4 | `KN` kinetics and the PROCESS layer | later; opens as S6 PROCESS |
| 5 | Anchor sentence format, the unit of numeric magnitudes, `RANGE_TO_SD` | S1 chapter 04 for wording; S3 for numbers; user approval |
| 6 | `DC` content (idioms per locale) | S4 when A2 starts |
| 7 | `RP` content and the `FT`-weight values | S2 |
| 8 | Short-key renames (`sauce_ow→sauce`, `icecream→dessert_frozen`) and all file renames | 1.1 migration, S5 implements |
| 9 | Moving the 7 correlation `IN` records into `overlaps` / `P.axes` | S1 with S3 |

---

## Review list

E5 (related-nodes boundary) is the only open draft. Deferred items are listed above with the session that decides them.
