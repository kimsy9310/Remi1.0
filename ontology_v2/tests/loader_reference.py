# -*- coding: utf-8 -*-
"""
remi ontology v2 — REFERENCE LOADER
Implements the loader-side rules of remi_ontology_spec_v2.md that are easy to get
wrong. Read this before writing your own loader; the four rules below were each
found by a smoke test failing (see migration/_MIGRATION_v2.md, findings F1-F8).

Usage:
    python loader_reference.py                 # validate all profiles
    python loader_reference.py suspension      # validate + assemble one profile

Requires: pyyaml, numpy. Model glue (mixture.py) is NOT included here.
"""
import sys, os, glob, yaml
import numpy as np

LAYERS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'layers')

# ---------------------------------------------------------------- numeric contracts (spec §5)
MAGNITUDE  = {'weak': 0.3, 'medium': 0.6, 'strong': 1.0}      # per 1 SD, -3..+3 scale
CONFIDENCE = {'high': 8.0, 'medium': 2.0, 'low': 0.4}         # prior precision Lambda
RELIABILITY_SIGMA = {'high': 0.5, 'medium': 1.0, 'low': 1.8,  # observation noise sigma
                     'low_absolute_high_relative': 1.0}
RHO = {'weak': 0.2, 'medium': 0.4, 'strong': 0.6}             # Sigma0 correlation
DELTA = {'strong': 2.0, 'medium': 1.0, 'weak': 0.5}           # R-3 target shift

# profile registry: profile key -> (M card files in layering order, scope aliases)
PROFILES = {
    'suspension': dict(
        cards=['layerM_cards_suspension.yaml'],
        scopes={'any', 'SC.suspension'}),
    'sauce_ow': dict(
        cards=['layerM_cards_sauce_ow.yaml'],
        scopes={'any', 'SC.emulsion.ow', 'SC.emulsion.ow.sauce', 'SC.emulsion.ow|APP.sauce'}),
    # 2026-09-11 에 beverage_cloud / beverage_milk 로 갈랐다가 09-12 에 되돌렸다.
    # 유음료는 SC.emulsion.ow x APP.beverage 에 ING.milk 가 든 제품이지 별도 APP 이
    # 아니다 - CLAUDE.md '제품의존은 없다'. 음료 프로파일 하나가 클라우드와 유음료를
    # 다 담도록 범위를 넓혔다 (tools/add_application.py --tidy).
    'beverage': dict(
        cards=['layerM_cards_beverage.yaml'],
        scopes={'any', 'SC.emulsion.ow', 'SC.emulsion.ow.beverage', 'SC.emulsion.ow|APP.beverage'}),
    # 2026-09-10: 'beverage_coffee_milk' 를 뺐다. 제품이 프로파일 등록부에
    # 제형처럼 올라 있었다. 스펙 2.3 이 활성 맥락을 SC x APP x ST 로만 정의해
    # 제품 차원이 없다는 것을 그 파일 헤더가 이미 적고 있었다. 실측이 없어
    # 잃는 것도 없다 - 제형 기본에 없던 카드는 커피 향·우유 향 둘뿐이고
    # 둘 다 재료만 넣으면 도달한다.
    # 2026-09-10: 'SC.emulsion.ow' 를 더했다. 아이스크림도 O/W 에멀전인데 그것이
    # 빠져 있어, 음료·소스와 형제로 인식되지 않았다. 두 가지가 걸려 있었다 —
    # (1) 제형 공통 물리를 위로 올리기 시작하면 아이스크림만 못 받는다.
    # (2) tools/audit_axis_scope.py 의 엣지 결손 비교가 structure_class 가족
    #     끼리 하는데, 아이스크림은 혼자라 가족이 만들어지지 않아 **비교 대상이
    #     된 적이 한 번도 없었다.**
    # 도달 자체는 거의 안 변한다(plain 'SC.emulsion.ow' 로만 걸린 엣지가 태그
    # 1건뿐). 바뀌는 것은 감사가 아이스크림을 형제로 보기 시작한다는 것이다.
    # 냉동 고유 스코프 둘은 그대로 둔다 — 얼음·오버런은 진짜 냉동 전용이다.
    'dressing': dict(   # 2026-09-11 tools/add_application.py 로 sauce_ow 에서 파생
        cards=['layerM_cards_dressing.yaml'],
        # 'SC.emulsion.ow.sauce' 를 넣는다 - 용량 면에서 소스의 하위 용도라 소스의
        # INGREDIENT 엣지(재료->물성, 용량이 든 것)를 물려받는다. R-1(물리)은 부모
        # SC.emulsion.ow 에서 온다. 베끼지도, 크기를 고르지도 않는다 (2026-09-11).
        scopes={'any', 'SC.emulsion.ow', 'SC.emulsion.ow.sauce',
                'SC.emulsion.ow.dressing', 'SC.emulsion.ow|APP.dressing'}),
    'dip': dict(   # 2026-09-11 tools/add_application.py 로 sauce_ow 에서 파생
        cards=['layerM_cards_dip.yaml'],
        # 'SC.emulsion.ow.sauce' 를 넣는다 - 용량 면에서 소스의 하위 용도라 소스의
        # INGREDIENT 엣지(재료->물성, 용량이 든 것)를 물려받는다. R-1(물리)은 부모
        # SC.emulsion.ow 에서 온다. 베끼지도, 크기를 고르지도 않는다 (2026-09-11).
        scopes={'any', 'SC.emulsion.ow', 'SC.emulsion.ow.sauce',
                'SC.emulsion.ow.dip', 'SC.emulsion.ow|APP.dip'}),
    'condiment': dict(   # 2026-09-11 tools/add_application.py 로 suspension 에서 파생
        cards=['layerM_cards_condiment.yaml'],
        scopes={'any', 'SC.suspension', 'SC.suspension.condiment', 'SC.suspension|APP.condiment'}),
    'icecream': dict(
        cards=['layerM_cards_icecream.yaml'],
        scopes={'any', 'SC.emulsion.ow', 'SC.frozen.ice_cream',
                'SC.emulsion.ow|APP.dessert|ST.frozen'}),
}


