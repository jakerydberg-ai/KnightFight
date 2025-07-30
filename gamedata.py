import copy

# --- Core Class Definitions ---


class Move:
    """Represents a move a Knight can perform."""

    def __init__(
        self,
        name,
        faction,
        power,
        accuracy=100,
        target_type="single_enemy",
        effect=None,
        effect_chance=0,
        self_effect=None,
        guard_gain=0,
        guard_multiplier=1.0,
        charge_turns=0,
        rampage_turns=0,
        blocks_aoe=False,
        sets_weather=None,
        priority=0,
        is_protection_move=False,
        synergy_effect=None,
        effect_duration=3,
        description="",
    ):
        self.name = name
        self.faction = faction
        self.power = power
        self.accuracy = accuracy
        self.target_type = target_type
        self.effect = effect
        self.effect_chance = effect_chance
        self.self_effect = self_effect
        self.guard_gain = guard_gain
        self.guard_multiplier = guard_multiplier
        self.charge_turns = charge_turns
        self.rampage_turns = rampage_turns
        self.blocks_aoe = blocks_aoe
        self.sets_weather = sets_weather
        self.priority = priority
        self.is_protection_move = is_protection_move
        self.synergy_effect = synergy_effect  # e.g., 'consecration'
        self.effect_duration = effect_duration
        self.description = description

    def __repr__(self):
        return f"{self.name} ({self.faction})"


class Ability:
    """Represents a passive or triggered ability."""

    def __init__(self, name, faction, description):
        self.name = name
        self.faction = faction
        self.description = description


class KnightTemplate:
    """A template for creating Knight instances, defining base stats and learnset."""

    def __init__(self, name, faction, hp, attack, defense, speed, learnset):
        self.name = name
        self.faction = faction
        self.base_stats = {"hp": hp, "atk": attack, "def": defense, "spd": speed}
        self.learnset = learnset


