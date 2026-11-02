#!/usr/bin/env python3
"""Repair one unchecked numeric part; preserve its original exported type.

Every state-vector bridge is a closed safe Agda equality, never an assumption.
Unchanged accepted modules and original data are not rewritten.
"""
import hashlib
from pathlib import Path
import re

from nat_indexed_pilot6 import HEADER
from wire_workflow6 import require

PREFIX = 'Tests.NatDescendant6'


def parse_map(text):
    tokens = re.findall(r'\(|\)|[A-Za-z0-9_.]+', text)
    require(' '.join(tokens).replace(' ', '') == re.sub(r'\s+', '', text), 'unsupported map syntax')
    position = 0

    def term():
        nonlocal position
        require(position < len(tokens), 'truncated sparse map')
        token = tokens[position]
        position += 1
        if token == 'M.absent':
            return ('absent',)
        require(token == '(' and position < len(tokens), 'map constructor expected')
        constructor = tokens[position]
        position += 1
        if constructor == 'M.rows':
            require(position + 3 < len(tokens), 'truncated rows')
            base, size, vector = tokens[position:position + 3]
            position += 3
            require(base.isdecimal() and size.isdecimal() and re.fullmatch(r'S[0-9]+\.states', vector),
                    'literal state rows required')
            result = ('rows', int(base), int(size), int(vector[1:-7]))
        else:
            require(constructor == 'M.branch' and position < len(tokens) and tokens[position].isdecimal(),
                    'unsupported sparse branch')
            pivot = int(tokens[position])
            position += 1
            result = ('branch', pivot, term(), term())
        require(position < len(tokens) and tokens[position] == ')', 'map closing parenthesis expected')
        position += 1
        return result

    result = term()
    require(position == len(tokens), 'trailing map syntax')
    return result


def expressions(node):
    if node[0] == 'absent':
        return 'M.absent', 'refl', set()
    if node[0] == 'rows':
        _, base, n, j = node
        return (f'(M.rows {base} {n} (Lazy.states {n} S{j}.text))',
                f'(cong (M.rows {base} {n}) E{j}.same)', {j})
    _, pivot, left, right = node
    l, le, ld = expressions(left)
    r, requal, rd = expressions(right)
    return f'(M.branch {pivot} {l} {r})', f'(branchEqual {pivot} {le} {requal})', ld | rd