def load_stack(layers_dir=LAYERS):
    """Load L, M, C, S, R. RULE 1 (alias_of): scope-extension tags merge into their base."""
    L = yaml.safe_load(open(f'{layers_dir}/layerL_lexicon.yaml', encoding='utf-8'))
    lex = {t['id']: t for t in L['lexicon_terms']}

    tags, ings, dup = {}, {}, []
    for f in sorted(glob.glob(f'{layers_dir}/layerC2_*.yaml')):
        d = yaml.safe_load(open(f, encoding='utf-8')) or {}
        for key in ('function_tags', 'function_tags_ext'):
            for t in d.get(key) or []:
                if t['id'] in tags: dup.append(('tag', t['id'], os.path.basename(f)))
                tags[t['id']] = t
        for key in ('ingredients', 'ingredients_ext'):
            for g in d.get(key) or []:
                if g['id'] in ings: dup.append(('ingredient', g['id'], os.path.basename(f)))
                ings[g['id']] = g
    # RULE 1: fold alias_of tags into their base tag, then drop them
    for tid in list(tags):
        base = tags[tid].get('alias_of')
        if base and base in tags:
            tags[base].setdefault('effects', []).extend(tags[tid].get('effects') or [])
            del tags[tid]
    # ingredients may also carry alias_of (edge extensions): fold overrides into the base
    for gid in list(ings):
        base = ings[gid].get('alias_of')
        if base and base in ings:
            ings[base].setdefault('overrides', []).extend(ings[gid].get('overrides') or [])
            del ings[gid]

    S = yaml.safe_load(open(f'{layers_dir}/layerS2_profiles.yaml', encoding='utf-8'))['structure_profiles']
    R = yaml.safe_load(open(f'{layers_dir}/layerR_seed.yaml', encoding='utf-8'))
    return dict(lex=lex, tags=tags, ings=ings, S=S, R=R, duplicates=dup)


