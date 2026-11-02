"""AI-assisted alternative proof layout; same finite arithmetic obligations."""
from itertools import product
from pathlib import Path
import row_arithmetic_source6 as original


def generate():
    old=original.generate();head=old.split('read-encode :',1)[0]
    lines=[head,'private']
    rows=list(product(original.CELLS,repeat=6))
    for index in range(6):
        fin=original.fin_pattern(index);name=f'read{index}'
        lines += [f'  {name} : ∀ row → read (Packed.encodeRow row) {fin} ≡ F.lookup row {fin}']
        lines += [f'  {name} {original.row_pattern(row)} = refl' for row in rows]
    for index in range(6):
        fin=original.fin_pattern(index)
        for k,cell in enumerate(original.CELLS):
            name=f'replace{index}-{k}'
            lines += [f'  {name} : ∀ row → replace (Packed.encodeRow row) {fin} {cell} ≡',
                      f'    Packed.encodeRow (F.updateAt row {fin} (λ _ → {cell}))']
            lines += [f'  {name} {original.row_pattern(row)} = refl' for row in rows]
    lines += ['', 'read-encode : ∀ (row : F.Vec Cell 6) (i : F.Fin 6) →',
              '  read (Packed.encodeRow row) i ≡ F.lookup row i']
    for index in range(6):
        lines += [f'read-encode row {original.fin_pattern(index)} = read{index} row']
    lines += ['', 'replace-encode : ∀ (row : F.Vec Cell 6) (i : F.Fin 6) (c : Cell) →',
              '  replace (Packed.encodeRow row) i c ≡',
              '  Packed.encodeRow (F.updateAt row i (λ _ → c))']
    for index in range(6):
        for k,cell in enumerate(original.CELLS):
            lines += [f'replace-encode row {original.fin_pattern(index)} {cell} = replace{index}-{k} row']
    source='\n'.join(lines)+'\n'
    assert sum(line.startswith('  read') and line.endswith('= refl') for line in lines)==4374
    assert sum(line.startswith('  replace') and line.endswith('= refl') for line in lines)==13122
    return source


if __name__=='__main__':
    original.TARGET.write_text(generate())
