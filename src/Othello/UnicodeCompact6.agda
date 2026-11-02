{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted strict parser. No solver claims are imported as proofs.
module Othello.UnicodeCompact6 where

open import Prelude
open import Agda.Builtin.String using (String; primStringToList)
open import Agda.Builtin.Char using (Char; primCharToNat)
open import Agda.Builtin.Nat using (_+_; _-_; _*_; _<_) renaming (_==_ to _≡ᵇ_)
open import Othello.Board using (Coord; six)
import Othello.Finite as F
import Game.Balanced as B
import Game.DirectedIndexed as D
open import Othello.Order using (_≤ᵇ_)

Certificate : Set
Certificate = D.DirectedCertificate ℕ (Coord six)

private
  readCode : ℕ → List Char → Maybe (ℕ × List Char)
  readCode bound [] = nothing
  readCode bound (c ∷ cs) with primCharToNat c < 256
  ... | true = nothing
  ... | false with (primCharToNat c - 256) ≤ᵇ bound
  ...   | false = nothing
  ...   | true = just ((primCharToNat c - 256) , cs)

  readWord : ℕ → List Char → Maybe (ℕ × List Char)
  readWord bound [] = nothing
  readWord bound (c ∷ cs) with primCharToNat c < 16384
  ... | true = nothing
  ... | false with (primCharToNat c - 16384) < bound
  ...   | false = nothing
  ...   | true = just ((primCharToNat c - 16384) , cs)

  readKey : List Char → Maybe (ℕ × List Char)
  readKey cs with readWord 19532 cs
  ... | nothing = nothing
  ... | just (hi , tail) with readWord 1024 tail
  ...   | nothing = nothing
  ...   | just (lo , rest) with (1024 * hi + lo) < 20000000
  ...     | false = nothing
  ...     | true = just ((1024 * hi + lo) , rest)

  length : ∀ {A : Set} → List A → ℕ
  length [] = zero
  length (_ ∷ xs) = suc (length xs)

coordinate : ℕ → Coord six
coordinate 0 = F.zero , F.zero
coordinate 1 = F.zero , (F.suc F.zero)
coordinate 2 = F.zero , (F.suc (F.suc F.zero))
coordinate 3 = F.zero , (F.suc (F.suc (F.suc F.zero)))
coordinate 4 = F.zero , (F.suc (F.suc (F.suc (F.suc F.zero))))
coordinate 5 = F.zero , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))
coordinate 6 = (F.suc F.zero) , F.zero
coordinate 7 = (F.suc F.zero) , (F.suc F.zero)
coordinate 8 = (F.suc F.zero) , (F.suc (F.suc F.zero))
coordinate 9 = (F.suc F.zero) , (F.suc (F.suc (F.suc F.zero)))
coordinate 10 = (F.suc F.zero) , (F.suc (F.suc (F.suc (F.suc F.zero))))
coordinate 11 = (F.suc F.zero) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))
coordinate 12 = (F.suc (F.suc F.zero)) , F.zero
coordinate 13 = (F.suc (F.suc F.zero)) , (F.suc F.zero)
coordinate 14 = (F.suc (F.suc F.zero)) , (F.suc (F.suc F.zero))
coordinate 15 = (F.suc (F.suc F.zero)) , (F.suc (F.suc (F.suc F.zero)))
coordinate 16 = (F.suc (F.suc F.zero)) , (F.suc (F.suc (F.suc (F.suc F.zero))))
coordinate 17 = (F.suc (F.suc F.zero)) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))
coordinate 18 = (F.suc (F.suc (F.suc F.zero))) , F.zero
coordinate 19 = (F.suc (F.suc (F.suc F.zero))) , (F.suc F.zero)
coordinate 20 = (F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc F.zero))
coordinate (suc 20) = (F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc (F.suc F.zero)))
coordinate (suc (suc 20)) = (F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc (F.suc (F.suc F.zero))))
coordinate (suc (suc (suc 20))) = (F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))
coordinate (suc (suc (suc (suc 20)))) = (F.suc (F.suc (F.suc (F.suc F.zero)))) , F.zero
coordinate (suc (suc (suc (suc (suc 20))))) = (F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc F.zero)
coordinate (suc (suc (suc (suc (suc (suc 20)))))) = (F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc F.zero))
coordinate (suc (suc (suc (suc (suc (suc (suc 20))))))) = (F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc (F.suc F.zero)))
coordinate (suc (suc (suc (suc (suc (suc (suc (suc 20)))))))) = (F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc (F.suc (F.suc F.zero))))
coordinate (suc (suc (suc (suc (suc (suc (suc (suc (suc 20))))))))) = (F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))
coordinate (suc (suc (suc (suc (suc (suc (suc (suc (suc (suc 20)))))))))) = (F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , F.zero
coordinate (suc (suc (suc (suc (suc (suc (suc (suc (suc (suc (suc 20))))))))))) = (F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc F.zero)
coordinate (suc (suc (suc (suc (suc (suc (suc (suc (suc (suc (suc (suc 20)))))))))))) = (F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc F.zero))
coordinate (suc (suc (suc (suc (suc (suc (suc (suc (suc (suc (suc (suc (suc 20))))))))))))) = (F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc (F.suc F.zero)))
coordinate (suc (suc (suc (suc (suc (suc (suc (suc (suc (suc (suc (suc (suc (suc 20)))))))))))))) = (F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc (F.suc (F.suc F.zero))))
coordinate (suc (suc (suc (suc (suc (suc (suc (suc (suc (suc (suc (suc (suc (suc (suc 20))))))))))))))) = (F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))
coordinate _ = F.zero , F.zero