def load_cards(profile, layers_dir=LAYERS):
    cards = []
    for fn in PROFILES[profile]['cards']:
        cards += yaml.safe_load(open(f'{layers_dir}/{fn}', encoding='utf-8'))['measurement_cards']
    return cards


def in_scope(edge, scopes):
    """RULE 2 (spec §5.10): dotted class paths and profile-identity strings are the same
    thing; a dotted prefix matches its refinements. Skipping this silently yields zero
    in-scope edges, which looks like a reachability failure but is a loader bug (F4)."""
    sc = edge.get('scoped_to_structure_class', 'any')
    scs = sc if isinstance(sc, list) else [sc]
    return any(s in scopes for s in scs)


def effects_of(ing, tags, proxies, scopes):
    """All (percept -> signed prior) an ingredient can move in this profile.

    RULE 3 (spec §5.11): where no direct edge to an L term exists, compose
    C edge (ING -> P) with an R-1 record (P -> percept). In emulsion profiles most
    texture/appearance percepts are reachable ONLY this way (F6), so a loader that
    skips composition will report healthy layers and an unusable model.
    """
    raw = {}
    for ft in ing.get('function_tags') or []:
        for e in (tags.get(ft, {}).get('effects') or []):
            if in_scope(e, scopes) and 'direction' in e: raw[e['to']] = e
    for e in (ing.get('overrides') or []):
        if in_scope(e, scopes) and 'direction' in e: raw[e['to']] = e
    for e in (ing.get('flavor_profile') or []):
        if 'direction' in e: raw[e['to']] = e          # flavor edges are recipe-activated

    out = {}
    for to, e in raw.items():                          # direct edges win
        if to.startswith('L.'):
            out[to] = dict(sign=1 if e['direction'] == 'increase' else -1,
                           mag=MAGNITUDE.get(e.get('magnitude') or e.get('intensity') or 'medium', 0.6),
                           conf=CONFIDENCE.get(e.get('confidence', 'medium'), 2.0), via='direct')
    for to, e in raw.items():                          # then composed edges
        if not to.startswith('P.'): continue
        esign = 1 if e['direction'] == 'increase' else -1
        emag = MAGNITUDE.get(e.get('magnitude', 'medium'), 0.6)
        econf = CONFIDENCE.get(e.get('confidence', 'medium'), 2.0)
        for r in proxies.get(to, []):
            p = r['percept']
            if out.get(p, {}).get('via') == 'direct': continue
            cand = dict(sign=esign * (1 if r['monotone'] == 'increasing' else -1),
                        mag=emag, conf=min(econf, CONFIDENCE.get(r.get('confidence', 'medium'), 2.0)),
                        via=f"composed:{to}")
            if p not in out or cand['mag'] > out[p]['mag']: out[p] = cand
    return out


def validate(profile, stack, cards):
    """Invariant checks. Returns (fails, warns)."""
    lex, tags, ings, R = stack['lex'], stack['tags'], stack['ings'], stack['R']
    scopes = PROFILES[profile]['scopes']
    proxies = {}
    for r in R['relations_proxy']:
        if r['scope'] in scopes: proxies.setdefault(r['parameter'], []).append(r)
    fails, warns = [], []
    for kind, i, f in stack['duplicates']:
        fails.append(f'Invariant 2: duplicate {kind} {i} (last definition wins, in {f})')
    for c in cards:
        if c['term_id'] not in lex: fails.append(f'M card references unknown term {c["term_id"]}')
        for req in ('tier', 'method', 'scale_type', 'default_goal', 'reliability', 'evidence_required'):
            if req not in c: fails.append(f'M card {c["term_id"]}: missing {req}')
    core = [c for c in cards if c['tier'] == 'core']
    if len(core) > 10: warns.append(f'spec §5.7: core tier = {len(core)} (> ~10 vs n=5-20)')
    movable = set()
    for g in ings.values():
        movable |= set(effects_of(g, tags, proxies, scopes))
    for c in core:
        # RULE 4 (Invariant 6): reachability applies to ACTIVATED terms, and counts
        # indirect movement through R-1. Shelf terms with no card are legal inventory.
        if c['term_id'] not in movable:
            fails.append(f'Invariant 6: core term {c["term_id"]} has no in-scope actuator')
    return fails, warns


