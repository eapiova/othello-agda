{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Numeric updates retain a checked canonical-code witness.
module Othello.ErasedArithmeticState6 where

open import Prelude
open import Othello.Board
import Othello.Finite as F
import Othello.RowPacked6 as P
import Othello.RowArithmetic6 as R
import Othello.Incremental6 as Inc
import Othello.DirectMoves6 as Moves
open import Othello.Rules using (nonempty; passState)
import Game.MappedTransfer as T
import Game.BooleanRecompute as Recover
import Othello.Encode6 as E
open import Agda.Builtin.Nat using () renaming (_==_ to _≡ᵇ_)
open import Game.Composite using (StateEquality; stateEquality)

record Coded : Set where
  constructor coded
  field
    raw : P.PackedState
    .storedCanonical : P.encode (P.decode raw) ≡ raw
open Coded public

decode : Coded → State six
decode s = P.decode (raw s)

pack : State six → Coded
pack s = coded (P.encode s) (cong P.encode (P.decode-encode s))

private
  nat-refl : ∀ n → (n ≡ᵇ n) ≡ true
  nat-refl zero = refl
  nat-refl (suc n) = nat-refl n

  rows-refl : ∀ {n} (rows : F.Vec ℕ n) →
    E.sameVec _≡ᵇ_ rows rows ≡ true
  rows-refl F.[] = refl
  rows-refl (n F.∷ ns) rewrite nat-refl n | rows-refl ns = refl

  player-refl : ∀ p → samePlayer p p ≡ true
  player-refl black = refl
  player-refl white = refl

  equal-refl : ∀ s → P.equal s s ≡ true
  equal-refl (P.packed rows p) rewrite rows-refl rows | player-refl p = refl

  module Recovery = Recover.Checking P.equal P.equal-sound equal-refl

canonical : ∀ s → P.encode (P.decode (raw s)) ≡ raw s
canonical (coded r witness) = Recovery.recompute witness

private

  coded-ext : ∀ s t → raw s ≡ raw t → s ≡ t
  coded-ext (coded r a) (coded .r b) refl = refl

equal : Coded → Coded → Bool
equal s t = P.equal (raw s) (raw t)

equal-sound : ∀ s t → equal s t ≡ true → s ≡ t
equal-sound s t checked = coded-ext s t (P.equal-sound (raw s) (raw t) checked)

equality : StateEquality Coded
equality = stateEquality equal equal-sound

certify : ∀ s r → P.encode s ≡ r → Coded
certify s .(P.encode s) refl = pack s

rawRead : P.PackedState → Coord six → Cell
rawRead s (r , c) = R.read (F.lookup (P.codes s) r) c

rawPut : P.PackedState → Coord six → Cell → P.PackedState
rawPut s (r , c) v = P.packed
  (F.updateAt (P.codes s) r (λ n → R.replace n c v)) (P.whose s)

private
  lookup-encodeRows : ∀ {n} (rows : F.Vec P.Row n) r →
    F.lookup (P.encodeRows rows) r ≡ P.encodeRow (F.lookup rows r)
  lookup-encodeRows (row F.∷ rows) F.zero = refl
  lookup-encodeRows (row F.∷ rows) (F.suc r) = lookup-encodeRows rows r

  update-encodeRows : ∀ {n} (rows : F.Vec P.Row n) r c v →
    F.updateAt (P.encodeRows rows) r (λ k → R.replace k c v) ≡
    P.encodeRows (F.updateAt rows r (λ row → F.updateAt row c (λ _ → v)))
  update-encodeRows (row F.∷ rows) F.zero c v rewrite R.replace-encode row c v = refl
  update-encodeRows (row F.∷ rows) (F.suc r) c v =
    cong (λ rest → P.encodeRow row F.∷ rest) (update-encodeRows rows r c v)

rawRead-encode : ∀ s q → rawRead (P.encode s) q ≡ at {six} (board s) q
rawRead-encode (state b p) (r , c) rewrite lookup-encodeRows b r =
  R.read-encode (F.lookup b r) c

rawPut-encode : ∀ s q v → rawPut (P.encode s) q v ≡
  P.encode (state (put {six} (board s) q v) (toMove s))
rawPut-encode (state b p) (r , c) v =
  cong (λ rows → P.packed rows p) (update-encodeRows b r c v)

mark : Player → Cell → Cell
mark p empty = empty
mark p blackCell = playerCell p
mark p whiteCell = playerCell p

rawMark : P.PackedState → Player → Coord six → P.PackedState
rawMark s p q = rawPut s q (mark p (rawRead s q))

private
  update-value : ∀ {A : Set} {n} (xs : F.Vec A n) i (f : A → A) →
    F.updateAt xs i (λ _ → f (F.lookup xs i)) ≡ F.updateAt xs i f
  update-value (x F.∷ xs) F.zero f = refl
  update-value (x F.∷ xs) (F.suc i) f = cong (F._∷_ x) (update-value xs i f)

  mark-put : ∀ {n} (b : F.Vec P.Row n) r c p →
    F.updateAt b r (λ row → F.updateAt row c (λ _ → mark p (F.lookup (F.lookup b r) c))) ≡
    F.updateAt b r (λ row → F.updateAt row c (mark p))
  mark-put (row F.∷ rows) F.zero c p =
    cong (λ newRow → newRow F.∷ rows) (update-value row c (mark p))
  mark-put (row F.∷ rows) (F.suc r) c p =
    cong (F._∷_ row) (mark-put rows r c p)

  update-cong : ∀ {A : Set} {n} (xs : F.Vec A n) i {f g : A → A} →
    (∀ x → f x ≡ g x) → F.updateAt xs i f ≡ F.updateAt xs i g
  update-cong (x F.∷ xs) F.zero equal = cong (λ y → y F.∷ xs) (equal x)
  update-cong (x F.∷ xs) (F.suc i) equal = cong (F._∷_ x) (update-cong xs i equal)

  modify-cong : ∀ b q {f g : Cell → Cell} →
    (∀ c → f c ≡ g c) → Inc.modify b q f ≡ Inc.modify b q g
  modify-cong b (r , c) equal = update-cong b r (λ row → update-cong row c equal)

  single-mark : ∀ b p q → Inc.modify b q (mark p) ≡ Inc.flipMany b p (q ∷ [])
  single-mark b p q = modify-cong b q
    (λ { empty → refl ; blackCell → refl ; whiteCell → refl })

rawMark-encode : ∀ s p q → rawMark (P.encode s) p q ≡
  P.encode (state (Inc.modify (board s) q (mark p)) (toMove s))
rawMark-encode (state b turn) p q@(r , c) rewrite rawRead-encode (state b turn) q =
  trans (rawPut-encode (state b turn) q (mark p (at {six} b q)))
    (cong (λ newBoard → P.encode (state newBoard turn)) (mark-put b r c p))

rawFlip : P.PackedState → Player → List (Coord six) → P.PackedState
rawFlip s p [] = s
rawFlip s p (q ∷ qs) = rawMark (rawFlip s p qs) p q

rawFlip-encode : ∀ s p qs → rawFlip (P.encode s) p qs ≡
  P.encode (state (Inc.flipMany (board s) p qs) (toMove s))
rawFlip-encode s p [] = refl
rawFlip-encode s p (q ∷ qs) rewrite rawFlip-encode s p qs =
  trans (rawMark-encode (state (Inc.flipMany (board s) p qs) (toMove s)) p q)
    (cong (λ b → P.encode (state b (toMove s)))
      (single-mark (Inc.flipMany (board s) p qs) p q))

switchRaw : P.PackedState → P.PackedState
switchRaw (P.packed rows p) = P.packed rows (other p)

pass : Coded → Coded
pass s = coded (switchRaw (raw s)) (cong switchRaw (canonical s))

pickRaw : P.PackedState → Coord six → Maybe P.PackedState
pickRaw s q with sameCell (rawRead s q) empty ∧ nonempty (Moves.capturesAt (P.decode s) q)
... | false = nothing
... | true = just (switchRaw
  (rawPut (rawFlip s (P.whose s) (Moves.capturesAt (P.decode s) q)) q (playerCell (P.whose s))))

abstract
  pickRaw-encode : ∀ s q → pickRaw (P.encode s) q ≡
    T.mapMaybe P.encode (Moves.pick s q)
  pickRaw-encode s q rewrite P.decode-encode s | rawRead-encode s q
    with sameCell (at {six} (board s) q) empty ∧ nonempty (Moves.capturesAt s q)
  ... | false = refl
  ... | true rewrite P.decode-encode s = trans
    (cong (λ r → just (switchRaw (rawPut r q (playerCell (toMove s)))))
      (rawFlip-encode s (toMove s) (Moves.capturesAt s q)))
    (cong (λ r → just (switchRaw r))
      (rawPut-encode (state (Inc.flipMany (board s) (toMove s) (Moves.capturesAt s q)) (toMove s))
        q (playerCell (toMove s))))

  pickRaw-agrees : ∀ s q → pickRaw (raw s) q ≡ T.mapMaybe P.encode (Moves.pick (decode s) q)
  pickRaw-agrees s q = trans (cong (λ r → pickRaw r q) (sym (canonical s)))
    (pickRaw-encode (decode s) q)

  results-agree : ∀ s q a b → pickRaw (raw s) q ≡ a → Moves.pick (decode s) q ≡ b →
    a ≡ T.mapMaybe P.encode b
  results-agree s q a b er ep = trans (sym er)
    (trans (pickRaw-agrees s q) (cong (T.mapMaybe P.encode) ep))

private
  nothing-elim : ∀ {A B : Set} {x : A} → nothing ≡ just x → B
  nothing-elim ()

  just-injective : ∀ {A : Set} {x y : A} → just x ≡ just y → x ≡ y
  just-injective refl = refl

  abstract
    picked-canonical : ∀ s q r → pickRaw (raw s) q ≡ just r →
      P.encode (P.decode r) ≡ r
    picked-canonical s q r hit with Moves.pick (decode s) q in ep
    ... | nothing = nothing-elim (sym (results-agree s q (just r) nothing hit ep))
    ... | just t = let e = sym (just-injective (results-agree s q (just r) (just t) hit ep)) in
      trans (cong (λ a → P.encode (P.decode a)) (sym e))
        (trans (cong P.encode (P.decode-encode t)) e)

pick : Coded → Coord six → Maybe Coded
pick s q with pickRaw (raw s) q in ep
... | nothing = nothing
... | just r = just (coded r (picked-canonical s q r ep))

abstract
  pick-decodes : ∀ s q → T.mapMaybe decode (pick s q) ≡ Moves.pick (decode s) q
  pick-decodes s q with pickRaw (raw s) q in er | Moves.pick (decode s) q in ep
  ... | nothing | nothing = refl
  ... | nothing | just t = nothing-elim (results-agree s q nothing (just t) er ep)
  ... | just r | nothing = nothing-elim (sym (results-agree s q (just r) nothing er ep))
  ... | just r | just t = cong just
    (trans (cong P.decode (just-injective (results-agree s q (just r) (just t) er ep)))
      (P.decode-encode t))