private
  classify : Char → ℕ
  classify c with primCharToNat c < 65
  ... | true = 8
  ... | false = primCharToNat c - 65

mutual
  read : ℕ → List Char → Maybe (Certificate × List Char)
  read zero cs = nothing
  read (suc fuel) [] = nothing
  read (suc fuel) (c ∷ cs) with classify c
  ... | 0 = just (D.indexedLeaf , cs)
  read (suc fuel) (c ∷ cs) | 1 with readKey cs
  ... | nothing = nothing
  ... | just (i , rest) = just (D.cite i , rest)
  read (suc fuel) (c ∷ cs) | 2 with readCode 7 cs
  ... | nothing = nothing
  ... | just (tag , tail) with readKey tail
  ...   | nothing = nothing
  ...   | just (i , rest) = just (D.citeBy tag i , rest)
  read (suc fuel) (c ∷ cs) | 3 with readCode 128 cs
  ... | nothing = nothing
  ... | just (n , rest) = just (D.indexedSolve n , rest)
  read (suc fuel) (c ∷ cs) | 4 with read fuel cs
  ... | nothing = nothing
  ... | just (x , rest) = just (D.indexedPass x , rest)
  read (suc fuel) (c ∷ cs) | 5 with readCode 35 cs
  ... | nothing = nothing
  ... | just (i , tail) with read fuel tail
  ...   | nothing = nothing
  ...   | just (x , rest) = just (D.indexedChoice i x , rest)
  read (suc fuel) (c ∷ cs) | 6 with readCode 35 cs
  ... | nothing = nothing
  ... | just (i , tail) with read fuel tail
  ...   | nothing = nothing
  ...   | just (x , rest) = just (D.indexedPick (coordinate i) x , rest)
  read (suc fuel) (c ∷ cs) | 7 with readCode 36 cs
  ... | nothing = nothing
  ... | just (n , tail) with reads fuel n tail
  ...   | nothing = nothing
  ...   | just (xs , rest) = just (D.indexedFork xs , rest)
  read (suc fuel) (c ∷ cs) | _ = nothing

  reads : ℕ → ℕ → List Char → Maybe (List Certificate × List Char)
  reads fuel zero cs = just ([] , cs)
  reads zero (suc n) cs = nothing
  reads (suc fuel) (suc n) cs with read fuel cs
  ... | nothing = nothing
  ... | just (x , tail) with reads fuel n tail
  ...   | nothing = nothing
  ...   | just (xs , rest) = just (x ∷ xs , rest)

private
  readBodies : ℕ → (n : ℕ) → List Char → Maybe (B.Vec Certificate n × List Char)
  readBodies fuel zero cs = just (B.nil , cs)
  readBodies fuel (suc n) cs with read fuel cs
  ... | nothing = nothing
  ... | just (x , tail) with readBodies fuel n tail
  ...   | nothing = nothing
  ...   | just (xs , rest) = just (B.cons x xs , rest)

  replicate : (n : ℕ) → B.Vec Certificate n
  replicate zero = B.nil
  replicate (suc n) = B.cons D.indexedLeaf (replicate n)

decodeBodies : (n : ℕ) → String → Maybe (B.Vec Certificate n)
decodeBodies n text with readBodies (suc (2 * length (primStringToList text))) n (primStringToList text)
... | just (cs , []) = just cs
... | _ = nothing

bodies : (n : ℕ) → String → B.Vec Certificate n
bodies n text = fromMaybe (replicate n) (decodeBodies n text)