# --- Master Ability List ---
ALL_ABILITIES = {
    "Adrenaline": Ability(
        "Adrenaline",
        "Generic",
        "Attack is 1.5x higher while having a status condition.",
    ),
    "Avenger": Ability(
        "Avenger", "Generic", "Attack is 1.3x higher if an ally has fainted."
    ),
    "Sturdy": Ability(
        "Sturdy",
        "Generic",
        "If at full HP, this Knight cannot be knocked out in a single hit.",
    ),
    "Imposing": Ability(
        "Imposing",
        "Generic",
        "Upon entering battle, lowers the Attack of opposing Knights.",
    ),
    "Survivor": Ability(
        "Survivor",
        "Generic",
        "Powers up this Knight's weaker moves (power 50 or less).",
    ),
    "Bodyguard": Ability(
        "Bodyguard",
        "Steel",
        "Redirects single-target attacks from ally to this Knight. Takes 80% damage from redirected hits.",
    ),
    "Reinforced": Ability(
        "Reinforced", "Steel", "Reduces damage from all incoming attacks by 10%."
    ),
    "Adaptive Defense": Ability(
        "Adaptive Defense",
        "Steel",
        "Reduces damage from super-effective attacks by 25%.",
    ),
    "Pure As Steel": Ability(
        "Pure As Steel", "Steel", "Prevents other Knights from lowering its stats."
    ),
    "Interlocking Plating": Ability(
        "Interlocking Plating",
        "Steel",
        "Raises Defense by 1 stage when hit by an attack.",
    ),
    "Piercing Thorns": Ability(
        "Piercing Thorns", "Verdant", "Deals 1.5x damage to targets that have Guard."
    ),
    "Relentless Growth": Ability(
        "Relentless Growth",
        "Verdant",
        "This Knight's attacks ignore the target's defensive stat boosts.",
    ),
    "Rooted Stance": Ability(
        "Rooted Stance", "Verdant", "Prevents this Knight from being dazed."
    ),
    "Heartwood Strength": Ability(
        "Heartwood Strength", "Verdant", "Powers up striking moves by 20%."
    ),
    "Bane Of Shadow": Ability(
        "Bane Of Shadow",
        "Verdant",
        "Attack is raised by 1 stage when hit by a Shadow-type move.",
    ),
    "Sun's Chosen": Ability(
        "Sun's Chosen", "Radiant", "This Knight is immune to the Burn status effect."
    ),
    "Last Stand": Ability(
        "Last Stand",
        "Radiant",
        "When HP is below 1/3, this Knight's attacks deal 1.5x damage.",
    ),
    "Wielder Of Flame": Ability(
        "Wielder Of Flame",
        "Radiant",
        "Absorbs Radiant-type moves, nullifying them and boosting its own Radiant moves.",
    ),
    "Soul Ablaze": Ability(
        "Soul Ablaze",
        "Radiant",
        "Contact with this Knight may burn the attacker (30% chance).",
    ),
    "Divine Power": Ability(
        "Divine Power",
        "Radiant",
        "In Blazing Sun, Attack is boosted but this Knight loses HP each turn.",
    ),
    "Witch Doctor": Ability(
        "Witch Doctor",
        "Shadow",
        "Status effects applied by this Knight last 2 turns longer.",
    ),
    "Opportunist": Ability(
        "Opportunist", "Shadow", "Deals 1.3x damage to targets with a status condition."
    ),
    "Shadow Walker": Ability(
        "Shadow Walker",
        "Shadow",
        "Passes through and ignores the effects of moves like Shield Wall.",
    ),
    "Assassin": Ability(
        "Assassin", "Shadow", "Status-inflicting moves have increased priority."
    ),
    "Mantle Of Shadow": Ability(
        "Mantle Of Shadow",
        "Shadow",
        "Attack is raised by 1 stage if it knocks out another Knight.",
    ),
    "Permafrost": Ability(
        "Permafrost",
        "Cryo",
        "This Knight takes 50% damage from multi-hit/rampage attacks.",
    ),
    "Ice Shield": Ability(
        "Ice Shield",
        "Cryo",
        "When hit by an attack, gain Guard equal to 15% of the damage taken. Guard reduces damage from future attacks.",
    ),
    "Brimstone Runes": Ability(
        "Brimstone Runes",
        "Cryo",
        "Halves the damage taken from Radiant and Cryo type moves.",
    ),
    "Frozenheart": Ability(
        "Frozenheart",
        "Cryo",
        "This Knight heals a small amount of HP at the end of each turn in a Hailstorm.",
    ),
    "Chilling Finesse": Ability(
        "Chilling Finesse", "Cryo", "Doubles Speed in a Hailstorm."
    ),
    "Conductor": Ability(
        "Conductor",
        "Storm",
        "Redirects all single-target Storm-type moves to this Knight and nullifies their damage, boosting its own Attack.",
    ),
    "Energy Core": Ability(
        "Energy Core",
        "Storm",
        "Absorbs Storm-type moves, nullifying them and raising its Speed.",
    ),
    "Static Charge": Ability(
        "Static Charge",
        "Storm",
        "Contact with this Knight may daze the attacker (30% chance).",
    ),
    "Grounded": Ability(
        "Grounded",
        "Storm",
        "This knight is immune to having its Speed stat lowered and the 'slowed' status.",
    ),
    "Tempest Champion": Ability(
        "Tempest Champion",
        "Storm",
        "Sharply raises Attack when a stat is lowered by a foe.",
    ),
}

