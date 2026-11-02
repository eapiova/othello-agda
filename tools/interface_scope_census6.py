"""Read-only typed container counts for Agda cb568525 scope serialization.

This does not traverse arbitrary words as pointers or rewrite interfaces. Sizes
describe identified serialized containers, not exclusive attribution or RAM.
Schema: Interface[7]: ScopeInfo; ScopeInfo[1]: Map ModuleName Scope;
Scope = 5 fields, Scope[2]: [(NameSpaceId, NameSpace)], Scope[3]: import map;
NameSpace = 4 fields, its first three fields are name/name-part/module maps.
See that commit's Serialise/Instances{,/Abstract,/General}.hs and Scope/Base.hs.
"""
from interface_census6 import node_array


def scope_fields(payload):
    root, nodes, _ = node_array(payload)
    containers = set()

    def node(index, arity=None):
        if not 0 <= index < len(nodes):
            raise ValueError('scope node outside serialized array')
        value = nodes[index]
        if arity is not None and len(value) != arity:
            raise ValueError('unexpected typed scope record')
        containers.add(index)
        return value

    def pairs(index):
        value = node(index)
        if len(value) % 2:
            raise ValueError('malformed serialized scope map')
        return list(zip(value[::2], value[1::2]))

    inside = node(nodes[root][7], 5)
    scopes = pairs(inside[1])
    imports = names = name_parts = modules = namespaces = 0
    rows = []
    for _, index in scopes:
        scope = node(index, 5)
        import_count = len(pairs(scope[3]))
        imports += import_count
        row = dict(namespace_name_keys=0, namespace_name_part_keys=0,
                   namespace_module_keys=0, imports=import_count)
        tags = []
        for entry in node(scope[2]):
            tag, namespace_index = node(entry, 2)
            if tag not in (0, 1, 2) or tag in tags:
                raise ValueError('unexpected or duplicate namespace ID')
            tags.append(tag)
            namespace = node(namespace_index, 4)
            for field, label in enumerate(('namespace_name_keys',
                                            'namespace_name_part_keys',
                                            'namespace_module_keys')):
                row[label] += len(pairs(namespace[field]))
            namespaces += 1
        names += row['namespace_name_keys']
        name_parts += row['namespace_name_part_keys']
        modules += row['namespace_module_keys']
        rows.append(row)
    return dict(scope_modules=len(scopes), scope_namespaces=namespaces,
                scope_import_keys=imports, scope_name_keys=names,
                scope_name_part_keys=name_parts, scope_module_keys=modules,
                identified_scope_container_nodes=len(containers),
                identified_scope_container_encoded_bytes=sum(8 + 4 * len(nodes[i])
                                                             for i in containers),
                largest_scope_name_key_counts=sorted((r['namespace_name_keys']
                                                      for r in rows), reverse=True)[:8],
                attribution='Typed container counts only; containers can be shared with other fields. No whole-field byte or RAM attribution.')
