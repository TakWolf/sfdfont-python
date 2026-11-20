import re

from sfdfont._glyph_layout import GLYPH_LAYOUT_KEYS
from sfdfont._glyph_layout import decode as decode_glyph_layout
from sfdfont._layout import AAT_KEYS, CONTEXT_KEYS, KERN_CLASS_KEYS
from sfdfont._legacy_layout import LEGACY_KERN_KEYS, LEGACY_PST_KEYS, decode_anchor_classes, decode_pairs, decode_pst
from sfdfont._reader import Reader
from sfdfont.aat import SfdStateMachine
from sfdfont.error import SfdParseError, SfdValidationError
from sfdfont.glyph_layout import SfdAnchorClasses
from sfdfont.layout import SfdContext, SfdKerningClass, SfdLookup


def need(condition: bool, message: str) -> None:
    if not condition:
        raise SfdValidationError(message)


def glyph_records(font):
    glyphs = list(font.iter_glyphs())
    for glyph in glyphs:
        yield from glyph.records
        for layer in glyph.layers:
            yield from layer.records


def validate_layout(font) -> None:
    from sfdfont._baselines import validate_baselines
    from sfdfont._validation import cycles

    try:
        validate_baselines(font)
        lookups = [SfdLookup.from_record(r) for r in font.metadata.records if r.keyword == 'Lookup:']
        contexts = [SfdContext.from_record(r) for r in font.metadata.records if r.keyword in CONTEXT_KEYS]
        kerns = [SfdKerningClass.from_record(r) for r in font.metadata.records if r.keyword in KERN_CLASS_KEYS]
        machines = [SfdStateMachine.from_record(r) for r in font.metadata.records if r.keyword in AAT_KEYS]
        from sfdfont._marks import validate_marks

        legacy_psts = []
        legacy_flags = []
        for record in glyph_records(font):
            if record.keyword in LEGACY_PST_KEYS:
                value = decode_pst(record)
                legacy_psts.append(value)
                legacy_flags.append(value.binding.flags or 0)
            elif record.keyword in LEGACY_KERN_KEYS:
                legacy_flags.extend(pair.flags or 0 for pair in decode_pairs(record).pairs)
        for record in font.metadata.records:
            if record.keyword == 'AnchorClass:':
                legacy_flags.extend(item.flags or 0 for item in decode_anchor_classes(record).classes)
        validate_marks(font, lookups, contexts, legacy_flags)
        lookup_names = {}
        subtables = {}
        for lookup in lookups:
            need(lookup.name not in lookup_names, f'duplicate lookup name {lookup.name!r}')
            lookup_names[lookup.name] = lookup
            for sub in lookup.subtables:
                need(sub.name not in subtables, f'duplicate subtable name {sub.name!r}')
                subtables[sub.name] = lookup
        glyphs = list(font.iter_glyphs())
        names = {glyph.name for glyph in glyphs}

        def members(values):
            for value in values:
                if isinstance(value, list):
                    yield from value
                elif isinstance(value, str):
                    yield value

        def check_names(values):
            for name in members(values):
                need(name in names, f'unknown glyph {name!r} in layout')

        definitions = {c.tag for c in contexts if c.tag is not None}
        for record in font.metadata.records:
            if record.keyword == 'GenTags:':
                definitions.update(tag.decode('ascii') for tag in re.findall(rb"'(.{4})'", record.value))
        for value in legacy_psts:
            if value.keyword != 'LCarets:':
                if isinstance(value.binding.tag, str):
                    definitions.add(value.binding.tag)
                elif value.binding.tag is None:
                    definitions.add('liga')
        graph = {name: [] for name in lookup_names}
        used = set()

        def subtable(name, kinds):
            need(name in subtables, f'undefined layout subtable {name!r}')
            owner = subtables[name]
            need(owner.lookup_type in kinds, f'lookup type mismatch for subtable {name!r}')
            return owner

        kinds = {'ContextSub2:': 5, 'ChainSub2:': 6, 'ReverseChain2:': 8, 'ContextPos2:': 263, 'ChainPos2:': 264}
        for context in contexts:
            for group in (context.input_classes, context.backtrack_classes, context.lookahead_classes):
                check_names(group)
            if context.subtable is not None:
                owner = subtable(context.subtable, {kinds[context.keyword]})
                need(context.subtable not in used, 'multiple layout blocks for one subtable')
                used.add(context.subtable)
                source = owner.name
            else:
                source = context.tag
            for rule in context.rules:
                for group in (rule.inputs, rule.backtrack, rule.lookahead):
                    check_names(group)
                check_names(rule.replacements or [])
                if context.form == 'revcov':
                    need(
                        bool(rule.inputs) and len(rule.inputs[0]) == len(rule.replacements or []),
                        'reverse substitution coverage/replacement count mismatch',
                    )
                for action in rule.lookups:
                    if action.lookup is None:
                        continue
                    if context.subtable is not None:
                        need(action.lookup in lookup_names, f'undefined nested lookup {action.lookup!r}')
                        target = lookup_names[action.lookup]
                        need(
                            (target.lookup_type < 256) == (owner.lookup_type < 256),
                            'cannot mix GSUB and GPOS nested lookups',
                        )
                    else:
                        need(action.lookup in definitions, f'undefined nested lookup tag {action.lookup!r}')
                    if source is not None:
                        graph.setdefault(source, []).append(action.lookup)
        machine_types = {
            'MacIndic': 253,
            'MacContext': 254,
            'MacInsert': 255,
            'MacKern': 511,
            'MacLigature': 4,
            'MacSimple': 1,
        }
        for machine in machines:
            for group in machine.classes[4:]:
                check_names(group)
            source = None
            if machine.subtable is not None:
                kind = machine_types[machine.keyword.removesuffix('2:')]
                owner = subtable(machine.subtable, {kind})
                need(machine.subtable not in used, 'multiple layout blocks for one subtable')
                used.add(machine.subtable)
                source = owner.name
            for row in machine.states:
                for state in row:
                    check_names(state.mark_insert)
                    check_names(state.current_insert)
                    for target in (state.mark_lookup, state.current_lookup):
                        if target is None:
                            continue
                        if source is not None:
                            need(target in lookup_names, f'undefined nested AAT lookup {target!r}')
                            need(lookup_names[target].lookup_type < 256, 'AAT context requires substitution lookup')
                            graph[source].append(target)
                        else:
                            need(target in definitions, f'undefined nested AAT lookup tag {target!r}')
        cycles(graph, 'layout')
        for record in font.metadata.records:
            if record.keyword == 'Justify:':
                from sfdfont._extended import read_justify

                extender_glyphs, jstf_lookups = read_justify(Reader(record.value))
                check_names(extender_glyphs)
                for target, maximum in jstf_lookups:
                    need(target in lookup_names, f'undefined JSTF lookup {target!r}')
                    need(not maximum or lookup_names[target].lookup_type >= 256, 'JSTF maximum requires GPOS lookup')
        for kern in kerns:
            check_names(kern.first_classes)
            check_names(kern.second_classes)
            if kern.subtable is not None:
                owner = subtable(kern.subtable, {258})
                need(kern.subtable not in used, 'multiple layout blocks for one subtable')
                used.add(kern.subtable)
                definition = next(sub for sub in owner.subtables if sub.name == kern.subtable)
                need(bool(definition.vertical) == kern.keyword.startswith('V'), 'kerning direction mismatch')
        modern_pst = {
            'Substitution2:': 1,
            'MultipleSubs2:': 2,
            'AlternateSubs2:': 3,
            'Ligature2:': 4,
            'Position2:': 257,
            'PairPos2:': 258,
        }
        gids = {glyph.glyph_id for glyph in glyphs}
        anchors = set()
        for record in font.metadata.records:
            if record.keyword == 'AnchorClass2:':
                for anchor in SfdAnchorClasses.from_record(record).classes:
                    if anchor.subtable:
                        subtable(anchor.subtable, {259, 260, 261, 262})
                    need(anchor.name not in anchors, 'duplicate anchor class name')
                    anchors.add(anchor.name)
            elif record.keyword == 'AnchorClass:':
                for anchor in decode_anchor_classes(record).classes:
                    need(anchor.name not in anchors, 'duplicate anchor class name')
                    anchors.add(anchor.name)
        for record in glyph_records(font):
            value = decode_glyph_layout(record, GLYPH_LAYOUT_KEYS) if record.keyword in GLYPH_LAYOUT_KEYS else None
            if record.keyword in modern_pst:
                subtable(value.subtable, {modern_pst[record.keyword]})
                if record.keyword in ('Substitution2:', 'MultipleSubs2:', 'AlternateSubs2:', 'Ligature2:'):
                    check_names(value.glyphs)
                elif record.keyword == 'PairPos2:':
                    check_names([value.glyph])
            elif record.keyword in ('Kerns2:', 'VKerns2:'):
                for pair in value.pairs:
                    need(pair.target in gids, 'dangling kerning glyph ID')
                    owner = subtable(pair.subtable, {258})
                    definition = next(sub for sub in owner.subtables if sub.name == pair.subtable)
                    need(bool(definition.vertical) == record.keyword.startswith('V'), 'kerning pair direction mismatch')
            elif record.keyword == 'AnchorPoint:':
                need(value.name in anchors, f'undefined anchor class {value.name!r}')
    except (SfdParseError, UnicodeError) as error:
        raise SfdValidationError(str(error)) from error