# --- Master Move List ---
ALL_MOVES = {
    # Generic
    "Cutting Blow": Move(
        "Cutting Blow",
        "Generic",
        40,
        100,
        description="A basic, reliable strike with a weapon.",
    ),
    "Empowered Strike": Move(
        "Empowered Strike",
        "Generic",
        60,
        85,
        description="A powerful but less accurate blow.",
    ),
    "Shield Wall": Move(
        "Shield Wall",
        "Generic",
        0,
        100,
        target_type="self",
        blocks_aoe=True,
        priority=4,
        is_protection_move=True,
        description="Protects the team from moves that hit all targets for one turn. Chance to fail if used consecutively.",
    ),
    "Swift Strike": Move(
        "Swift Strike",
        "Generic",
        35,
        100,
        priority=1,
        description="An attack that strikes before most others.",
    ),
    "Parry": Move(
        "Parry",
        "Generic",
        0,
        100,
        target_type="self",
        self_effect="slowed",
        priority=4,
        is_protection_move=True,
        description="Completely blocks an attack, disabling it for 1 turn. Slows the user. Chance to fail if used consecutively.",
    ),
    "Endure": Move(
        "Endure",
        "Generic",
        0,
        100,
        target_type="self",
        priority=4,
        is_protection_move=True,
        description="Allows the user to survive a fatal hit with 1 HP. Chance to fail if used consecutively.",
    ),
    "Reckless Charge": Move(
        "Reckless Charge",
        "Generic",
        85,
        100,
        self_effect="recoil_33",
        description="A powerful charge that also causes significant recoil damage.",
    ),
    "Hone Edge": Move(
        "Hone Edge",
        "Generic",
        0,
        100,
        target_type="self",
        self_effect="attack_up_2",
        description="A dazzling display that sharply raises the user's Attack stat.",
    ),
    "Foreboding Challenge": Move(
        "Foreboding Challenge",
        "Generic",
        0,
        100,
        target_type="all_enemies",
        effect="vulnerable",
        effect_chance=100,
        description="Lowers the defense of all opposing Knights.",
    ),
    # Steel
    "Royal Aegis": Move(
        "Royal Aegis",
        "Steel",
        0,
        100,
        target_type="self",
        priority=4,
        is_protection_move=True,
        description="Completely blocks an attack and lowers the attacker's Attack. Chance to fail if used consecutively.",
    ),
    "Crucible of Metal": Move(
        "Crucible of Metal",
        "Steel",
        0,
        100,
        sets_weather="Metalstorm",
        description="Summons a storm of metal shards for 5 turns. Boosts Steel-type Defense and may make foes Vulnerable.",
    ),
    "Bulwark Charge": Move(
        "Bulwark Charge",
        "Steel",
        1,
        100,
        description="Retaliates with 1.5x the damage taken from the last hit. Boosted in Metalstorm.",
    ),
    "Guard Bash": Move(
        "Guard Bash",
        "Steel",
        55,
        90,
        effect="dazed",
        effect_chance=20,
        description="A hard headbutt that may daze the target.",
    ),
    "Iron Brace": Move(
        "Iron Brace",
        "Steel",
        0,
        100,
        target_type="self",
        guard_gain=50,
        description="Braces for impact, gaining 50 Guard which reduces incoming damage.",
    ),
    "Crushing Blow": Move(
        "Crushing Blow",
        "Steel",
        75,
        95,
        self_effect="slowed",
        description="A massive slam that slows the user after.",
    ),
    "Steel Plating": Move(
        "Steel Plating",
        "Steel",
        0,
        100,
        target_type="self",
        self_effect="defense_up_2",
        description="Hardens the user's armor, sharply raising Defense.",
    ),
    "Splintering Charge": Move(
        "Splintering Charge",
        "Steel",
        60,
        100,
        effect="vulnerable",
        effect_chance=10,
        description="A blast of polished light that may lower the target's defense.",
    ),
    "Overclock": Move(
        "Overclock",
        "Steel",
        0,
        100,
        target_type="self",
        self_effect="attack_up_1_speed_up_2",
        description="Pushes internals to raise Attack by 1 and Speed by 2 stages.",
    ),
    "Forge Cannon": Move(
        "Forge Cannon",
        "Steel",
        100,
        95,
        self_effect="recoil_50",
        description="An ultimate Steel attack that costs 50% of the user's max HP.",
    ),
    "Phalanx": Move(
        "Phalanx",
        "Steel",
        0,
        100,
        target_type="team_synergy",
        guard_gain=25,
        description="For one turn, if the user's ally is also Steel-type, both gain Guard equal to 25% of their max HP.",
    ),
    # Verdant
    "Vine Whip": Move(
        "Vine Whip",
        "Verdant",
        40,
        100,
        priority=1,
        description="A quick whip that strikes before most others.",
    ),
    "Vastwood Surge": Move(
        "Vastwood Surge",
        "Verdant",
        0,
        100,
        sets_weather="Overgrowth",
        description="Summons an Overgrowth for 5 turns, boosting Verdant moves and healing Verdant knights.",
    ),
    "Onslaught Of Thorns": Move(
        "Onslaught Of Thorns",
        "Verdant",
        70,
        80,
        description="A powerful lash of thorns with a high critical-hit ratio. Always crits in Overgrowth.",
    ),
    "Hail of Briars": Move(
        "Hail of Briars",
        "Verdant",
        80,
        100,
        self_effect="weaken",
        description="A wild attack that weakens the user's own attack afterwards.",
    ),
    "Undergrowth Eruption": Move(
        "Undergrowth Eruption",
        "Verdant",
        45,
        100,
        guard_multiplier=2.5,
        description="Roots burst from the ground, effectively depleting enemy Guard.",
    ),
    "Wrath Of The Ancients": Move(
        "Wrath Of The Ancients",
        "Verdant",
        90,
        90,
        charge_turns=1,
        description="User takes root for a turn, then unleashes a devastating attack.",
    ),
    "Nature's Reach": Move(
        "Nature's Reach",
        "Verdant",
        60,
        101,
        description="A cloud of spores that never misses.",
    ),
    "Cut Of The Wild": Move(
        "Cut Of The Wild",
        "Verdant",
        90,
        100,
        self_effect="vulnerable",
        description="A flurry of blows that leaves the user vulnerable.",
    ),
    "Leeching Grasp": Move(
        "Leeching Grasp",
        "Verdant",
        50,
        100,
        description="An attack that heals the user for 50% of the damage dealt.",
    ),
    "Barkskin": Move(
        "Barkskin",
        "Verdant",
        0,
        100,
        target_type="self",
        self_effect="attack_up_1_defense_up_1",
        description="Hardens the user's skin, raising Attack and Defense by 1 stage.",
    ),
    "Ensnaring Vines": Move(
        "Ensnaring Vines",
        "Verdant",
        0,
        90,
        effect="slowed",
        effect_chance=100,
        description="Vines erupt to ensnare and slow the target.",
    ),
    # Radiant
    "Daylight": Move(
        "Daylight",
        "Radiant",
        0,
        100,
        sets_weather="Blazing Sun",
        description="Summons a Blazing Sun for 5 turns.",
    ),
    "Blazing Judgment": Move(
        "Blazing Judgment",
        "Radiant",
        80,
        90,
        charge_turns=1,
        description="Absorbs light for one turn, then fires. Fires instantly in Blazing Sun.",
    ),
    "Sacred Blade": Move(
        "Sacred Blade",
        "Radiant",
        45,
        100,
        effect="burn",
        effect_chance=30,
        description="A flaming sword strike that may burn the target.",
    ),
    "Solar Flare": Move(
        "Solar Flare",
        "Radiant",
        0,
        80,
        target_type="all_enemies",
        effect="dazed",
        effect_chance=25,
        description="A flash of light that may daze all opponents.",
    ),
    "Angelic Cut": Move(
        "Angelic Cut",
        "Radiant",
        65,
        100,
        description="A holy strike that ignores the target's defensive stat changes.",
    ),
    "Sunfire Burst": Move(
        "Sunfire Burst",
        "Radiant",
        70,
        100,
        effect="burn",
        effect_chance=10,
        description="A powerful blast of fire that may burn the target.",
    ),
    "Divine Light": Move(
        "Divine Light",
        "Radiant",
        0,
        85,
        effect="burn",
        effect_chance=100,
        description="A ghostly flame that is guaranteed to burn the target.",
    ),
    "Heavenly Blessing": Move(
        "Heavenly Blessing",
        "Radiant",
        0,
        100,
        target_type="single_ally",
        description="Heals an ally. Heals more in Blazing Sun.",
    ),
    "Blaze of Fury": Move(
        "Blaze of Fury",
        "Radiant",
        85,
        100,
        self_effect="recoil_33",
        effect="burn",
        effect_chance=10,
        description="A powerful, fiery charge that causes recoil and may burn the target.",
    ),
    "Fiery Immolation": Move(
        "Fiery Immolation",
        "Radiant",
        60,
        100,
        target_type="all_enemies",
        effect="burn",
        effect_chance=30,
        description="A burst of fire that hits all adjacent Knights and may burn them.",
    ),
    "Consecration": Move(
        "Consecration",
        "Radiant",
        0,
        100,
        target_type="team_synergy",
        synergy_effect="consecration",
        effect_duration=3,
        description="For 3 turns, if the user's ally is also Radiant-type, any foe that makes contact with either is burned.",
    ),
    # Shadow
    "Eclipse": Move(
        "Eclipse",
        "Shadow",
        0,
        100,
        sets_weather="Veil of Shadows",
        description="Casts a Veil of Shadows for 5 turns, boosting Shadow moves.",
    ),
    "Dread Pulse": Move(
        "Dread Pulse",
        "Shadow",
        55,
        100,
        target_type="all_enemies",
        effect="dazed",
        effect_chance=15,
        description="An aura of dark energy. Effect chance doubles in Veil of Shadows.",
    ),
    "Malediction": Move(
        "Malediction",
        "Shadow",
        0,
        90,
        effect="cursed",
        effect_chance=100,
        description="Curses the target, causing them to take damage when they attack.",
    ),
    "Shadow Blade": Move(
        "Shadow Blade",
        "Shadow",
        50,
        100,
        description="Deals double damage if the target has a status condition.",
    ),
    "Umbral Step": Move(
        "Umbral Step",
        "Shadow",
        60,
        100,
        charge_turns=1,
        description="Vanishes for a turn, then strikes, bypassing protection.",
    ),
    "Shadow Claw": Move(
        "Shadow Claw",
        "Shadow",
        50,
        100,
        priority=1,
        description="An attack that strikes before most others, but fails if the target isn't attacking.",
    ),
    "Dark Machinations": Move(
        "Dark Machinations",
        "Shadow",
        0,
        100,
        target_type="self",
        self_effect="attack_up_2",
        description="Sharply raises the user's Attack with wicked thoughts.",
    ),
    "Entice": Move(
        "Entice",
        "Shadow",
        0,
        100,
        effect="taunt",
        effect_chance=100,
        description="Forces the target to only use attacking moves for a few turns.",
    ),
    "Void Warp": Move(
        "Void Warp",
        "Shadow",
        70,
        100,
        description="Uses the target's Attack stat instead of the user's to calculate damage.",
    ),
    "Lingering Ghosts": Move(
        "Lingering Ghosts",
        "Shadow",
        0,
        100,
        effect="weaken",
        effect_chance=100,
        description="Lowers the target's Attack, then the user switches out.",
    ),
    "Shared Shadow": Move(
        "Shared Shadow",
        "Shadow",
        0,
        100,
        target_type="team_synergy",
        synergy_effect="invisible",
        effect_duration=3,
        description="If the user's ally is also Shadow-type, both become invisible for 3 turns.",
    ),
    # Cryo
    "Blizzard": Move(
        "Blizzard",
        "Cryo",
        0,
        100,
        sets_weather="Hailstorm",
        description="Summons a hailstorm for 5 turns. Boosts Cryo-type Defense and may slow foes.",
    ),
    "Rimefall": Move(
        "Rimefall",
        "Cryo",
        80,
        70,
        target_type="all_enemies",
        effect="dazed",
        effect_chance=10,
        description="A harsh snowstorm that never misses in a Hailstorm.",
    ),
    "Frozen Slash": Move(
        "Frozen Slash",
        "Cryo",
        30,
        90,
        effect="slowed",
        effect_chance=100,
        description="A chilling attack that slows the target.",
    ),
    "Avalanche": Move(
        "Avalanche",
        "Cryo",
        60,
        90,
        description="A powerful avalanche. Power doubles if the user was hit this turn.",
    ),
    "Icicle Spear": Move(
        "Icicle Spear",
        "Cryo",
        40,
        100,
        priority=1,
        description="A sharp shard of ice is fired at the target before most others.",
    ),
    "Cryo Beam": Move(
        "Cryo Beam",
        "Cryo",
        70,
        100,
        effect="dazed",
        effect_chance=10,
        description="A powerful beam of ice that may daze the target.",
    ),
    "Mists of Borealis": Move(
        "Mists of Borealis",
        "Cryo",
        0,
        100,
        target_type="team_synergy",
        priority=4,
        synergy_effect="mists_of_borealis",
        effect_duration=3,
        description="For 3 turns, halves damage from all attacks for the user and their Cryo ally. Only works in a Hailstorm.",
    ),
    "Glacial Crash": Move(
        "Glacial Crash",
        "Cryo",
        65,
        90,
        effect="dazed",
        effect_chance=30,
        description="Drops a large icicle on the target, which may cause it to flinch.",
    ),
    "Deep Freeze": Move(
        "Deep Freeze",
        "Cryo",
        0,
        100,
        target_type="all_enemies",
        description="Eliminates all stat changes for all Knights on the field.",
    ),
    "Dessicating Frost": Move(
        "Dessicating Frost",
        "Cryo",
        55,
        100,
        description="An attack that is super-effective against Radiant types.",
    ),
    "Winter's Embrace": Move(
        "Winter's Embrace",
        "Cryo",
        0,
        100,
        target_type="team_synergy",
        self_effect="attack_up_1_defense_up_1",
        description="If the user's ally is also Cryo-type, raises the Attack and Defense of both by one stage.",
    ),
    # Storm
    "Call Thunder": Move(
        "Call Thunder",
        "Storm",
        0,
        100,
        sets_weather="Thunderstorm",
        description="Summons a thunderstorm for 5 turns.",
    ),
    "Storm's Wrath": Move(
        "Storm's Wrath",
        "Storm",
        70,
        100,
        effect="dazed",
        effect_chance=10,
        description="A strong electrical attack. Never misses in a Thunderstorm.",
    ),
    "Unleash The Tempest": Move(
        "Unleash The Tempest",
        "Storm",
        75,
        100,
        rampage_turns=2,
        self_effect="dazed",
        description="User rampages for 2-3 turns, then becomes dazed.",
    ),
    "Static Discharge": Move(
        "Static Discharge",
        "Storm",
        55,
        90,
        target_type="all_enemies",
        description="Releases a wave of electricity to hit all foes.",
    ),
    "Galvanic Charge": Move(
        "Galvanic Charge",
        "Storm",
        80,
        100,
        self_effect="recoil_33",
        description="A powerful, full-body tackle that also causes 1/3 recoil damage to the user.",
    ),
    "Paralyzing Jolt": Move(
        "Paralyzing Jolt",
        "Storm",
        0,
        90,
        effect="dazed",
        effect_chance=100,
        description="A jolt of electricity that is guaranteed to daze the target.",
    ),
    "Arcing Rebound": Move(
        "Arcing Rebound",
        "Storm",
        50,
        100,
        description="After attacking, the user switches out of battle.",
    ),
    "Supercharge": Move(
        "Supercharge",
        "Storm",
        70,
        100,
        self_effect="recoil_25",
        description="An electrified tackle that also causes recoil damage.",
    ),
    "Stasis Field": Move(
        "Stasis Field",
        "Storm",
        0,
        100,
        target_type="all_enemies",
        effect="weaken",
        effect_chance=100,
        description="Sharply lowers the Attack of all opposing Knights.",
    ),
    "Volt Nova": Move(
        "Volt Nova",
        "Storm",
        60,
        100,
        target_type="all_enemies",
        effect="dazed",
        effect_chance=30,
        description="Hits all adjacent Knights and may daze them.",
    ),
    "Eye of the Storm": Move(
        "Eye of the Storm",
        "Storm",
        0,
        100,
        target_type="team_synergy",
        synergy_effect="eye_of_the_storm",
        effect_duration=3,
        description="For 3 turns, if the user's ally is also Storm-type, grants both a 30% chance to evade attacks.",
    ),
}

