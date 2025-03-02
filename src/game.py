"""
Game logic for the LLM Mafia Game Competition.
"""

import random
import uuid
from player import Player, Role
import config


class MafiaGame:
    """Represents a Mafia game with LLM players."""

    def __init__(self, models=None):
        """
        Initialize a Mafia game.

        Args:
            models (list, optional): List of model names to use as players.
        """
        self.game_id = str(uuid.uuid4())
        self.round_number = 0
        self.phase = "setup"  # setup, night, day
        self.players = []
        self.mafia_players = []
        self.doctor_player = None
        self.villager_players = []
        self.discussion_history = ""
        self.rounds_data = []
        self.current_round_data = {
            "round_number": 0,
            "messages": [],
            "actions": {},
            "eliminations": [],
            "outcome": "",
        }

        # Use provided models or default from config
        self.models = models if models else config.MODELS

        # Set random seed if specified
        if config.RANDOM_SEED is not None:
            random.seed(config.RANDOM_SEED)

    def setup_game(self):
        """
        Set up the game by assigning roles to players.

        Returns:
            bool: True if setup successful, False otherwise.
        """
        # Check if we have enough models
        if len(self.models) < config.PLAYERS_PER_GAME:
            print(
                f"Not enough models. Need {config.PLAYERS_PER_GAME}, but only have {len(self.models)}."
            )
            return False

        # Randomly select models for this game
        selected_models = random.sample(self.models, config.PLAYERS_PER_GAME)

        # Assign roles
        roles = []

        # Add Mafia roles
        for _ in range(config.MAFIA_COUNT):
            roles.append(Role.MAFIA)

        # Add Doctor roles
        for _ in range(config.DOCTOR_COUNT):
            roles.append(Role.DOCTOR)

        # Add Villager roles
        villager_count = (
            config.PLAYERS_PER_GAME - config.MAFIA_COUNT - config.DOCTOR_COUNT
        )
        for _ in range(villager_count):
            roles.append(Role.VILLAGER)

        # Shuffle roles
        random.shuffle(roles)

        # Create players
        for i, model_name in enumerate(selected_models):
            player = Player(model_name, roles[i])
            self.players.append(player)

            # Add to role-specific lists
            if player.role == Role.MAFIA:
                self.mafia_players.append(player)
            elif player.role == Role.DOCTOR:
                self.doctor_player = player
            else:  # Role.VILLAGER
                self.villager_players.append(player)

        # Set phase to night
        self.phase = "night"
        self.round_number = 1
        self.current_round_data = {
            "round_number": self.round_number,
            "messages": [],
            "actions": {},
            "eliminations": [],
            "outcome": "",
        }

        print(
            f"Game setup complete. {len(self.players)} players, {len(self.mafia_players)} Mafia, {len(self.villager_players)} Villagers, {1 if self.doctor_player else 0} Doctor."
        )
        return True

    def get_game_state(self):
        """
        Get the current state of the game as a string.

        Returns:
            str: The current game state.
        """
        alive_count = sum(1 for p in self.players if p.alive)
        mafia_count = sum(1 for p in self.mafia_players if p.alive)
        villager_count = sum(1 for p in self.villager_players if p.alive)
        doctor_count = 1 if self.doctor_player and self.doctor_player.alive else 0

        state = f"Round {self.round_number}, {self.phase.capitalize()} phase. "
        state += f"{alive_count} players alive ({mafia_count} Mafia, {villager_count + doctor_count} Villagers/Doctor). "

        if self.round_number > 1:
            state += f"In the previous round, {', '.join(self.current_round_data['eliminations'])} {'was' if len(self.current_round_data['eliminations']) == 1 else 'were'} eliminated. "

        return state

    def get_alive_players(self):
        """
        Get a list of alive players.

        Returns:
            list: List of alive players.
        """
        return [p for p in self.players if p.alive]

    def check_game_over(self):
        """
        Check if the game is over.

        Returns:
            tuple: (is_game_over, winner) where winner is "Mafia" or "Villagers" or None.
        """
        # Count alive players by role
        mafia_alive = sum(1 for p in self.mafia_players if p.alive)
        villagers_alive = sum(1 for p in self.villager_players if p.alive)
        doctor_alive = 1 if self.doctor_player and self.doctor_player.alive else 0

        # Check win conditions
        if mafia_alive == 0:
            return True, "Villagers"
        elif mafia_alive >= (villagers_alive + doctor_alive):
            return True, "Mafia"
        elif self.round_number >= config.MAX_ROUNDS:
            # Draw, but we'll count it as a villager win if there are more villagers than mafia
            if villagers_alive + doctor_alive > mafia_alive:
                return True, "Villagers"
            else:
                return True, "Mafia"

        return False, None

    def execute_night_phase(self):
        """
        Execute the night phase of the game.

        Returns:
            list: List of eliminated players.
        """
        print(f"\n--- Night Phase (Round {self.round_number}) ---")

        # Reset protected status
        for player in self.players:
            player.protected = False

        # Get actions from Mafia players
        mafia_targets = []
        for player in self.mafia_players:
            if player.alive:
                # Generate prompt
                game_state = (
                    f"{self.get_game_state()} It's night time. Choose a player to kill."
                )
                prompt = player.generate_prompt(
                    game_state, self.get_alive_players(), self.mafia_players
                )

                # Get response
                response = player.get_response(prompt)
                print(f"{player.model_name} (Mafia) response: {response}")

                # Parse action
                action_type, target = player.parse_night_action(
                    response, self.get_alive_players()
                )

                if action_type == "kill" and target:
                    mafia_targets.append(target)
                    self.current_round_data["actions"][
                        player.model_name
                    ] = f"Kill {target.model_name}"
                else:
                    print(f"Invalid action from {player.model_name} (Mafia)")
                    self.current_round_data["actions"][
                        player.model_name
                    ] = "Invalid action"

        # Determine Mafia kill target (majority vote)
        kill_target = None
        if mafia_targets:
            # Count votes for each target
            target_counts = {}
            for target in mafia_targets:
                if target.model_name in target_counts:
                    target_counts[target.model_name] += 1
                else:
                    target_counts[target.model_name] = 1

            # Find target with most votes
            max_votes = 0
            for target_name, votes in target_counts.items():
                if votes > max_votes:
                    max_votes = votes
                    for player in self.get_alive_players():
                        if player.model_name == target_name:
                            kill_target = player
                            break

        # Get action from Doctor
        protected_player = None
        if self.doctor_player and self.doctor_player.alive:
            # Generate prompt
            game_state = (
                f"{self.get_game_state()} It's night time. Choose a player to protect."
            )
            prompt = self.doctor_player.generate_prompt(
                game_state, self.get_alive_players()
            )

            # Get response
            response = self.doctor_player.get_response(prompt)
            print(f"{self.doctor_player.model_name} (Doctor) response: {response}")

            # Parse action
            action_type, target = self.doctor_player.parse_night_action(
                response, self.get_alive_players()
            )

            if action_type == "protect" and target:
                protected_player = target
                target.protected = True
                self.current_round_data["actions"][
                    self.doctor_player.model_name
                ] = f"Protect {target.model_name}"
            else:
                print(f"Invalid action from {self.doctor_player.model_name} (Doctor)")
                self.current_round_data["actions"][
                    self.doctor_player.model_name
                ] = "Invalid action"

        # Process night actions
        eliminated_players = []
        if kill_target and not kill_target.protected:
            kill_target.alive = False
            eliminated_players.append(kill_target)
            self.current_round_data["eliminations"].append(kill_target.model_name)
            self.current_round_data["outcome"] = (
                f"{kill_target.model_name} was killed by the Mafia."
            )
            print(f"{kill_target.model_name} was killed by the Mafia.")
        else:
            if kill_target and kill_target.protected:
                self.current_round_data["outcome"] = (
                    f"The Doctor protected {kill_target.model_name} from the Mafia."
                )
                print(f"The Doctor protected {kill_target.model_name} from the Mafia.")
            else:
                self.current_round_data["outcome"] = (
                    "No one was killed during the night."
                )
                print("No one was killed during the night.")

        # Set phase to day
        self.phase = "day"

        return eliminated_players

    def execute_day_phase(self):
        """
        Execute the day phase of the game.

        Returns:
            list: List of eliminated players.
        """
        print(f"\n--- Day Phase (Round {self.round_number}) ---")

        # Get alive players
        alive_players = self.get_alive_players()

        # Collect messages and votes from all alive players
        messages = []
        votes = {}

        for player in alive_players:
            # Generate prompt
            game_state = f"{self.get_game_state()} It's day time. Discuss with other players and vote to eliminate a suspected Mafia member."
            prompt = player.generate_prompt(
                game_state,
                alive_players,
                self.mafia_players if player.role == Role.MAFIA else None,
                self.discussion_history,
            )

            # Get response
            response = player.get_response(prompt)
            print(f"{player.model_name} ({player.role.value}) response: {response}")

            # Add to messages
            messages.append({"speaker": player.model_name, "content": response})
            self.current_round_data["messages"].append(
                {"speaker": player.model_name, "content": response}
            )

            # Parse vote
            vote_target = player.parse_day_vote(response, alive_players)
            if vote_target:
                votes[player.model_name] = vote_target.model_name
                self.current_round_data["actions"][
                    player.model_name
                ] = f"Vote {vote_target.model_name}"
            else:
                print(f"Invalid vote from {player.model_name}")
                self.current_round_data["actions"][player.model_name] = "Invalid vote"

        # Update discussion history
        for message in messages:
            self.discussion_history += f"{message['speaker']}: {message['content']}\n\n"

        # Count votes
        vote_counts = {}
        for voter, target_name in votes.items():
            if target_name in vote_counts:
                vote_counts[target_name] += 1
            else:
                vote_counts[target_name] = 1

        # Find player with most votes
        max_votes = 0
        eliminated_player = None

        for target_name, vote_count in vote_counts.items():
            if vote_count > max_votes:
                max_votes = vote_count
                for player in alive_players:
                    if player.model_name == target_name:
                        eliminated_player = player
                        break

        # Eliminate player with most votes
        eliminated_players = []
        if eliminated_player:
            eliminated_player.alive = False
            eliminated_players.append(eliminated_player)
            self.current_round_data["eliminations"].append(eliminated_player.model_name)
            self.current_round_data[
                "outcome"
            ] += f" {eliminated_player.model_name} was eliminated by vote."
            print(f"{eliminated_player.model_name} was eliminated by vote.")
        else:
            self.current_round_data["outcome"] += " No one was eliminated by vote."
            print("No one was eliminated by vote.")

        # Set phase to night and increment round
        self.phase = "night"
        self.rounds_data.append(self.current_round_data)
        self.round_number += 1
        self.current_round_data = {
            "round_number": self.round_number,
            "messages": [],
            "actions": {},
            "eliminations": [],
            "outcome": "",
        }

        return eliminated_players

    def run_game(self):
        """
        Run the Mafia game until completion.

        Returns:
            tuple: (winner, rounds_data, participants) where winner is "Mafia" or "Villagers".
        """
        # Setup game
        if not self.setup_game():
            return None, [], {}

        # Game loop
        game_over = False
        winner = None

        while not game_over:
            # Check if game is over
            game_over, winner = self.check_game_over()
            if game_over:
                break

            # Execute night phase
            self.execute_night_phase()

            # Check if game is over after night phase
            game_over, winner = self.check_game_over()
            if game_over:
                break

            # Execute day phase
            self.execute_day_phase()

        # Add final round data if not already added
        if self.current_round_data["round_number"] > 0:
            self.rounds_data.append(self.current_round_data)

        # Create participants dictionary
        participants = {}
        for player in self.players:
            participants[player.model_name] = player.role.value

        print(f"\n--- Game Over ---")
        print(f"Winner: {winner}")
        print(f"Rounds: {self.round_number}")

        return winner, self.rounds_data, participants
