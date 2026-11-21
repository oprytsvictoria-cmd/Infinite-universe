from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from core.text import Document, DocumentBuilder


class Item:
    def __init__(self, name: str, bonus: int = 0, description: str = ""):
        self._name = name
        self._bonus = bonus
        self._description = description

    @property
    def name(self) -> str: return self._name

    @property
    def bonus(self) -> int: return self._bonus

    @property
    def description(self) -> str: return self._description


class Weapon(Item):
    pass


class Armor(Item):
    pass


class CombatMath:
    """Stateless mathematical combat formulas."""

    @staticmethod
    def calculate_damage(attacker_atk: int, target_arm: int) -> int:
        return max(1, attacker_atk - target_arm)

    @staticmethod
    def calculate_shield_slam(attacker_atk: int, attacker_arm: int) -> int:
        return attacker_atk + (attacker_arm // 2)

    @staticmethod
    def calculate_pyroblast(attacker_atk: int):
        magic_damage = attacker_atk * 2
        return magic_damage, magic_damage // 3


# ==============================================================================
# STRATEGY PATTERN
# Purpose: Encapsulates interchangeable combat algorithms (Melee, Shield Slam,
# Pyroblast) so characters can switch attack styles dynamically at runtime.
# ==============================================================================
class IAttackStrategy(ABC):
    @abstractmethod
    def execute_attack(self, attacker: 'Character', target: 'Character') -> str: pass


class MeleeAttackStrategy(IAttackStrategy):
    def execute_attack(self, attacker: 'Character', target: 'Character') -> str:
        damage = CombatMath.calculate_damage(attacker.total_attack_power, target.total_armor)
        target.health -= damage
        return f"[MELEE] {attacker.name} strikes {target.name} for {damage} physical damage!"


class ShieldSlamStrategy(IAttackStrategy):
    def execute_attack(self, attacker: 'Character', target: 'Character') -> str:
        raw = CombatMath.calculate_shield_slam(attacker.total_attack_power, attacker.total_armor)
        damage = max(1, raw - target.total_armor)
        target.health -= damage
        return f"[SHIELD] {attacker.name} slams {target.name} with a shield for {damage} damage!"


class PyroblastAttackStrategy(IAttackStrategy):
    def execute_attack(self, attacker: 'Character', target: 'Character') -> str:
        dmg, recoil = CombatMath.calculate_pyroblast(attacker.total_attack_power)
        target.health -= dmg
        attacker.health -= recoil
        return f"[MAGIC] {attacker.name} blasts {target.name} for {dmg} magic damage (took {recoil} recoil)!"


# ==============================================================================
# OBSERVER PATTERN
# Purpose: Decouples domain events inside GameEngine from CLI presenters.
# ==============================================================================
class IGameObserver(ABC):
    @abstractmethod
    def on_game_event(self, event_type: str, message: str) -> None: pass


class GameEventManager:
    def __init__(self):
        self._observers: List[IGameObserver] = []

    def subscribe(self, observer: IGameObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def notify(self, event_type: str, message: str) -> None:
        for observer in self._observers:
            observer.on_game_event(event_type, message)


class Character(ABC):
    """Base Character entity supporting Strategy attacks, Graphics URL, and Serialization."""

    def __init__(self, name: str, health: int, armor: int, attack_power: int,
                 description: str = "", abilities: List[Dict[str, str]] = None,
                 image_url: str = "", attack_strategy: Optional[IAttackStrategy] = None):
        self._name = name
        self._max_health = health
        self._health = health
        self._base_armor = armor
        self._base_attack_power = attack_power
        self._description = description
        self._abilities = abilities or []
        self._image_url = image_url or f"https://genshin.jmp.blue/characters/{name.lower().replace(' ', '-')}/icon-big"
        self._weapon: Optional[Weapon] = None
        self._armor_gear: Optional[Armor] = None
        self._attack_strategy: IAttackStrategy = attack_strategy or MeleeAttackStrategy()

    @property
    def name(self) -> str: return self._name

    @property
    def health(self) -> int: return self._health

    @health.setter
    def health(self, value: int):
        self._health = max(0, min(value, self._max_health))

    @property
    def max_health(self) -> int: return self._max_health

    @property
    def total_attack_power(self) -> int:
        return self._base_attack_power + (self._weapon.bonus if self._weapon else 0)

    @property
    def total_armor(self) -> int:
        return self._base_armor + (self._armor_gear.bonus if self._armor_gear else 0)

    @property
    def description(self) -> str: return self._description

    @property
    def image_url(self) -> str: return self._image_url

    @property
    def abilities(self) -> List[Dict[str, str]]: return self._abilities

    @property
    def attack_strategy(self) -> IAttackStrategy: return self._attack_strategy

    def set_attack_strategy(self, strategy: IAttackStrategy) -> None:
        self._attack_strategy = strategy

    def reset_health(self) -> None:
        self._health = self._max_health

    def attack(self, target: 'Character') -> str:
        return self._attack_strategy.execute_attack(self, target)

    def equip_item(self, item: Item) -> str:
        if isinstance(item, Weapon):
            self._weapon = item
            return f"[{self._name}] equipped weapon: {item.name} (+{item.bonus} ATK)"
        elif isinstance(item, Armor):
            self._armor_gear = item
            return f"[{self._name}] equipped armor: {item.name} (+{item.bonus} ARM)"
        return ""

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the character into a dictionary for JSON persistence."""
        return {
            "name": self._name,
            "class": self.__class__.__name__,
            "max_health": self._max_health,
            "armor": self._base_armor,
            "attack_power": self._base_attack_power,
            "description": self._description,
            "image_url": self._image_url,
            "abilities": self._abilities
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Character':
        """Reconstructs a Character instance from a JSON dictionary."""
        char_cls = Mage if data.get("class") == "Mage" else Warrior
        return char_cls(
            name=data["name"],
            health=data["max_health"],
            armor=data["armor"],
            attack_power=data["attack_power"],
            description=data.get("description", ""),
            abilities=data.get("abilities", []),
            image_url=data.get("image_url", "")
        )

    def to_document(self) -> Document:
        """Generates a structured Document dossier including portrait link."""
        builder = DocumentBuilder(f"Character Dossier: {self._name}")
        builder.add_heading(self._name, level=1)
        builder.add_paragraph(f"Class: {self.__class__.__name__}")
        builder.add_paragraph(f"Description: {self._description}")
        builder.add_image(f"{self._name} Portrait", self._image_url)

        builder.add_heading("Combat Specifications", level=2)
        builder.add_paragraph(f"Health (HP): {self._health}/{self._max_health}")
        builder.add_paragraph(f"Attack (ATK): {self.total_attack_power} (Base: {self._base_attack_power})")
        builder.add_paragraph(f"Armor (ARM): {self.total_armor}")
        builder.add_paragraph(f"Active Strategy: {self._attack_strategy.__class__.__name__}")

        if self._abilities:
            builder.add_heading("Abilities", level=2)
            for ab in self._abilities:
                builder.add_heading(ab.get("name", "Skill"), level=3)
                builder.add_paragraph(ab.get("description", ""))

        return builder.get_document()


class Warrior(Character):
    def __init__(self, name: str, health: int, armor: int, attack_power: int,
                 description: str = "", abilities: List[Dict[str, str]] = None, image_url: str = ""):
        super().__init__(name, health, armor, attack_power, description, abilities,
                         image_url, attack_strategy=MeleeAttackStrategy())


class Mage(Character):
    def __init__(self, name: str, health: int, armor: int, attack_power: int,
                 description: str = "", abilities: List[Dict[str, str]] = None, image_url: str = ""):
        super().__init__(name, health, armor, attack_power, description, abilities,
                         image_url, attack_strategy=PyroblastAttackStrategy())


class GameEngine:
    """Manages the character roster and turn-based combat game loop state."""

    def __init__(self):
        self._characters: List[Character] = []
        self._items: List[Item] = []
        self.events = GameEventManager()

        # Turn-based game state (Topic 2)
        self.player1: Optional[Character] = None
        self.player2: Optional[Character] = None
        self.active_turn: int = 1
        self.game_started: bool = False
        self.winner: Optional[str] = None
        self.battle_log: List[str] = []

    @property
    def characters(self) -> List[Character]:
        return self._characters

    def add_character(self, char: Character) -> int:
        self._characters.append(char)
        idx = len(self._characters) - 1
        self.events.notify("CATALOG", f"Added character [{idx}] {char.name}")
        return idx

    def select_fighters(self, idx1: int, idx2: int) -> None:
        if idx1 == idx2:
            raise ValueError("Please select two different characters for the match.")
        self.player1 = self._characters[idx1]
        self.player2 = self._characters[idx2]
        self.game_started = False
        self.winner = None
        self.events.notify("GAME", f"Selected fighters: {self.player1.name} vs {self.player2.name}")

    def start_game(self) -> None:
        if not self.player1 or not self.player2:
            raise ValueError("Select two characters first using 'select <id1> <id2>'.")
        self.player1.reset_health()
        self.player2.reset_health()
        self.active_turn = 1
        self.game_started = True
        self.winner = None
        self.battle_log = [f"Match started: {self.player1.name} vs {self.player2.name}"]
        self.events.notify("GAME", self.battle_log[-1])

    def execute_turn_attack(self) -> str:
        if not self.game_started or self.winner:
            raise RuntimeError("No active match in progress. Use 'start' to begin.")

        attacker = self.player1 if self.active_turn == 1 else self.player2
        defender = self.player2 if self.active_turn == 1 else self.player1

        log = attacker.attack(defender)
        self.battle_log.append(log)
        self.events.notify("COMBAT", log)

        if defender.health <= 0:
            self.winner = attacker.name
            self.game_started = False
            win_msg = f"Match Over! Winner: {self.winner}!"
            self.battle_log.append(win_msg)
            self.events.notify("GAME_OVER", win_msg)
        elif attacker.health <= 0:
            self.winner = defender.name
            self.game_started = False
            win_msg = f"Match Over! Winner: {self.winner} (opponent defeated by recoil)!"
            self.battle_log.append(win_msg)
            self.events.notify("GAME_OVER", win_msg)
        else:
            self.active_turn = 2 if self.active_turn == 1 else 1

        return log

    def get_match_summary(self) -> Dict[str, Any]:
        return {
            "player1": self.player1.name if self.player1 else None,
            "player1_hp": self.player1.health if self.player1 else 0,
            "player2": self.player2.name if self.player2 else None,
            "player2_hp": self.player2.health if self.player2 else 0,
            "winner": self.winner,
            "turns_played": len(self.battle_log),
            "battle_log": self.battle_log
        }

    def setup_demo(self) -> None:
        if self._characters:
            return
        thorin = Warrior(
            "Thorin Ironshield", 120, 15, 18,
            "Veteran dwarven defender of the Mountain Kingdom.",
            image_url="https://example.com/assets/characters/thorin.png"
        )
        jaina = Mage(
            "Jaina Spellweaver", 90, 6, 22,
            "Archmage specializing in high-risk pyromancy.",
            image_url="https://example.com/assets/characters/jaina.png"
        )
        self._characters.extend([thorin, jaina])
