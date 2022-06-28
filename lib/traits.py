traits = {
    'crusher': {
            'name': 'crusher',
            'emoji': '🔨',
            'amount': 251,
            'description': 'Crushers always attack the first enemy.',
            'effects': [
            ],
            'note': ''
        },
    'piercer': {
                'name': 'piercer',
                'emoji': '🗡️',
                'amount': 243,
                'description': 'Piercers always attack the last enemy.',
                'effects': [
                ],
                'note': ''
            },
    'slasher': {
                'name': 'slasher',
                'emoji': '✂️',
                'amount': 215,
                'description': 'Slashers always attack two random enemies.',
                'effects': [
                ],
                'note': 'Attack effects get applied twice. Round effects do not get applied twice.'
            },
    'pacifist': {
                'name': 'pacifist',
                'emoji': '🕊️',
                'amount': 4,
                'description': 'Pacfists do not attack. Instead they increase the critical hit chance for allies',
                'effects': [
                    {
                        'amount': 1,
                        'text': 'Allow allies to also crit when rolling a 19.'
                    },
                    {
                        'amount': 2,
                        'text': 'Allow allies to also crit when rolling a 19 or 18.'
                    },
                    {
                        'amount': 3,
                        'text': 'Allow allies to also crit when rolling a 19, 18 or 17.'
                    },
                    {
                        'amount': 4,
                        'text': 'Allow allies to also crit when rolling a 19, 18, 17 or 16.'
                    }
                ],
                'note': 'Every creature starts out with a hit chance of 1 out of 20. An increase of 1 of hit chance gives the creatures a hit chance of 2 out of 20.'
            },
    'underdark': {
                'name': 'underdark',
                'emoji': '🌌',
                'amount': 127,
                'description': 'Underdark creatures consume weaker allies.',
                'effects': [
                    {
                        'amount': 5,
                        'text': 'At the start of an underdark\'s turn, if the next ally attacker has less hp then the underdark, the underdark consumes them, adding 50% of the ally\'s hp and stats (but not ac) to themselves.'
                    },
                    {
                        'amount': 10,
                        'text': 'At the start of an underdark\'s turn, if the next ally attacker has less hp then the underdark, the underdark consumes them, adding 100% of the ally\'s hp and stats (but not ac) to themselves.'
                    }
                ],
                'note': ''
            },
    'beast': {
                'name': 'beast',
                'emoji': '🐻',
                'amount': 105,
                'description': 'Beasts call other beasts to their help at the end of their turn.',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'Each type of beast has a 30% chance to summon a beast of same type and level.'
                    },
                    {
                        'amount': 6,
                        'text': 'Each type of beast has a 50% chance to summon a beast of same type and level.'
                    },
                    {
                        'amount': 9,
                        'text': 'Each type of beast has a 80% chance to summon a beast of same type and level.'
                    }
                ],
                'note': ''
            },
    'forest': {
                'name': 'forest',
                'emoji': '🌲',
                'amount': 93,
                'description': 'Forest Trees summon Awakened Trees.',
                'effects': [
                    {
                        'amount': 5,
                        'text': 'At the end of each round, summon an Awakened Tree for your side.'
                    }
                ],
                'note': ''
            },
    'monstrosity': {
                'name': 'monstrosity',
                'emoji': '🦖',
                'amount': 83,
                'description': 'Monstrosities feed on their enemies to become stronger.',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'On enemy death, all monstrosities gain +3 in all stats.',
                    },
                    {
                        'amount': 6,
                        'text': 'On enemy death, all monstrosities gain +6 in all stats.',
                    },
                    {
                        'amount': 9,
                        'text': 'On enemy death, all monstrosities gain +9 in all stats.',
                    }
                ],
                'note': ''
            },
    'poison': {
                'name': 'poison',
                'emoji': '💚',
                'amount': 77,
                'description': 'All poisonous creatures poison enemy creatures on a successful hit.',
                'effects': [
                    {
                        'amount': 1,
                        'text': 'Poison the enemy creature, making them take damage equal to 10% of their maximum health at the start of their turn.'
                    }
                ],
                'note': ''
            },
    'grassland': {
                'name': 'grassland',
                'emoji': '🥦',
                'amount': 69,
                'description': 'Grassland restore part of their maximum health at the end of each turn.',
                'effects': [
                    {
                        'amount': 5,
                        'text': 'Heal for 40% of their maximum health'
                    }
                ],
                'note': ''
            },
    'necrotic': {
                'name': 'necrotic',
                'emoji': '☠️',
                'amount': 62,
                'description': 'Upon successfully hitting a target, necrotic creatures reduce the target\'s maximum hp',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'Reduce the target\'s maximum hp to their current hp.'
                    }
                ],
                'note': 'Creatures cannot be healed beyond their maximum hp.'
            },
    'mountain': {
                'name': 'mountain',
                'emoji': '⛰️',
                'amount': 57,
                'description': 'Mountain creatures reduce the damage taken by non-mountain allies.',
                'effects': [
                    {
                        'amount': 5,
                        'text': 'Non-mountain allies take 50% less damage.'
                    }
                ],
                'note': ''
            },
    'dragon': {
                'name': 'dragon',
                'emoji': '🐉',
                'amount': 56,
                'description': 'Dragons compete against one-another: At the start of the fight the dragon with highest cr gains additional stats but all other dragons gain reduced stats.',
                'effects': [
                    {
                        'amount': 3,
                        'text': '+10 in all stats for the strongest dragon, -3 for the other dragons.'
                    },
                    {
                        'amount': 6,
                        'text': '+20 in all stats for the strongest dragon, -5 for the other dragons.'
                    },
                    {
                        'amount': 9,
                        'text': '+30 in all stats for the strongest dragon, -10 for the other dragons.'
                    }
                ],
                'note': 'For dragons with equal CR, a random strongest dragon is chosen.'
            },
    'urban': {
                'name': 'urban',
                'emoji': '🏙️',
                'amount': 56,
                'description': 'Urban creatures adapt quickly, gaining additional stats if they fail an attack.',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'If an urban creature fails an attack, they gain +2 in all stats.'
                    },
                    {
                        'amount': 6,
                        'text': 'If an urban creature fails an attack, they gain +3 in all stats.'
                    },
                    {
                        'amount': 9,
                        'text': 'If an urban creature fails an attack, they gain +4 in all stats.'
                    }
                ],
                'note': ''
            },
    'psychic': {
                'name': 'psychic',
                'emoji': '🔮',
                'amount': 54,
                'description': 'Psychic reduces the stats of the enemies they hit.',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'Being hit by a psychic creature reduces all stats by 1'
                    },
                    {
                        'amount': 6,
                        'text': 'Being hit by a psychic creature reduces all stats by 2'
                    },
                    {
                        'amount': 9,
                        'text': 'Being hit by a psychic creature reduces all stats by 3'
                    }
                ],
                'note': ''
            },
    'fire': {
                'name': 'fire',
                'emoji': '🔥',
                'amount': 53,
                'description': 'On a successful attack, fire creatures burn the target and adjacent creatures, making them take damage at the start of their turn.',
                'effects': [
                    {
                        'amount': 2,
                        'text': '10 damage at the start of their turn.'
                    },
                    {
                        'amount': 4,
                        'text': '20 damage at the start of their turn.'
                    },
                    {
                        'amount': 6,
                        'text': '30 damage at the start of their turn.'
                    },
                    {
                        'amount': 8,
                        'text': '40 damage at the start of their turn.'
                    },
                    {
                        'amount': 10,
                        'text': '55 damage at the start of their turn.'
                    }
                ],
                'note': ''
            },
    'desert': {
                'name': 'desert',
                'emoji': '🏜️',
                'amount': 49,
                'description': 'Desert creatures take less damage.',
                'effects': [
                    {
                        'amount': 5,
                        'text': 'Desert creatures take 40% less damage.'
                    }
                ],
                'note': ''
            },
    'undead': {
                'name': 'undead',
                'emoji': '🧟',
                'amount': 48,
                'description': 'Upon death, all allies have a chance to be resurrected with reduced health.',
                'effects': [
                    {
                        'amount': 2,
                        'text': '10% chance to be resurrected with 10% of their maximum health'
                    },
                    {
                        'amount': 4,
                        'text': '20% chance to be resurrected with 15% of their maximum health'
                    },
                    {
                        'amount': 6,
                        'text': '30% chance to be resurrected with 20% of their maximum health'
                    },
                    {
                        'amount': 8,
                        'text': '40% chance to be resurrected with 25% of their maximum health'
                    },
                    {
                        'amount': 10,
                        'text': '50% chance to be resurrected with 50% of their maximum health'
                    }
                ],
                'note': ''
            },
    'aberration': {
                'name': 'aberration',
                'emoji': '👾',
                'amount': 39,
                'description': 'Aberrations get an increase to all stats upon the successful hit of a friendly aberration.',
                'effects': [
                    {
                        'amount': 3,
                        'text': '+1 in all stats upon the successful hit of a friendly aberration'
                    },
                    {
                        'amount': 6,
                        'text': '+2 in all stats upon the successful hit of a friendly aberration'
                    },
                    {
                        'amount': 9,
                        'text': '+3 in all stats upon the successful hit of a friendly aberration'
                    },
                ],
                'note': ''
            },
    'acid': {
                'name': 'acid',
                'emoji': '❇️',
                'amount': 39,
                'description': 'Acidic creature give acidic burns to creatures that attack them, making them take damage at the start of their turn.',
                'effects': [
                    {
                        'amount': 1,
                        'text': 'Every turn after attacking, attackers will take 5% of their maximum health as damage.'
                    }
                ],
                'note': ''
            },
    'demon': {
                'name': 'demon',
                'emoji': '🎃',
                'amount': 38,
                'description': 'Demons heal for part of the damage they deal when attacking.',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'Heal for 30% of dealt damage when attacking.'
                    },
                    {
                        'amount': 6,
                        'text': 'Heal for 60% of dealt damage when attacking.'
                    },
                    {
                        'amount': 9,
                        'text': 'Heal for 120% of dealt damage when attacking.'
                    }
                ],
                'note': 'Bonus damage does not count'
            },
    'coastal': {
                'name': 'coastal',
                'emoji': '🏝️',
                'amount': 35,
                'description': 'Coastal creatures allow adjacent allies to additionally attack a random enemy.',
                'effects': [
                    {
                        'amount': 5,
                        'text': 'Allow adjacent allies to additionally attack a random enemy.'
                    }
                ],
                'note': 'Attack effects apply.'
            },
    'elemental': {
                'name': 'elemental',
                'emoji': '🌀',
                'amount': 33,
                'description': 'Elementals summon a random weaker elemental at the end of each round.',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'At the end of the round, summon a random elemental (Cr < 5).'
                    },
                    {
                        'amount': 6,
                        'text': 'At the end of the round, summon a random elemental (Cr < 10).'
                    },
                    {
                        'amount': 9,
                        'text': 'At the end of the round, summon a random elemental (Cr Unbounded).'
                    }
                ],
                'note': ''
            },
    'shapechanger': {
                'name': 'shapechanger',
                'emoji': '👽',
                'amount': 30,
                'description': 'Shapechangers use stats from other creatures when it suits them.',
                'effects': [
                    {
                        'amount': 5,
                        'text': 'For all checks, Shapechangers always choose their target\'s stats if its higher than their own. (excluding AC)'
                    },
                    {
                        'amount': 10,
                        'text': 'For all checks, Shapechangers always choose the highest stat in the entire battle. (excluding AC)'
                    }
                ],
                'note': ''
            },
    'lightning': {
                'name': 'lightning',
                'emoji': '⚡',
                'amount': 28,
                'description': 'Successful hits of lightning creatures also damage additional enemies.',
                'effects': [
                    {
                        'amount': 5,
                        'text': 'Also damage 2 additional random enemies.'
                    }
                ],
                'note': ''
            },
    'construct': {
                'name': 'construct',
                'emoji': '⚙️',
                'amount': 28,
                'description': 'At the beginning of the fight, constructs gain additional AC and damage resistance.',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'Constructs gain +2 AC and take 30% less damage.'
                    },
                    {
                        'amount': 6,
                        'text': 'Constructs gain +4 AC and take 50% less damage.'
                    },
                    {
                        'amount': 9,
                        'text': 'Constructs gain +7 AC and take 70% less damage.'
                    }
                ],
                'note': ''
            },
    'swamp': {
                'name': 'swamp',
                'emoji': '🏕️',
                'amount': 27,
                'description': 'Swamp creatures take less damage from enemies with a higher CR than them.',
                'effects': [
                    {
                        'amount': 5,
                        'text': 'Take 50% less damage from enemies with higher CR.'
                    }
                ],
                'note': ''
            },
    'devil': {
                'name': 'devil',
                'emoji': '👿',
                'amount': 27,
                'description': 'Devils bind the creature in front of them to themselves, giving it increased stats and resummoning it once after dying.',
                'effects': [
                    {
                        'amount': 1,
                        'text': 'Bind the creature in front of you giving it +5 in all stats and resummoning it once after death.'
                    }
                ],
                'note': 'The creature will not be resummoned if the devil it is bound to is dead.'
            },
    'giant': {
                'name': 'giant',
                'emoji': '🗿',
                'amount': 27,
                'description': 'Giants gain increased HP at the start of the fight.',
                'effects': [
                    {
                        'amount': 3,
                        'text': '+50% health'
                    },
                    {
                        'amount': 6,
                        'text': '+100% health'
                    },
                    {
                        'amount': 9,
                        'text': '+200% health'
                    }
                ],
                'note': ''
            },
    'underwater': {
                'name': 'underwater',
                'emoji': '🌊',
                'amount': 26,
                'description': 'Underwater creatures take less damage and deal less damage.',
                'effects': [
                    {
                        'amount': 5,
                        'text': 'Take 50% less damage and deal 50% less damage.'
                    }
                ],
                'note': ''
            },
    'cold': {
                'name': 'cold',
                'emoji': '❄️',
                'amount': 25,
                'description': 'On a successful hit, cold creatures reduce the stats of the target and adjacent enemies. (excluding AC)',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'On a successful hit, reduce the stats of the target and adjacent enemies by 2. (excluding AC)'
                    },
                    {
                        'amount': 6,
                        'text': 'On a successful hit, reduce the stats of the target and adjacent enemies by 4. (excluding AC)'
                    },
                    {
                        'amount': 9,
                        'text': 'On a successful hit, reduce the stats of the target and adjacent enemies by 7. (excluding AC)'
                    }
                ],
                'note': ''
            },
    'spellcaster': {
                'name': 'spellcaster',
                'emoji': '🧙',
                'amount': 23,
                'description': 'On a crit, spellcasters additionally damage all enemies.',
                'effects': [
                ],
                'note': ''
            },
    'fey': {
                'name': 'fey',
                'emoji': '✨',
                'amount': 21,
                'description': 'At the end of the round, fey summon pixies.',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'At the end of the round, summon 1 pixie.'
                    },
                    {
                        'amount': 6,
                        'text': 'At the end of the round, summon 2 pixies.'
                    },
                    {
                        'amount': 9,
                        'text': 'At the end of the round, summon 3 pixies.'
                    }
                ],
                'note': 'The pixies are pacifists and therefore not attack.'
            },
    'arctic': {
                'name': 'arctic',
                'emoji': '🧊',
                'amount': 19,
                'description': 'At the start of every round, all non-arctic creatures gain reduced stats.',
                'effects': [
                    {
                        'amount': 5,
                        'text': 'At the start of every round, all non-arctic creatures gain -5 to all stats. (excluding AC)'
                    }
                ],
                'note': ''
            },
    'plant': {
                'name': 'plant',
                'emoji': '🌱',
                'amount': 19,
                'description': 'Heal the most damaged ally to full health and give them additional maximum health at the end of the round.',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'Heal the most damaged ally to maximum health and give them +20% maximum health at the end of the round.'
                    },
                    {
                        'amount': 6,
                        'text': 'Heal the most damaged ally to maximum health and give them +40% maximum health at the end of the round.'
                    },
                    {
                        'amount': 9,
                        'text': 'Heal the most damaged ally to maximum health and give them +70% maximum health.'
                    }
                ],
                'note': ''
            },
    'elf': {
                'name': 'elf',
                'emoji': '🧝',
                'amount': 17,
                'description': 'Instead of using AC, elves dodge attacks.',
                'effects': [
                    {
                        'amount': 1,
                        'text': 'dodge chance of 30%'
                    },
                    {
                        'amount': 3,
                        'text': 'dodge chance of 40%'
                    },
                    {
                        'amount': 6,
                        'text': 'dodge chance of 60%'
                    },
                    {
                        'amount': 9,
                        'text': 'dodge chance of 80%'
                    }
                ],
                'note': ''
            },
    'hill': {
                'name': 'hill',
                'emoji': '🏞️',
                'amount': 16,
                'description': 'At the start of the fight, all hill creatures gain increased HP for each AC.',
                'effects': [
                    {
                        'amount': 5,
                        'text': 'Gain +10% HP for each AC.'
                    }
                ],
                'note': ''
            },
    'force': {
                'name': 'force',
                'emoji': '🏋️',
                'amount': 13,
                'description': 'Force creatures may ignore armor.',
                'effects': [
                    {
                        'amount': 5,
                        'text': 'Force creatures ignore armor.'
                    }
                ],
                'note': 'They do not ignore any armor alternatives (e.g. dodge chance) or damage reductions.'
            },
    'thunder': {
                'name': 'thunder',
                'emoji': '🌩️',
                'amount': 11,
                'description': 'Thunder attacks also damage additional enemies behind the target.',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'Thunder attacks also damage 2 enemies behind the enemy.'
                    },
                    {
                        'amount': 6,
                        'text': 'Thunder attacks also damage 3 enemies behind the enemy.'
                    },
                    {
                        'amount': 9,
                        'text': 'Thunder attacks also damage 5 enemies behind the enemy.'
                    }
                ],
                'note': ''
            },
    'yugoloth': {
                'name': 'yugoloth',
                'emoji': '👹',
                'amount': 3,
                'description': 'Yugoloths allow allies to also crit when rolling a 1.',
                'effects': [
                ],
                'note': ''
            },
    'goblinoid': {
                'name': 'goblinoid',
                'emoji': '👺',
                'amount': 10,
                'description': 'On a succesful attack of a goblinoid, also other goblinoids damage the target.',
                'effects': [
                    {
                        'amount': 5,
                        'text': 'On a succesful attack of a goblinoid, all friendly goblinoids damage the target.'
                    }
                ],
                'note': ''
            },
    'orc': {
                'name': 'orc',
                'emoji': '💪',
                'amount': 10,
                'description': 'Orc gain a bonus on their attack roll when missing health.',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'Gain +5 on their attack roll for each 5% of health missing'
                    },
                    {
                        'amount': 6,
                        'text': 'Gain +8 on their attack roll for each 5% of health missing'
                    },
                    {
                        'amount': 9,
                        'text': 'Gain +15 on their attack roll for each 5% of health missing'
                    }
                ],
                'note': ''
            },
    'gith': {
                'name': 'gith',
                'emoji': '🧝🏽‍♀️',
                'amount': 9,
                'description': 'Gith gain additional stats on their attack roll if their CR is lower than the enemies.',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'Gain +10 on their attack roll if their CR is lower than the enemies.'
                    },
                    {
                        'amount': 6,
                        'text': 'Gain +20 on their attack roll if their CR is lower than the enemies.'
                    },
                    {
                        'amount': 9,
                        'text': 'Gain +30 on their attack roll if their CR is lower than the enemies.'
                    }
                ],
                'note': ''
            },
    'ooze': {
                'name': 'ooze',
                'emoji': '🧪',
                'amount': 8,
                'description': 'Ooze may consum weakened attackers, absorbing them for their stats (excluding AC).',
                'effects': [
                    {
                        'amount': 1,
                        'text': 'Being attacked by an enemy with 20% or less HP leads to the ooze consuming them for their max HP and makes them absorb all of the enemy\'s stats.'
                    }
                ],
                'note': ''
            },
    'celestial': {
                'name': 'celestial',
                'emoji': '👼',
                'amount': 8,
                'description': 'Celestials shield all allies, directing reduced damage to themselves instead.',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'If a celestial is still alive and an ally takes damage, the highest HP celestial will instead take 50% of the damage and the attacked creature none.'
                    },
                    {
                        'amount': 6,
                        'text': 'If a celestial is still alive and an ally takes damage, the highest HP celestial will instead take 30% of the damage and the attacked creature none.'
                    }
                ],
                'note': ''
            },
    'dwarf': {
                'name': 'dwarf',
                'emoji': '🧔',
                'amount': 8,
                'description': 'Dwarves take less damage when on low health.',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'When below 20% of health, take 70% less damage.'
                    },
                    {
                        'amount': 6,
                        'text': 'When below 20% of health, take 80% less damage.'
                    },
                    {
                        'amount': 8,
                        'text': 'When below 20% of health, take 95% less damage.'
                    }
                ],
                'note': ''
            },
    'radiant': {
                'name': 'radiant',
                'emoji': '😇',
                'amount': 6,
                'description': 'On death, radiant creatures heal all allies to full health.',
                'effects': [
                ],
                'note': ''
            },
    'yuan-ti': {
                'name': 'yuan-ti',
                'emoji': '🐍',
                'amount': 4,
                'description': 'Yuan-ti deal increased damage when attacking enemies with lower health.',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'If the enemy is below 10% health, deal +100% damage.'
                    },
                    {
                        'amount': 6,
                        'text': 'If the enemy is below 20% health, deal +100% damage.'
                    },
                    {
                        'amount': 9,
                        'text': 'If the enemy is below 30% health, deal +100% damage.'
                    }
                ],
                'note': ''
            }
}

