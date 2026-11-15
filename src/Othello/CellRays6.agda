{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Othello.CellRays6 where

open import Prelude
open import Othello.Rules using
  ( Board; Player; State; Coord; Cell; Direction; six
  ; at; board; toMove; sameCell; playerCell; other
  ; directions; concatMap
  )
import Othello.Rules as Rules
import Othello.Fast6 as Fast6
open import Othello.Rays6 using (ray6)

cells : Board six → List (Coord six) → List (Coord six × Cell)
cells b qs = map (λ q → q , at {six} b q) qs

scanCells : Player → List (Coord six × Cell) → Maybe (List (Coord six))
scanCells p [] = nothing
scanCells p ((q , c) ∷ qs) =
  Rules.scanStep {six} p q c (scanCells p qs)

scanCells-correct : ∀ b p qs →
  scanCells p (cells b qs) ≡ Rules.scan {six} b p qs
scanCells-correct b p [] = refl
scanCells-correct b p (q ∷ qs)
  rewrite scanCells-correct b p qs = refl

capturesCells : Player → List (Coord six × Cell) → List (Coord six)
capturesCells p [] = []
capturesCells p ((r , c) ∷ rs) with sameCell c (playerCell (other p))
... | false = []
... | true with scanCells p rs
... | nothing = []
... | just xs = r ∷ xs

capturesCells-correct : ∀ b p qs →
  capturesCells p (cells b qs) ≡ Fast6.capturesOn b p qs
capturesCells-correct b p [] = refl
capturesCells-correct b p (r ∷ rs)
  with sameCell (at {six} b r) (playerCell (other p))
... | false = refl
... | true rewrite scanCells-correct b p rs
  with Rules.scan {six} b p rs
... | nothing = refl
... | just xs = refl

capturesRays : Player → List (List (Coord six × Cell)) → List (Coord six)
capturesRays p rays = concatMap (capturesCells p) rays

raysAt : State six → Coord six → List (List (Coord six × Cell))
raysAt s q =
  map (λ d → cells (board s) (ray6 d q)) directions

capturesRays-directions-correct : ∀ b p q ds →
  capturesRays p (map (λ d → cells b (ray6 d q)) ds) ≡
  concatMap (λ d → Fast6.captures6 b p d q) ds
capturesRays-directions-correct b p q [] = refl
capturesRays-directions-correct b p q (d ∷ ds)
  rewrite capturesCells-correct b p (ray6 d q)
        | capturesRays-directions-correct b p q ds = refl

capturesRays-correct : ∀ s q →
  capturesRays (toMove s) (raysAt s q) ≡ Fast6.allCaptures6 s q
capturesRays-correct s q =
  capturesRays-directions-correct (board s) (toMove s) q directions
