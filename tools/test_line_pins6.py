"""All line edges transport legally; altered moves and scores are rejected."""
import copy
import json
from pathlib import Path
import unittest

import line_pins6 as pins
import ref


class LinePinTests(unittest.TestCase):
    def setUp(self):
        self.document=json.loads((Path(__file__).resolve().parents[1]/'certificates/six-line.json').read_text())

    def test_full_line_and_all_orientations(self):
        report=pins.plan(self.document)
        self.assertEqual(sum(map(len,report['pins'].values())),32)
        self.assertFalse(report['optimality_proved'])
        positions=[pins.state(k[1:],'black' if k[0]=='b' else 'white') for k in report['states']]
        for rows in report['pins'].values():
            for row in rows:
                s=positions[row['ply']]; child=positions[row['ply']+1]
                representative=pins.ccanonical(s)
                self.assertEqual(pins.encode_state(ref.successors(representative)[row['selected_index']]),row['chosen_state'])
                for tag in range(8):
                    actual=pins.image(s,tag); target=pins.image(child,tag)
                    self.assertIn(target,ref.successors(actual))
                    self.assertEqual(pins.ccanonical(actual),representative)
                    self.assertEqual(pins.encode_state(pins.ccanonical(target)),row['canonical_child'])

    def test_wrong_start_move_pass_or_score(self):
        changes=[lambda d:d['events'][0].update(index=999),
                 lambda d:d['events'][0].update(move='b2'),
                 lambda d:d['events'][30].update(move='d3'),
                 lambda d:d['states'].__setitem__(0,'b'+'1'*36),
                 lambda d:d['states'].__setitem__(-1,'w'+'2'*36)]
        for change in changes:
            document=copy.deepcopy(self.document); change(document)
            with self.assertRaises(ValueError): pins.plan(document)


if __name__=='__main__': unittest.main()
