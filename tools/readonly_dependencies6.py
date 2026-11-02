"""Run Agda with immutable borrowed dependencies and a private writable check root."""
from pathlib import Path
import json
import re
import shutil
from initial_shards_resume6 import argv
from wire_workflow6 import require


def command(machine, target, check, donor):
    check, donor = Path(check).resolve(), Path(donor).resolve()
    require(check != donor and donor not in check.parents and check not in donor.parents,
            'borrowed and writable roots must be disjoint')
    require(not any(p.is_symlink() for p in (check, donor)), 'real roots required')
    sandbox = shutil.which('bwrap')
    require(sandbox is not None, 'read-only mount sandbox unavailable')
    checker = argv(machine, target)
    checker[4:4] = ['-i', str(donor/'src')]
    return [sandbox, '--ro-bind', '/', '/', '--bind', str(check), str(check),
            '--proc', '/proc', '--dev-bind', '/dev', '/dev', '--tmpfs', '/tmp',
            '--die-with-parent', '--', *checker]


# Open original directories before hiding the duplicated source tree. Passing
# directory fds is essential: a later path bind would reopen the hidden tree.
# This exact launcher is exercised by the joint two-sided desktop pilot.
NAMESPACE_LAUNCHER = "import json,os,sys;args=json.loads(sys.argv[1]);root=sys.argv[2];paths=json.loads(sys.argv[3]);opts=['--tmpfs',root,'--dir',root+'/Tests'];fds=[os.open(p,os.O_RDONLY|os.O_DIRECTORY) for p in paths];[os.set_inheritable(fd,True) for fd in fds];[opts.extend(['--ro-bind-fd',str(fd),p]) for fd,p in zip(fds,paths)];opts.extend(['--remount-ro',root]);i=args.index('--');os.execv(args[0],args[:i]+opts+args[i:])"


def namespace_view(sandbox_command, source_root, prefixes):
    """Expose only selected Tests namespaces from a second immutable donor.

    Shared modules must be checked byte-identical by the caller, which must
    also hold all donor build locks and record their source/cache identities.
    Original absolute source and interface paths remain unchanged. The view
    exists only in the child mount namespace; no source/cache file is copied.
    The returned Python launcher execs bwrap, so record the checker hash too.
    """
    require(isinstance(sandbox_command, list) and sandbox_command
            and sandbox_command[1:5] == ['--ro-bind', '/', '/', '--bind']
            and sandbox_command.count('--') == 1,
            'existing read-only dependency command required')
    source = Path(source_root).absolute()
    require(source.name == 'src' and source == source.resolve()
            and not any(p.is_symlink() for p in (source, *source.parents)),
            'original nonsymlink source root required')
    private = Path(sandbox_command[5])
    require(private not in source.parents and source != private,
            'cannot mask the private writable check root')
    checker = sandbox_command[sandbox_command.index('--') + 1:]
    require(any(a == '-i' and b == str(source) for a, b in zip(checker, checker[1:])),
            'masked source must be an explicit dependency include root')
    require(isinstance(prefixes, (list, tuple)) and prefixes
            and all(isinstance(p, str) and re.fullmatch(r'Tests\.[A-Za-z][A-Za-z0-9_]*', p)
                    for p in prefixes) and len(set(prefixes)) == len(prefixes),
            'distinct direct Tests namespaces required')
    paths = [source / p.replace('.', '/') for p in prefixes]
    require(all(p.is_dir() and not any(q.is_symlink() for q in (p, *p.parents)) for p in paths),
            'original namespace directories required')
    return ['python3', '-c', NAMESPACE_LAUNCHER, json.dumps(sandbox_command),
            str(source), json.dumps([str(p) for p in paths])]