ALL_KNIGHTS = {
    "Aegis": KnightTemplate(
        "Aegis",
        "Steel",
        250,
        40,
        70,
        30,
        [
            "Empowered Strike",
            "Iron Brace",
            "Guard Bash",
            "Royal Aegis",
            "Crucible of Metal",
            "Bulwark Charge",
            "Steel Plating",
            "Parry",
            "Phalanx",
        ],
    ),
    "Briarheart": KnightTemplate(
        "Briarheart",
        "Verdant",
        180,
        60,
        35,
        50,
        [
            "Hail of Briars",
            "Undergrowth Eruption",
            "Wrath Of The Ancients",
            "Cutting Blow",
            "Onslaught Of Thorns",
            "Leeching Grasp",
            "Ensnaring Vines",
            "Vine Whip",
        ],
    ),
    "Sol": KnightTemplate(
        "Sol",
        "Radiant",
        195,
        58,
        40,
        60,
        [
            "Sacred Blade",
            "Blazing Judgment",
            "Solar Flare",
            "Angelic Cut",
            "Daylight",
            "Heavenly Blessing",
            "Swift Strike",
            "Consecration",
        ],
    ),
    "Nocturne": KnightTemplate(
        "Nocturne",
        "Shadow",
        180,
        55,
        30,
        70,
        [
            "Malediction",
            "Dread Pulse",
            "Umbral Step",
            "Eclipse",
            "Shadow Blade",
            "Dark Machinations",
            "Shadow Claw",
            "Shared Shadow",
        ],
    ),
    "Boreas": KnightTemplate(
        "Boreas",
        "Cryo",
        220,
        40,
        60,
        40,
        [
            "Icicle Spear",
            "Frozen Slash",
            "Avalanche",
            "Blizzard",
            "Rimefall",
            "Mists of Borealis",
            "Winter's Embrace",
        ],
    ),
    "Indra": KnightTemplate(
        "Indra",
        "Storm",
        185,
        60,
        38,
        80,
        [
            "Unleash The Tempest",
            "Static Discharge",
            "Call Thunder",
            "Storm's Wrath",
            "Paralyzing Jolt",
            "Arcing Rebound",
            "Swift Strike",
            "Eye of the Storm",
        ],
    ),
}
