# Mafia Game Rules

## Roles

1. **Mafia** - Knows who other mafia members are. Can kill one villager each night.
2. **Villager** - Regular citizen with no special abilities. Can vote during the day.
3. **Doctor** - Can protect one player each night from Mafia kills.

## Game Structure

1. **Game Setup**:

   - Assign roles to each LLM randomly
   - Inform Mafia members of each other's identities
   - Other players know only their own roles

2. **Game Phases**:

   - **Night Phase**:
     - Mafia selects a player to kill
     - Doctor selects a player to save
   - **Day Phase**:
     - All surviving players discuss and vote to eliminate one player
     - Player with most votes is identified
     - A confirmation vote is held to determine if this player should be eliminated
     - Player is eliminated only if the majority votes to confirm

3. **Win Conditions**:
   - **Mafia wins** when they equal or outnumber the villagers
   - **Villagers win** when all Mafia members are eliminated

## Standard Game Configuration

- 4-8 players total
- 1-2 Mafia members
- 1 Doctor
- Remaining players are Villagers
