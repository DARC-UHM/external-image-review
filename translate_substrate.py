# Substrate code translations and grain size order

sub_concepts = {
    'sed': 'sediment',
    'peb': 'pebble',
    'cob': 'cobble',
    'bou': 'boulder',
    'bed': 'bedrock',
    'man': 'man-made',
    'dead': 'dead',
    'dik': 'dike rock formation of',
    'c': 'cemented',
    'b': 'basalt',
    'l': 'limestone',
    'fl': 'fluted',
    'blk': 'block',
    'nodmn': 'manganese nodules',
    'orgcn': 'Cnidaria',
    'orgal': 'algal organism',
    'orgrho': 'Rhodophyta',
    'rov': 'remotely operated underwater vehicle',
    'ven': 'vent',
    'mn': 'with manganese crust',
    'pi': ['pillow lava formation of', 'from pillow lava'],
    'a': 'composed of algal carbonate',
    't': 'talus',
    'po': 'pocket',
    'hp': 'of hydrothermal precipitate',
    'led': 'ledge',
    'cre': 'crevice',
    'cha': 'channel',
    'cav': 'cavity',
    'cra': 'crack',
    'bu': 'burrow',
    'mo': 'mound',
    'ho': 'hollow',
    'tr': 'track',
    'sc': 'sediment-covered',
    'tu': 'tube formation of',
    'mu': 'mudstone',
    'm': 'mudstone',
    'du': 'dunes',
    'ri': 'rippled',
    'col': 'columnar',
    'cn': 'Cnidaria',
    'spo': 'Porifera',
    'org': 'organism',
    ' org': 'organism',
    'art': 'artificial reef',
    'cem': 'cement',
    'fib': 'fiber object',
    'met': 'metallic object',
    'tra': 'trash',
    'ord': 'ordnance',
    'made': 'object',
    'wre': 'wreck',
    'pla': 'plastic object'
}

roots = ['sed', 'nodmn', 'peb', 'cob', 'bou', 'blk', 'bed', 'orgcn', 'orgal',
         'orgrho', 'dead', 'man', 'rov', 'ven', 'org']
sames = ['organism', 'man-made trash', 'tube', 'Animal-made tube', 'debris',
         'sediment', 'pebble', 'cobble', 'boulder', 'bedrock']
suffixes = ['mn', 'pi', 'a', 't', 'po', 'hp']
suffixes_forms = ['led', 'cre', 'cha', 'cav', 'cra', 'bu', 'mo', 'ho', 'tr', 'du']
prefixes = ['dik', 'fl', 'sc', 'tu', 'mu', 'ri', 'col', 'c', 'b', 'l', 'm']
suffixes_dead = ['cn', 'spo', ' org']
suffixes_man = ['art', 'cem', 'fib', 'met', 'tra', 'ord', 'made', 'wre', 'pla']

all_affixes = suffixes + suffixes_forms + prefixes + suffixes_dead + suffixes_man
all_affixes.sort(key=len, reverse=True)


def translate_substrate_code(code):
    """ Translates substrate codes into human language """
    if code in sames:
        return code
    substrate_word_list = []
    r = ''
    man_or_forms = []
    for root in roots:
        if root in code:
            substrate_word_list.append(sub_concepts[root])
            r = sub_concepts[root]
            code = code.replace(root, '')
            if code == '':
                if r == 'man-made':
                    return 'man-made object'
                else:
                    return r
            break
    for affix in all_affixes:
        if affix in code:
            if affix == 'pi':
                if r == 'bedrock' or r == 'block':
                    substrate_word_list.insert(0, sub_concepts[affix][0])
                else:
                    substrate_word_list.append(sub_concepts[affix][1])
            elif affix in suffixes and r in substrate_word_list:
                substrate_word_list.insert(substrate_word_list.index(r) + 1, sub_concepts[affix])
            elif affix in suffixes_forms or affix in suffixes_man:
                substrate_word_list.append(sub_concepts[affix])
                man_or_forms.append(affix)
            elif affix in suffixes_dead:
                substrate_word_list.append(sub_concepts[affix])
            elif affix in prefixes and r in substrate_word_list:
                substrate_word_list.insert(substrate_word_list.index(r), sub_concepts[affix])
            code = code.replace(affix, '')
            if code == '':
                if len(man_or_forms) >= 2:
                    substrate_word_list.insert(-1, 'and')
                subs = ' '.join(substrate_word_list)
                if subs[:4] == 'dead':
                    subs = f'{subs[5:]} (dead)'
                return subs
    return ''
