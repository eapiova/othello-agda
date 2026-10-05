{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Game.Player where

open import Agda.Builtin.Bool using (Bool; true; false)

data Player : Set where
  black white : Player

other : Player → Player
other black = white
other white = black

samePlayer : Player → Player → Bool
samePlayer black black = true
samePlayer white white = true
samePlayer _ _ = false
