{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted strict parser. No solver claims are imported as proofs.
module Othello.DirectedCompact6 where

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
  rankNat : ℕ → Maybe ℕ
  rankNat n with n < 48
  ... | true = nothing
  ... | false with n < 58
  ...   | true = just (n - 48)
  ...   | false with n < 65
  ...     | true = nothing
  ...     | false with n < 91
  ...       | true = just (10 + (n - 65))
  ...       | false with n ≡ᵇ 95
  ...         | true = just 36
  ...         | false = nothing

  readCode : ℕ → List Char → Maybe (ℕ × List Char)
  readCode bound [] = nothing
  readCode bound (c ∷ cs) with rankNat (primCharToNat c)
  ... | nothing = nothing
  ... | just n with n ≤ᵇ bound
  ...   | false = nothing
  ...   | true = just (n , cs)

  idTail : ℕ → Bool → List Char → Maybe (ℕ × List Char)
  idTail n seen [] = nothing
  idTail n seen (c ∷ cs) with primCharToNat c ≡ᵇ 59
  ... | true with seen
  ...   | true = just (n , cs)
  ...   | false = nothing
  idTail n seen (c ∷ cs) | false with rankNat (primCharToNat c)
  ... | nothing = nothing
  ... | just d with (37 * n + d) < 20000000
  ...   | false = nothing
  ...   | true = idTail (37 * n + d) true cs

  numberTail : ℕ → Bool → List Char → Maybe (ℕ × List Char)
  numberTail n seen [] = nothing
  numberTail n seen (c ∷ cs) with primCharToNat c ≡ᵇ 59
  ... | true with seen
  ...   | true = just (n , cs)
  ...   | false = nothing
  numberTail n seen (c ∷ cs) | false with rankNat (primCharToNat c)
  ... | nothing = nothing
  ... | just d with d < 10
  ...   | false = nothing
  ...   | true with (10 * n + d) ≤ᵇ 128
  ...     | false = nothing
  ...     | true = numberTail (10 * n + d) true cs

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
  classify c with primCharToNat c ≡ᵇ 76
  ... | true = 0
  ... | false with primCharToNat c ≡ᵇ 75
  ... | true = 1
  ... | false with primCharToNat c ≡ᵇ 82
  ... | true = 2
  ... | false with primCharToNat c ≡ᵇ 83
  ... | true = 3
  ... | false with primCharToNat c ≡ᵇ 80
  ... | true = 4
  ... | false with primCharToNat c ≡ᵇ 67
  ... | true = 5
  ... | false with primCharToNat c ≡ᵇ 81
  ... | true = 6
  ... | false with primCharToNat c ≡ᵇ 70
  ... | true = 7
  ... | false = 8

mutual
  read : ℕ → List Char → Maybe (Certificate × List Char)
  read zero cs = nothing
  read (suc fuel) [] = nothing
  read (suc fuel) (c ∷ cs) with classify c
  ... | 0 = just (D.indexedLeaf , cs)
  read (suc fuel) (c ∷ cs) | 1 with idTail 0 false cs
  ... | nothing = nothing
  ... | just (i , rest) = just (D.cite i , rest)
  read (suc fuel) (c ∷ cs) | 2 with readCode 7 cs
  ... | nothing = nothing
  ... | just (tag , tail) with idTail 0 false tail
  ...   | nothing = nothing
  ...   | just (i , rest) = just (D.citeBy tag i , rest)
  read (suc fuel) (c ∷ cs) | 3 with numberTail 0 false cs
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
