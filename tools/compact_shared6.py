#!/usr/bin/env python3
"""AI-assisted, untrusted compact 6x6 shared-certificate wire codec.

Invalid input raises ValueError. This module changes representation only;
decoded entries still require the safe Agda SharedCertificate checker.
"""
from __future__ import annotations

TRIPLES = '0123456789ABCDEFGHIJKLMNOPQ'
COUNTS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_'


def pack_state(state_or_rawkey):
    """Pack a ref.State or a player-prefixed 37-character ternary key."""
    if isinstance(state_or_rawkey, str):
        raw = state_or_rawkey
    else:
        state = state_or_rawkey
        try:
            if (state.size != 6 or len(state.cells) != 36
                    or type(state.turn) is not int or state.turn not in (1, 2)
                    or any(type(c) is not int or c not in (0, 1, 2) for c in state.cells)):
                raise ValueError('invalid 6x6 state')
            raw = ('b' if state.turn == 1 else 'w') + ''.join(map(str, state.cells))
        except (AttributeError, TypeError) as error:
            raise ValueError('invalid 6x6 state') from error
    if len(raw) != 37 or raw[0] not in 'bw' or any(c not in '012' for c in raw[1:]):
        raise ValueError('invalid raw state key')
    cells = raw[1:]
    return raw[0] + ''.join(TRIPLES[9 * int(cells[i]) + 3 * int(cells[i + 1])
                                   + int(cells[i + 2])] for i in range(0, 36, 3))


def unpack_state(packed):
    """Decode exactly one 13-character compact state to its raw key."""
    if (not isinstance(packed, str) or len(packed) != 13 or packed[0] not in 'bw'
            or any(c not in TRIPLES for c in packed[1:])):
        raise ValueError('invalid compact state key')
    values = (TRIPLES.index(c) for c in packed[1:])
    return packed[0] + ''.join(f'{v // 9}{(v // 3) % 3}{v % 3}' for v in values)


def _decimal(text, offset):
    start, number = offset, 0
    while offset < len(text) and text[offset] in '0123456789':
        number = 10 * number + int(text[offset])
        if number > 128:
            raise ValueError('certificate number exceeds 128')
        offset += 1
    if offset == start or offset == len(text) or text[offset] != ';':
        raise ValueError('invalid decimal certificate number')
    return number, offset + 1


def _certificate(text, compact):
    if not isinstance(text, str):
        raise ValueError('certificate must be text')
    # Each node consumes one outstanding child slot. The iterative parser avoids
    # a recursion limit for deeply nested, otherwise valid pass/choice trees.
    offset, pending, output = 0, 1, []
    while pending:
        if offset == len(text):
            raise ValueError('truncated certificate')
        token = text[offset]
        offset += 1
        pending -= 1
        output.append(token)
        if token in 'LK':
            continue
        if token == 'P':
            pending += 1
            continue
        if token not in 'RCFS':
            raise ValueError('unknown certificate token')
        if compact and token != 'S':
            alphabet = '01234567' if token == 'R' else COUNTS
            if offset == len(text) or text[offset] not in alphabet:
                raise ValueError('invalid compact certificate number')
            number = alphabet.index(text[offset])
            offset += 1
        else:
            number, offset = _decimal(text, offset)
        if ((token == 'R' and number > 7) or (token == 'C' and number >= 36)
                or (token == 'F' and number > 36)):
            raise ValueError('certificate tag/count out of range')
        if compact:
            output.append(f'{number};')
        elif token == 'S':
            output.append(f'{number};')
        else:
            output.append(('01234567' if token == 'R' else COUNTS)[number])
        if token == 'C':
            pending += 1
        elif token == 'F':
            pending += number
    if offset != len(text):
        raise ValueError('trailing certificate data')
    return ''.join(output)


def pack_certificate(oldtext):
    """Pack exactly one certificate in the existing decimal/semicolon grammar."""
    return _certificate(oldtext, compact=False)


def unpack_certificate(compacttext):
    """Unpack exactly one compact certificate to the existing grammar."""
    return _certificate(compacttext, compact=True)


def encode(entries):
    """Concatenate (state, old-grammar certificate) entries in their given order."""
    return ''.join(pack_state(state) + pack_certificate(text) for state, text in entries)
