{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}
-- AI-assisted data/proofs; global ownership remains explicit.
module Tests.TextUpperPacked6.Group653 where
open import Agda.Builtin.String using (String)
import Othello.TextStateMap6 as T
t32650 : String
t32650 = "Bɑ͟͢ϗ̣˦W˥ɱλʹʑɬWĂȇʔʾɭɣWʗɘˊʾɭɬWɅͬɯʒǳĀWǴƁʃǲĀĀWāǤıƟĀĀWěǏžĭĀĀBĀďĪŎĀĀWĀĀĭŵĀĀBĀĀĭĿĀĀ"
table : T.Map
table = (T.rows 6530000 11 t32650)
