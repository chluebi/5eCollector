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
    'underdark': {
                'name': 'underdark',
                'emoji': '🌌',
                'amount': 127,
                'description': 'Underdark creatures consume weaker allies.',
                'effects': [
                    {
                        'amount': 5,
                        'text': 'At the start of an underdark\'s turn, if the next ally attacker has less hp then the underdark, the underdark consumes them, adding all of the ally\'s hp and stats (but not ac) to themselves.'
                    }
                ],
                'note': ''
            },
    'beast': {
                'name': 'beast',
                'emoji': '🐻',
                'amount': 105,
                'description': 'Beasts gain increased stats at the start of the fight.',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'All Beasts get +3 in all stats'
                    },
                    {
                        'amount': 6,
                        'text': 'All Beasts get +5 in all stats'
                    },
                    {
                        'amount': 9,
                        'text': 'All Beasts get +8 in all stats'
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
                'description': 'Monstrosities deal increased damage.',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'Monstrosities deal +20% more damage',
                    },
                    {
                        'amount': 6,
                        'text': 'Monstrosities deal +40% more damage',
                    },
                    {
                        'amount': 9,
                        'text': 'Monstrosities deal +80% more damage',
                    }
                ],
                'note': ''
            },
    'poison': {
                'name': 'poison',
                'emoji': '💚',
                'amount': 77,
                'description': 'All poisonous creatures deal additional damage on a critical hit.',
                'effects': [
                    {
                        'amount': 2,
                        'text': '+4 damage on a critical hit.'
                    },
                    {
                        'amount': 4,
                        'text': '+12 damage on a critical hit.'
                    },
                    {
                        'amount': 6,
                        'text': '+20 damage on a critical hit.'
                    },
                    {
                        'amount': 8,
                        'text': '+30 damage on a critical hit.'
                    },
                    {
                        'amount': 10,
                        'text': '+50 damage on a critical hit.'
                    }
                ],
                'note': 'Critical hits occur when a 20 is rolled for the attack roll and always hit.'
            },
    'grassland': {
                'name': 'grassland',
                'emoji': '🥦',
                'amount': 69,
                'description': 'Grassland restore part of their maximum health at the end of each turn.',
                'effects': [
                    {
                        'amount': 5,
                        'text': 'Heal for 5% of their maximum health'
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
                        'text': 'Non-mountain allies take 30% less damage.'
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
                        'text': '+5 in all stats for the strongest dragon, -2 for the other dragons.'
                    },
                    {
                        'amount': 6,
                        'text': '+10 in all stats for the strongest dragon, -5 for the other dragons.'
                    },
                    {
                        'amount': 9,
                        'text': '+20 in all stats for the strongest dragon, -10 for the other dragons.'
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
                        'amount': 5,
                        'text': 'If an urban creature fails an attack, they gain +1 in the stat they attacked with.'
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
                'description': 'On a successful attack, fire creatures deal additional damage to the target and adjacent creatures.',
                'effects': [
                    {
                        'amount': 2,
                        'text': 'An additional +1 damage to the target and adjacent creatures.'
                    },
                    {
                        'amount': 4,
                        'text': 'An additional +2 damage to the target and adjacent creatures.'
                    },
                    {
                        'amount': 6,
                        'text': 'An additional +3 damage to the target and adjacent creatures.'
                    },
                    {
                        'amount': 8,
                        'text': 'An additional +4 damage to the target and adjacent creatures.'
                    },
                    {
                        'amount': 10,
                        'text': 'An additional +5 damage to the target and adjacent creatures.'
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
                        'text': 'Desert creatures take 20% less damage.'
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
                        'text': '5% chance to be resurrected with 10% of their health'
                    },
                    {
                        'amount': 4,
                        'text': '10% chance to be resurrected with 15% of their health'
                    },
                    {
                        'amount': 6,
                        'text': '15% chance to be resurrected with 20% of their health'
                    },
                    {
                        'amount': 8,
                        'text': '20% chance to be resurrected with 25% of their health'
                    },
                    {
                        'amount': 10,
                        'text': '25% chance to be resurrected with 50% of their health'
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
                'description': 'Acidic creature damage enemies who attack them.',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'Deal 5 damage to the attacker.'
                    },
                    {
                        'amount': 6,
                        'text': 'Deal 10 damage to the attacker.'
                    },
                    {
                        'amount': 9,
                        'text': 'Deal 20 damage to the attacker.'
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
                        'text': 'Heal for 10% of dealt damage when attacking.'
                    },
                    {
                        'amount': 6,
                        'text': 'Heal for 30% of dealt damage when attacking.'
                    },
                    {
                        'amount': 9,
                        'text': 'Heal for 50% of dealt damage when attacking.'
                    }
                ],
                'note': ''
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
                        'text': 'At the end of the round, summon a random elemental (Cr < 2).'
                    },
                    {
                        'amount': 6,
                        'text': 'At the end of the round, summon a random elemental (Cr < 4).'
                    },
                    {
                        'amount': 9,
                        'text': 'At the end of the round, summon a random elemental (Cr < 10).'
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
                        'text': 'Also damage the first and last enemy.'
                    }
                ],
                'note': ''
            },
    'construct': {
                'name': 'construct',
                'emoji': '⚙️',
                'amount': 28,
                'description': 'At the beginning of the fight, constructs gain additional AC.',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'Constructs gain +2 AC.'
                    },
                    {
                        'amount': 6,
                        'text': 'Constructs gain +4 AC.'
                    },
                    {
                        'amount': 9,
                        'text': 'Constructs gain +7 AC.'
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
                        'text': 'Take 30% less damage from enemies with higher CR.'
                    }
                ],
                'note': ''
            },
    'devil': {
                'name': 'devil',
                'emoji': '👿',
                'amount': 27,
                'description': 'When a devil rolls a 6, all devils gain increased stats.',
                'effects': [
                    {
                        'amount': 5,
                        'text': 'When a devil rolls a 6, all devils gain +6 in all stats. (excluding AC)'
                    }
                ],
                'note': ''
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
                'description': 'On a crit, cold creatures reduce the stats of the target and adjacent enemies. (excluding AC)',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'On a crit, reduce the stats of the target and adjacent enemies by 3. (excluding AC)'
                    },
                    {
                        'amount': 6,
                        'text': 'On a crit, reduce the stats of the target and adjacent enemies by 5. (excluding AC)'
                    },
                    {
                        'amount': 9,
                        'text': 'On a crit, reduce the stats of the target and adjacent enemies by 7. (excluding AC)'
                    }
                ],
                'note': ''
            },
    'spellcaster': {
                'name': 'spellcaster',
                'emoji': '🧙',
                'amount': 23,
                'description': 'On a crit, spellcasters damage all enemies.',
                'effects': [
                ],
                'note': ''
            },
    'fey': {
                'name': 'fey',
                'emoji': '✨',
                'amount': 21,
                'description': 'Instead of attacking an enemy, fey heal all allies.',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'Heal all allies for 30% of the roll.'
                    },
                    {
                        'amount': 6,
                        'text': 'Heal all allies for 60% of the roll.'
                    },
                    {
                        'amount': 9,
                        'text': 'Heal all allies for 100% of the roll.'
                    }
                ],
                'note': ''
            },
    'arctic': {
                'name': 'arctic',
                'emoji': '🧊',
                'amount': 19,
                'description': 'At the start of the fight, all non-arctic creatures gain reduced stats.',
                'effects': [
                    {
                        'amount': 5,
                        'text': 'At the start of the fight, all non-arctic creatures gain -5 to all stats. (excluding AC)'
                    }
                ],
                'note': ''
            },
    'plant': {
                'name': 'plant',
                'emoji': '🌱',
                'amount': 19,
                'description': 'Heal the most damaged ally for a part of their maximum health at the end of the turn.',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'Heal the most damaged ally for 10% of their maximum health at the end of the turn.'
                    },
                    {
                        'amount': 6,
                        'text': 'Heal the most damaged ally for 20% of their maximum health at the end of the turn.'
                    },
                    {
                        'amount': 9,
                        'text': 'Heal the most damaged ally for 30% of their maximum health at the end of the turn.'
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
                        'text': 'Gain +5% HP for each AC.'
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
                        'amount': 10,
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
                        'text': 'Thunder attacks also damage all enemies behind the enemy.'
                    }
                ],
                'note': ''
            },
    'yugoloth': {
                'name': 'yugoloth',
                'emoji': '👹',
                'amount': 10,
                'description': 'Yugoloths allow nearby allies to also crit when rolling a 1.',
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
                'description': 'Orc gain additional stats on their attack roll with their missing health.',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'Gain +1 on their attack roll for each 5% of health missing'
                    },
                    {
                        'amount': 6,
                        'text': 'Gain +2 on their attack roll for each 5% of health missing'
                    },
                    {
                        'amount': 9,
                        'text': 'Gain +4 on their attack roll for each 5% of health missing'
                    }
                ],
                'note': ''
            },
    'gith': {
                'name': 'gith',
                'emoji': '🧝🏽‍♀️',
                'amount': 9,
                'description': 'Orc gain additional stats on their attack roll if their CR is lower than the enemies.',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'Gain +5 on their attack roll if their CR is lower than the enemies.'
                    },
                    {
                        'amount': 6,
                        'text': 'Gain +10 on their attack roll if their CR is lower than the enemies.'
                    },
                    {
                        'amount': 9,
                        'text': 'Gain +15 on their attack roll if their CR is lower than the enemies.'
                    }
                ],
                'note': ''
            },
    'ooze': {
                'name': 'ooze',
                'emoji': '🧪',
                'amount': 8,
                'description': 'Ooze may consum weakened enemies, absorbing them for their stats and healing for their max HP.',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'Attacking an enemy with 10% or less HP leads to the ooze consuming them for their max HP and makes them absorb all of the enemy\'s stats.'
                    }
                ],
                'note': ''
            },
    'celestial': {
                'name': 'celestial',
                'emoji': '👼',
                'amount': 8,
                'description': 'If an enemy fails to attack on a celestial, all allies are healed for a part of their max HP.',
                'effects': [
                    {
                        'amount': 3,
                        'text': 'If an enemy fails to attack on a celestial, all allies are healed for 10% of their max HP.'
                    },
                    {
                        'amount': 6,
                        'text': 'If an enemy fails to attack on a celestial, all allies are healed for 20% of their max HP.'
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
                        'text': 'When below 20% of health, take 50% less damage.'
                    },
                    {
                        'amount': 6,
                        'text': 'When below 20% of health, take 70% less damage.'
                    },
                    {
                        'amount': 8,
                        'text': 'When below 20% of health, take 90% less damage.'
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

