{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. A genuine toy symmetry reverses the winning choice index.
-- Othello tags are decoded here without claiming concrete 6×6 transport laws.
module Tests.SharedSymmetry6 where

open import Game.Core
open import Game.Certificate
open import Game.Composite using (StateEquality)
open import Game.Shared
open import Game.Symmetry using (CertificateTransport)
open import Othello.Shared6 using (readShared)
open import Agda.Builtin.String using (primStringToList)

data Toy : Set where
  left right win lose both : Toy

moves : Toy → List Toy
moves left = win ∷ lose ∷ []
moves right = lose ∷ win ∷ []
moves win = []
moves lose = []
moves both = win ∷ win ∷ []

owner : Toy → Player
owner both = white
owner _ = black

toy : Game Toy
toy = record { turn = owner ; next = moves ; forcedPass = λ _ → false }

goal : Toy → Bool
goal win = true
goal _ = false

mirror : Toy → Toy
mirror left = right
mirror right = left
mirror win = win
mirror lose = lose
mirror both = both

-- Choice indices differ between the mirrored roots. Fixed states retain
-- their evidence. This is an actual checked certificate transport function.
mirrorProof : ∀ s → Proven toy black goal (mirror s) → Proven toy black goal s
mirrorProof left proof = choice 0 leaf , refl
mirrorProof right proof = choice 1 leaf , refl
mirrorProof win proof = proof
mirrorProof lose proof = proof
mirrorProof both proof = proof

actToy : ℕ → Toy → Toy
actToy zero s = s
actToy (suc tag) s = mirror s

validTag : ℕ → Bool
validTag zero = true
validTag (suc zero) = true
validTag (suc (suc tag)) = false

transportToy : ∀ tag s → Proven toy black goal (actToy tag s) → Proven toy black goal s
transportToy zero s proof = proof
transportToy (suc tag) s proof = mirrorProof s proof

laws : CertificateTransport toy black goal
laws = record { act = actToy ; acceptedTag = validTag ; transport = transportToy }

eqToy : Toy → Toy → Bool
eqToy left left = true
eqToy right right = true
eqToy win win = true
eqToy lose lose = true
eqToy both both = true
eqToy _ _ = false

eqToy-sound : ∀ s t → eqToy s t ≡ true → s ≡ t
eqToy-sound left left e = refl
eqToy-sound left right ()
eqToy-sound left win ()
eqToy-sound left lose ()
eqToy-sound left both ()
eqToy-sound right left ()
eqToy-sound right right e = refl
eqToy-sound right win ()
eqToy-sound right lose ()
eqToy-sound right both ()
eqToy-sound win left ()
eqToy-sound win right ()
eqToy-sound win win e = refl
eqToy-sound win lose ()
eqToy-sound win both ()
eqToy-sound lose left ()
eqToy-sound lose right ()
eqToy-sound lose win ()
eqToy-sound lose lose e = refl
eqToy-sound lose both ()
eqToy-sound both left ()
eqToy-sound both right ()
eqToy-sound both win ()
eqToy-sound both lose ()
eqToy-sound both both e = refl

keys : Toy → List Bool
keys left = false ∷ false ∷ []
keys right = false ∷ true ∷ []
keys win = true ∷ false ∷ []
keys lose = true ∷ true ∷ false ∷ []
keys both = true ∷ true ∷ true ∷ []

toyKeyed : Keyed Toy
toyKeyed = keyed keys (record { equal = eqToy ; equal-sound = eqToy-sound })

entries : List (SharedEntry Toy)
entries = sharedEntry right (sharedChoice 1 sharedLeaf) ∷
          sharedEntry left (knownBy 1) ∷ []

valid-tag-citation : acceptSharedBy toyKeyed toy black goal laws entries left ≡ true
valid-tag-citation = refl

valid-tag-guarantee : Guarantees toy black goal left
valid-tag-guarantee = acceptSharedBy-sound toyKeyed toy black goal laws entries left valid-tag-citation

-- The source choice certificate cannot simply be reused at the target root.
source-choice-rejected-at-target : check toy black goal left (choice 1 leaf) ≡ false
source-choice-rejected-at-target = refl

transported-choice-checked :
  check toy black goal left (proj₁ (mirrorProof left (choice 1 leaf , refl))) ≡ true
transported-choice-checked = refl

sourceTable : Trie Toy
sourceTable = insertT (keys right) right tip

invalid-tag-rejected :
  checkSharedBy toyKeyed sourceTable toy black goal laws left (knownBy 2) ≡ false
invalid-tag-rejected = refl

-- Force a routing collision: full equality must still reject the wrong state.
wrongTable : Trie Toy
wrongTable = insertT (keys right) win tip

wrong-transformed-state-rejected :
  checkSharedBy toyKeyed wrongTable toy black goal laws left (knownBy 1) ≡ false
wrong-transformed-state-rejected = refl

exact-known-remains-exact :
  checkSharedBy toyKeyed sourceTable toy black goal laws left known ≡ false
exact-known-remains-exact = refl

exact-known-accepted :
  checkSharedBy toyKeyed sourceTable toy black goal laws right known ≡ true
exact-known-accepted = refl

old-checker-rejects-tagged-reference :
  checkShared toyKeyed sourceTable toy black goal left (knownBy 1) ≡ false
old-checker-rejects-tagged-reference = refl

self-citation-rejected :
  acceptSharedBy toyKeyed toy black goal laws (sharedEntry left (knownBy 0) ∷ []) left ≡ false
self-citation-rejected = refl

forward-citation-rejected :
  acceptSharedBy toyKeyed toy black goal laws
    (sharedEntry left (knownBy 1) ∷ sharedEntry right (sharedChoice 1 sharedLeaf) ∷ []) left ≡ false
forward-citation-rejected = refl

missing-and-reply-rejected :
  checkSharedBy toyKeyed tip toy black goal laws both (sharedFork (sharedLeaf ∷ [])) ≡ false
missing-and-reply-rejected = refl

all-and-replies-accepted :
  checkSharedBy toyKeyed tip toy black goal laws both (sharedFork (sharedLeaf ∷ sharedLeaf ∷ [])) ≡ true
all-and-replies-accepted = refl

decode-identity-tag : readShared 10 (primStringToList "R0;") ≡ just (knownBy 0 , [])
decode-identity-tag = refl

decode-last-tag : readShared 10 (primStringToList "R7;") ≡ just (knownBy 7 , [])
decode-last-tag = refl

decode-all-tags :
  readShared 10 (primStringToList "R1;") ≡ just (knownBy 1 , []) ×
  (readShared 10 (primStringToList "R2;") ≡ just (knownBy 2 , []) ×
  (readShared 10 (primStringToList "R3;") ≡ just (knownBy 3 , []) ×
  (readShared 10 (primStringToList "R4;") ≡ just (knownBy 4 , []) ×
  (readShared 10 (primStringToList "R5;") ≡ just (knownBy 5 , []) ×
   readShared 10 (primStringToList "R6;") ≡ just (knownBy 6 , [])))))
decode-all-tags = refl , (refl , (refl , (refl , (refl , refl))))

decode-invalid-tag : readShared 10 (primStringToList "R8;") ≡ nothing
decode-invalid-tag = refl

decode-invalid-large-tag : readShared 10 (primStringToList "R128;") ≡ nothing
decode-invalid-large-tag = refl

decode-missing-number : readShared 10 (primStringToList "R;") ≡ nothing
decode-missing-number = refl

decode-missing-terminator : readShared 10 (primStringToList "R1") ≡ nothing
decode-missing-terminator = refl

decode-preserves-known : readShared 10 (primStringToList "K") ≡ just (known , [])
decode-preserves-known = refl

decode-nested-tag :
  readShared 10 (primStringToList "C0;R1;") ≡ just (sharedChoice 0 (knownBy 1) , [])
decode-nested-tag = refl
