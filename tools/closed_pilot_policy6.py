"""One user-approved 80-GiB exception; normal study gates stay unchanged."""
LABEL = 'initial-lower-global-closed-20261015'
RETRY_LABEL = 'initial-lower-global-closed-retry-20261015'
FLAG = '--closed-lookup-80g-20261015'
NARROW_LABEL = 'initial-lower-global-narrow-20261015'
NARROW_FLAG = '--narrow-routes-80g-20261015'
MODULE_LABEL = 'initial-lower-global-module-20261016'
MODULE_UPPER_LABEL = 'initial-upper-global-module-20261016'
MODULE_FLAG = '--module-imports-80g-20261016'


FULL_MAP_FLAG = '--approved-full-map6-20261016'
FULL_MAP_PHASES = {
    'full-map-lower-native-20261016': ('native', 1000, 8.25),
    'full-map-lower-generate-20261016': ('generate', 240, 1),
    'full-map-lower-check-20261016': ('check', 2400, 11.5),
    'full-map-lower-alignment-20261016': ('align', 1120, 11.5),
    'full-map-lower-row-link-20261016': ('rowlink', 285, 11.5),
}


def full_map_exception(label, command, cpu_limit, rss_limit_gib, *, smoke=False):
    if FULL_MAP_FLAG not in command:
        return False
    require = FULL_MAP_PHASES.get(label)
    if (smoke or require is None or command[:2] != ['python3', 'tools/full_map_pilot6.py']
            or command != ['python3', 'tools/full_map_pilot6.py', '--phase', require[0], FULL_MAP_FLAG]
            or command.count(FULL_MAP_FLAG) != 1 or command.count('--phase') != 1
            or command.index('--phase')+1 >= len(command)
            or command[command.index('--phase')+1] != require[0]
            or not 0 < cpu_limit <= require[1] or not 0 < rss_limit_gib <= require[2]):
        raise ValueError('invalid approved full-map pilot resource exception')
    return True


def artifact_cap_gib(label, command, cpu_limit, rss_limit_gib, *, smoke=False):
    return 12 if full_map_exception(label, command, cpu_limit, rss_limit_gib, smoke=smoke) else 10


def free_disk_gib(label, command, cpu_limit, rss_limit_gib, *, smoke=False):
    if full_map_exception(label, command, cpu_limit, rss_limit_gib, smoke=smoke):
        return 80
    flags = [f for f in (FLAG, NARROW_FLAG, MODULE_FLAG) if f in command]
    if not flags:
        return 100
    flag = flags[0]
    labels = (LABEL, RETRY_LABEL) if flag == FLAG else (NARROW_LABEL,) if flag == NARROW_FLAG else (MODULE_LABEL, MODULE_UPPER_LABEL)
    side = 'upper' if flag == MODULE_FLAG and label == MODULE_UPPER_LABEL else 'lower'
    output = 'results/initial-' + side + '-global-' + ('closed6' if flag == FLAG else 'narrow6' if flag == NARROW_FLAG else 'module6')
    if (len(flags) != 1 or smoke or label not in labels or command[:2] != ['python3', 'tools/initial_direct_pilot6.py']
            or command.count(flag) != 1 or '--smoke' in command
            or not 0 < cpu_limit <= 290 or not 0 < rss_limit_gib <= 2.75):
        raise ValueError('invalid one-off closed pilot resource exception')
    for key, value in (('--side', side), ('--output', output)):
        if command.count(key) != 1 or command.index(key) + 1 >= len(command) or command[command.index(key) + 1] != value:
            raise ValueError('one-off closed pilot command differs')
    return 80


def same_compiler_after_reboot(prior, current):
    """A new boot is not a different machine/compiler; reject every other change."""
    keys = {'hostname', 'boot_id', 'agda_path', 'agda_sha256', 'agda_version'}
    return (set(prior) == set(current) == keys and all(prior[k] == current[k]
            for k in keys - {'boot_id'}) and all(isinstance(m['boot_id'], str)
            and bool(m['boot_id']) for m in (prior, current)))
