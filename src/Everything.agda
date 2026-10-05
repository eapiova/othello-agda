{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Everything where

import Prelude
import Game.Player
import Game.Core
import Game.Certificate
import Game.Soundness
import Othello.Finite
import Othello.Counting
import Othello.Order
import Othello.Board
import Othello.Rules
import Othello.Correctness
import Othello.Termination
import Othello.Statements
import Othello.Generated4
import Othello.Proof4
import Othello.Value
import Tests.Rules
import Tests.Perft
import Tests.DeepPerft
import Tests.PerfectLine
import Tests.Certificates