def layout_identity(font):
    """Names remain fixed while references in uninterpreted records are retained."""
    result = []
    for record in font.metadata.records:
        if record.keyword in ('BaseHoriz:', 'BaseVert:'):
            from sfdfont._baselines import baseline_identity

            result.append(baseline_identity(record))
        elif record.keyword == 'Lookup:':
            lookup = SfdLookup.from_record(record)
            result.append(('Lookup:', lookup.name, tuple(sub.name for sub in lookup.subtables)))
        elif record.keyword in CONTEXT_KEYS:
            context = SfdContext.from_record(record)
            result.append((record.keyword, context.subtable, context.tag, context.script_language_index))
        elif record.keyword in KERN_CLASS_KEYS:
            kern = SfdKerningClass.from_record(record)
            result.append((record.keyword, kern.subtable, kern.script_language_index))
        elif record.keyword in AAT_KEYS:
            machine = SfdStateMachine.from_record(record)
            result.append((record.keyword, machine.subtable, machine.feature, machine.setting))
        elif record.keyword == 'AnchorClass2:':
            classes = SfdAnchorClasses.from_record(record).classes
            result.append((record.keyword, tuple((v.name, v.subtable) for v in classes)))
        elif record.keyword in ('MarkAttachClasses:', 'MarkAttachSets:'):
            from sfdfont._marks import mark_identity

            result.append(mark_identity(record))
    return result
