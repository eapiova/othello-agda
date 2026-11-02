"""Boolean-only specialization diagnostic; no semantic TreeOK claim."""
import hashlib
from pathlib import Path
import completion_batch6 as prior
from provenance import source_identity
from run_job import atomic_json, utc


def emit(check):
    check = Path(check)
    assert not check.exists()
    check.mkdir(parents=True)
    source = prior.ROOT/'src/Othello/ConcreteLowerChecker6.agda'
    text = source.read_text()
    text = text[:text.index('private\n  cong₂')]
    text = text.replace('module Othello.ConcreteLowerChecker6 where', 'module Othello.ConcreteLowerBoolean6 where')
    text = text.replace('import Game.EncodedResolver as General\nmodule Generic = General.Checking order eq g p goal laws picker decode matches matches-sound\nmodule Old = Generic.Old\n', '')
    text = text.replace('import Othello.AgreedIndexed6 as A', 'import Othello.Fast6 as Fast')
    text = text.replace('module Agreed = A.With New.specializedGame6 New.agreement\nlaws : CertificateTransport g p goal\nlaws = Agreed.adapt white (lowerGoal 4) lowerTransport6', 'laws : CertificateTransport Fast.fastGame6 p goal\nlaws = lowerTransport6')
    text += '''
import Game.Balanced as B
checkRows : ∀ {n} → Resolver → (B.Fin n → ℕ) → B.Vec S n →
  B.Vec (DirectedCertificate Key Move) n → Bool
checkRows L embed B.nil B.nil = true
checkRows L embed (B.cons s ss) (B.cons c cs) =
  checkLocal L (embed B.fzero) s c ∧ checkRows L (λ i → embed (B.fsuc i)) ss cs
'''
    target = check/'src/Othello/ConcreteLowerBoolean6.agda'
    target.parent.mkdir(parents=True)
    target.write_text(text)
    old = prior.ROOT/'results/inline-entries-probe6-20261018/check/src/Tests/InlineProbe6/Variant.agda'
    baseline = old.read_text().replace('Tests.InlineProbe6.Variant', 'Tests.ConcreteBooleanProbe6.Baseline')
    baseline = baseline[:baseline.index('abstract\n')]+'''abstract
  checked : Check.checkRows (M.lookup Refs.demand) Original.embed ss Data.newBodies ≡ true
  checked = refl
'''
    variant = baseline.replace('Tests.ConcreteBooleanProbe6.Baseline', 'Tests.ConcreteBooleanProbe6.Variant')
    variant = variant.replace('import Othello.InlineRows6 as Rows', 'import Othello.ConcreteLowerBoolean6 as Check').replace('module Check = Rows.Checking white (lowerGoal 4) lowerTransport6\n', '')
    compare = '''{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted Boolean-only comparison; generic soundness remains unproved.
module Tests.ConcreteBooleanProbe6.Compare where
import Tests.ConcreteBooleanProbe6.Baseline
import Tests.ConcreteBooleanProbe6.Variant
'''
    folder = check/'src/Tests/ConcreteBooleanProbe6'
    folder.mkdir(parents=True)
    for name, body in [('Baseline', baseline), ('Variant', variant), ('Compare', compare)]:
        (folder/(name+'.agda')).write_text(body)
    (check/'othello.agda-lib').write_bytes((prior.ROOT/'othello.agda-lib').read_bytes())
    atomic_json(check.parent/'formal-source-provenance.json', dict(
        format='othello-concrete-boolean6-sources-v1', created_utc=utc(),
        input_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        boolean_source_sha256=hashlib.sha256(text.encode()).hexdigest(),
        existing_boolean_rows=200, conditional_semantic_rows=0,
        generic_soundness_checked=False, native_solver_executed=False,
        new_distinct_rows=0, mathematical_objective_complete=False))
    return source_identity(check)