def generate(check, part, *, accepted_parts):
    check = Path(check)
    require(part == accepted_parts and 0 <= part < 267, 'only the next unchecked part may be repaired')
    folder = check / 'src' / PREFIX.replace('.', '/')
    original = folder / f'Part{part}.agda'
    old = original.read_text()
    require(f'module {PREFIX}.Part{part} where' in old and 'LazyFamily' not in old,
            'original unchecked part required')
    require(not re.search(r'^import ' + re.escape(PREFIX) + r'\.Part[0-9]+(?:\s|$)', old, re.M),
            'a row part must not import other part proofs')
    data = (folder / f'PartData{part}.agda').read_text()
    line = re.search(r'^demand = (.+)$', data, re.M)
    require(line is not None, 'original sparse demand required')
    fast, same, dependencies = expressions(parse_map(line[1]))
    require(part in dependencies, 'own state rows are missing')
    state_modules = dict((int(j), module) for module, j in re.findall(
        r'^import ([A-Za-z0-9_.]+) as S([0-9]+)$', data, re.M))
    require(dependencies <= state_modules.keys(), 'state data import missing')
    generated = {}
    targets = []

    def emit(name, body, replace=False):
        path = folder / (name + '.agda')
        content = HEADER + '-- AI-assisted generator; all assertions checked by safe Agda.\nmodule ' + PREFIX + '.' + name + ' where\n\n' + body
        if path.exists() and not replace:
            require(path.read_text() == content, 'existing helper source differs')
        else:
            path.write_text(content)
        generated[path.relative_to(check).as_posix()] = hashlib.sha256(content.encode()).hexdigest()

    family = '''open import Game.Core using (white)
open import Othello.Statements using (lowerGoal)
open import Othello.SharedSymmetry6 using (lowerTransport6)
import Othello.Fast6 as Fast
import Othello.LazyIndexed6 as Lazy
module Lower = Lazy.Checking Fast.fastGame6 white (lowerGoal 4) lowerTransport6
'''
    emit('LazyFamily', family)
    targets.append(PREFIX + '.LazyFamily')
    emit('RepairBridge', f'''open import Prelude
open import Agda.Builtin.Nat using (_+_)
open import Agda.Builtin.String using (String)
open import Othello.Board using (State; six)
import Game.Balanced as B
import Game.Indexed as I
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Othello.LazyIndexed6 as Lazy
import Othello.NatIndexed6 as D
import {PREFIX}.Family as Family
import {PREFIX}.LazyFamily as LazyFamily

link : ∀ {{n}} base (oldDemand fastDemand oldStates : M.Map (State six)) →
  (oldBodies : M.Map (I.IndexedCertificate ℕ)) → (stateText bodyText : String) →
  fastDemand ≡ oldDemand → M.rows base n (Lazy.states n stateText) ≡ oldStates →
  M.rows base n (D.bodies n bodyText) ≡ oldBodies →
  LazyFamily.Lower.checkPart {{n}} (M.lookup fastDemand) (λ i → base + B.finToNat i)
    stateText bodyText ≡ true →
  (G : ℕ → State six) → (C : ℕ → I.IndexedCertificate ℕ) →
  Laws.Aligned oldDemand G → Laws.Aligned oldStates G → Laws.Aligned oldBodies C →
  Family.A.Partial G C oldStates
link base oldDemand fastDemand oldStates oldBodies stateText bodyText
  demandEqual statesEqual bodiesEqual accepted G C demand states bodies =
  subst (Family.A.Partial G C) statesEqual
    (LazyFamily.Lower.linkedAligned base fastDemand stateText bodyText accepted G C
      (subst (λ m → Laws.Aligned m G) (sym demandEqual) demand)
      (subst (λ m → Laws.Aligned m G) (sym statesEqual) states)
      (subst (λ m → Laws.Aligned m C) (sym bodiesEqual) bodies))
''')
    targets.append(PREFIX + '.RepairBridge')
    sizes = {}
    for j in sorted(dependencies):
        module = state_modules[j]
        raw = (check / 'src' / (module.replace('.', '/') + '.agda')).read_text()
        match = re.search(r'^states : B\.Vec \(State six\) ([0-9]+)$', raw, re.M)
        require(match is not None and 0 < int(match[1]) <= 200, 'bounded original state vector required')
        sizes[j] = int(match[1])
        emit('StateEq' + str(j), f'''open import Prelude
import Othello.LazyIndexed6 as Lazy
import {module} as S
abstract
  same : Lazy.states {sizes[j]} S.text ≡ S.states
  same = refl
''')
        targets.append(PREFIX + '.StateEq' + str(j))
    own = sizes[part]
    head, _ = old.split('abstract\n', 1)
    signature = re.search(r'  linked : ([\s\S]+?)\n  linked = ', old)
    require(signature is not None, 'original conditional export signature required')
    extras = f'import {PREFIX}.LazyFamily as LazyFamily\nimport {PREFIX}.RepairBridge as Bridge\nimport Othello.LazyIndexed6 as Lazy\n'
    for j in sorted(dependencies):
        if j != part:
            extras += f'import {state_modules[j]} as S{j}\n'
        extras += f'import {PREFIX}.StateEq{j} as E{j}\n'
    body = head.split(' where\n\n', 1)[1] + extras + f'''
branchEqual : ∀ {{a b c d : M.Map (State six)}} pivot → a ≡ b → c ≡ d →
  M.branch pivot a c ≡ M.branch pivot b d
branchEqual pivot refl refl = refl
fastDemand : M.Map (State six)
fastDemand = {fast}
abstract
  demandEqual : fastDemand ≡ Data.demand
  demandEqual = {same}
  statesEqual : M.rows {200 * part} {own} (Lazy.states {own} S{part}.text) ≡ Data.states
  statesEqual = cong (M.rows {200 * part} {own}) E{part}.same
  accepted : LazyFamily.Lower.checkPart (M.lookup fastDemand) embed S{part}.text C{part}.text ≡ true
  accepted = refl
  linked : {signature[1]}
  linked G C demand states bodies =
    Bridge.link {{n = {own}}} {200 * part} Data.demand fastDemand Data.states Data.bodies
      S{part}.text C{part}.text demandEqual statesEqual refl accepted G C demand states bodies
'''
    emit('Part' + str(part), body, replace=True)
    targets.append(PREFIX + '.Part' + str(part))
    return dict(part=part, dependencies=sorted(dependencies), targets=targets,
                original_part_sha256=hashlib.sha256(old.encode()).hexdigest(),
                generated_sha256=generated, exported_linked_type_unchanged=True,
                scope='one unchecked lazy part with explicit original-vector equalities')