def assemble(profile, stack, cards, palette):
    """Model inputs per spec §5: y axes, Gamma0, Lambda, Sigma0.
    NOTE: Gamma0 is on the standardized-x scale; the caller must center/scale x
    (open item G1). Ingredient upper limits live in C as free-text `limitations`
    and are NOT translated here (open item G5) - pass real bounds to propose()."""
    tags, ings, R = stack['tags'], stack['ings'], stack['R']
    scopes = PROFILES[profile]['scopes']
    proxies = {}
    for r in R['relations_proxy']:
        if r['scope'] in scopes: proxies.setdefault(r['parameter'], []).append(r)

    core = [c for c in cards if c['tier'] == 'core'
            and c['evidence_required'] != 'sample_aged']       # §5.8 time quarantine
    y_terms = [c['term_id'] for c in core]
    q, m = len(palette), len(y_terms)
    G0 = np.zeros((q, m)); lam_e = np.full((q, m), CONFIDENCE['low'])
    for j, gid in enumerate(palette):
        eff = effects_of(ings[gid], tags, proxies, scopes)
        for k, t in enumerate(y_terms):
            if t in eff:
                G0[j, k] = eff[t]['sign'] * eff[t]['mag']
                lam_e[j, k] = eff[t]['conf']
    lam = lam_e.min(axis=1)   # §5.3 interim: mixture.py takes Lambda as (q,);
                              # change it to (q, m) and pass lam_e instead.
    sigma = np.array([RELIABILITY_SIGMA[c['reliability']] for c in core])
    Sigma0 = np.diag(sigma ** 2)
    for r in R['relations_interaction']:
        a, b = r['from'], r['to']
        if a in y_terms and b in y_terms:
            i, j = y_terms.index(a), y_terms.index(b)
            sign = -1 if r['effect'] in ('suppress', 'inverse_corr') else +1
            Sigma0[i, j] = Sigma0[j, i] = sign * RHO[r['magnitude']] * sigma[i] * sigma[j]
    return dict(y_terms=y_terms, Gamma0=G0, Lambda=lam, Lambda_per_edge=lam_e,
                Sigma0=Sigma0, cards=core)


def decompose(idiom_or_ko, R, y_terms):
    """R-3: holistic user phrase -> target deltas (§5.6).
    CAUTION (F8): a masking relation recorded only in R-2 is invisible to the mean
    prediction, because the model is y = f(x) and cannot express y-to-y coupling.
    Masking/enhancement must ALSO exist as a C edge."""
    for rec in R['relations_decomposition']:
        if idiom_or_ko in (rec.get('idiom'), rec.get('idiom_ko')):
            return {c['term']: DELTA[c['weight']] for c in rec['components'] if c['term'] in y_terms}
    return {}


if __name__ == '__main__':
    stack = load_stack()
    todo = sys.argv[1:] or list(PROFILES)
    print(f"stack: L={len(stack['lex'])} terms | C={len(stack['ings'])} ingredients, "
          f"{len(stack['tags'])} tags | S={len(stack['S'])} profiles | "
          f"R={sum(len(stack['R'][k]) for k in stack['R'] if k.startswith('relations'))} records")
    for prof in todo:
        cards = load_cards(prof)
        fails, warns = validate(prof, stack, cards)
        core = [c for c in cards if c['tier'] == 'core']
        aged = [c['term_id'] for c in cards if c['evidence_required'] == 'sample_aged']
        print(f"\n[{prof}] cards={len(cards)} core={len(core)} aged-quarantined={len(aged)} "
              f"-> {'FAIL' if fails else 'OK'}")
        for f in fails: print('   FAIL:', f)
        for w in warns: print('   warn:', w)
