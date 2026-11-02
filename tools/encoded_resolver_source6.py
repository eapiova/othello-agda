"""AI-assisted checker specialization; safe Agda checks every proof transport."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def generate():
    original=(ROOT/'src/Game/DirectedIndexed.agda').read_text()
    evaluator=original[original.index('  mutual\n    checkLocal :'):original.index('  mutual\n    data LocalOK')]
    evaluator=evaluator.replace('Resolver Key S','Resolver').replace('equal eq','matches')
    sound=original[original.index('  mutual\n    checkLocal-sound :'):original.index('  Compatible :')]
    sound=sound.replace('LocalOK L','Old.LocalOK (decodeResolver L)').replace('ForestOK L','Old.ForestOK (decodeResolver L)')
    sound=re.sub(r'\bok-([A-Za-z]+)',r'Old.ok-\1',sound)
    sound=sound.replace('equal-sound eq','matches-sound')
    sound=sound.replace('order j owner eb) el\n','order j owner eb) (cong decodeMaybe el)\n')
    sound=sound.replace('order j owner eb) et el\n','order j owner eb) et (cong decodeMaybe el)\n')
    header='''{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Keep ordinary working states; decode stored codes only in proofs.
module Game.EncodedResolver where

open import Game.Core
open import Game.Composite using (StateEquality)
open import Game.BooleanSearch using (forcesB)
open import Game.Symmetry using (CertificateTransport; act; acceptedTag)
open import Game.DirectedIndexed using (DirectedCertificate; indexedLeaf; indexedSolve;
  indexedChoice; indexedFork; indexedPass; cite; citeBy; indexedPick; MovePicker; pick)
import Game.DirectedIndexed as D
import Game.Indexed as I

private
  false-elim : ∀ {A : Set} → false ≡ true → A
  false-elim ()

  nothing-elim : ∀ {A B : Set} {x : A} → nothing ≡ just x → B
  nothing-elim ()

  just-injective : ∀ {A : Set} {x y : A} → just x ≡ just y → x ≡ y
  just-injective refl = refl

  and-left : ∀ a b → a ∧ b ≡ true → a ≡ true
  and-left true b checked = refl
  and-left false b ()

  and-right : ∀ a b → a ∧ b ≡ true → b ≡ true
  and-right true b checked = checked
  and-right false b ()

module Checking {Key S Stored Move : Set} (order : I.Order Key) (eq : StateEquality S)
  (g : Game S) (p : Player) (goal : S → Bool)
  (laws : CertificateTransport g p goal) (picker : MovePicker g Move)
  (decode : Stored → S) (matches : S → Stored → Bool)
  (matches-sound : ∀ s t → matches s t ≡ true → s ≡ decode t) where

  module Old = D.Checker order eq g p goal laws picker

  Resolver : Set
  Resolver = Key → Maybe Stored

  decodeMaybe : Maybe Stored → Maybe S
  decodeMaybe nothing = nothing
  decodeMaybe (just t) = just (decode t)

  decodeResolver : Resolver → Key → Maybe S
  decodeResolver L j = decodeMaybe (L j)

'''
    tail='''  Compatible : Resolver → (Key → Stored) → Set
  Compatible L G = ∀ j u → L j ≡ just u → G j ≡ u

  decoded-compatible : ∀ {L G} → Compatible L G →
    Old.Compatible (decodeResolver L) (λ j → decode (G j))
  decoded-compatible {L} {G} compatible j s hit with L j in el
  ... | nothing = nothing-elim hit
  ... | just u = trans (cong decode (compatible j u el)) (just-injective hit)

  abstract
    tree-sound : ∀ L G owner s c → Compatible L G → checkLocal L owner s c ≡ true →
      Old.TreeOK (λ j → decode (G j)) owner s c
    tree-sound L G owner s c compatible checked =
      Old.lift-local (decoded-compatible compatible) (checkLocal-sound L owner s c checked)
'''
    (ROOT/'src/Game/EncodedResolver.agda').write_text(header+evaluator+sound+tail)
