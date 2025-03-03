"""
Game logic for the LLM Mafia Game Competition.
"""

import random
import uuid
from player import Player, Role
import config
from logger import GameLogger, Color


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
            "eliminated_by_vote": [],  # New field to track players eliminated by vote
            "outcome": "",
        }

        # Use provided models or default from config
        self.models = models if models else config.MODELS

        # Set random seed if specified
        if config.RANDOM_SEED is not None:
            random.seed(config.RANDOM_SEED)

        # Initialize logger
        self.logger = GameLogger()

    def setup_game(self):
        """
        Set up the game by assigning roles to players.

        Returns:
            bool: True if setup successful, False otherwise.
        """
        # Check if we have enough models
        if len(self.models) < config.PLAYERS_PER_GAME:
            self.logger.error(
                f"Not enough models. Need {config.PLAYERS_PER_GAME}, but only have {len(self.models)}."
            )
            return False

        # Log game start
        self.logger.game_start(1, self.game_id)

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
        self.logger.header("PLAYER SETUP", Color.CYAN)
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

            # Log player setup
            self.logger.player_setup(player.model_name, player.role.value)

        # Set phase to night
        self.phase = "night"
        self.round_number = 1
        self.current_round_data = {
            "round_number": self.round_number,
            "messages": [],
            "actions": {},
            "eliminations": [],
            "eliminated_by_vote": [],  # Reset for the new round
            "outcome": "",
        }

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
        self.logger.phase_header("Night", self.round_number)

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
                self.logger.player_response(player.model_name, "Mafia", response)

                # Add to messages with night phase marker
                self.current_round_data["messages"].append(
                    {
                        "speaker": player.model_name,
                        "content": response,
                        "phase": "night",
                        "role": "Mafia",
                    }
                )

                # Parse action
                action_type, target = player.parse_night_action(
                    response, self.get_alive_players()
                )

                if action_type == "kill" and target:
                    mafia_targets.append(target)
                    action_text = f"Kill {target.model_name}"
                    self.current_round_data["actions"][player.model_name] = action_text
                    self.logger.player_action(player.model_name, "Mafia", action_text)
                else:
                    self.logger.error(
                        f"Invalid action from {player.model_name} (Mafia)"
                    )
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
            self.logger.player_response(
                self.doctor_player.model_name, "Doctor", response
            )

            # Add to messages with night phase marker
            self.current_round_data["messages"].append(
                {
                    "speaker": self.doctor_player.model_name,
                    "content": response,
                    "phase": "night",
                    "role": "Doctor",
                }
            )

            # Parse action
            action_type, target = self.doctor_player.parse_night_action(
                response, self.get_alive_players()
            )

            if action_type == "protect" and target:
                protected_player = target
                target.protected = True
                action_text = f"Protect {target.model_name}"
                self.current_round_data["actions"][
                    self.doctor_player.model_name
                ] = action_text
                self.logger.player_action(
                    self.doctor_player.model_name, "Doctor", action_text
                )
            else:
                self.logger.error(
                    f"Invalid action from {self.doctor_player.model_name} (Doctor)"
                )
                self.current_round_data["actions"][
                    self.doctor_player.model_name
                ] = "Invalid action"

        # Process night actions
        eliminated_players = []
        if kill_target and not kill_target.protected:
            kill_target.alive = False
            eliminated_players.append(kill_target)
            self.current_round_data["eliminations"].append(kill_target.model_name)
            # Not adding to eliminated_by_vote since this is a night kill
            outcome_text = f"{kill_target.model_name} was killed by the Mafia."
            self.current_round_data["outcome"] = outcome_text
            self.logger.event(outcome_text, Color.RED)
        else:
            if kill_target and kill_target.protected:
                outcome_text = (
                    f"The Doctor protected {kill_target.model_name} from the Mafia."
                )
                self.current_round_data["outcome"] = outcome_text
                self.logger.event(outcome_text, Color.BLUE)
            else:
                outcome_text = "No one was killed during the night."
                self.current_round_data["outcome"] = outcome_text
                self.logger.event(outcome_text, Color.YELLOW)

        # Set phase to day
        self.phase = "day"

        return eliminated_players

    def execute_day_phase(self):
        """
        Execute the day phase of the game.

        Returns:
            list: List of eliminated players.
        """
        self.logger.phase_header("Day", self.round_number)

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
                self.discussion_history,  # Only contains day phase messages
            )

            # Get response
            response = player.get_response(prompt)
            self.logger.player_response(player.model_name, player.role.value, response)

            # Add to messages
            messages.append({"speaker": player.model_name, "content": response})
            self.current_round_data["messages"].append(
                {
                    "speaker": player.model_name,
                    "content": response,
                    "phase": "day",
                    "role": player.role.value,
                }
            )

            # Parse vote
            vote_target = player.parse_day_vote(response, alive_players)
            if vote_target:
                votes[player.model_name] = vote_target.model_name
                action_text = f"Vote {vote_target.model_name}"
                self.current_round_data["actions"][player.model_name] = action_text
                self.logger.player_action(
                    player.model_name, player.role.value, action_text
                )
            else:
                self.logger.error(f"Invalid vote from {player.model_name}")
                self.current_round_data["actions"][player.model_name] = "Invalid vote"

        # Update discussion history - only include day phase messages
        for message in messages:
            self.discussion_history += f"{message['speaker']}: {message['content']}\n\n"

        # Count votes
        vote_counts = {}
        vote_details = {}  # New dictionary to store who voted for whom
        for voter, target_name in votes.items():
            if target_name in vote_counts:
                vote_counts[target_name] += 1
            else:
                vote_counts[target_name] = 1

            # Store voter information for each target
            if target_name not in vote_details:
                vote_details[target_name] = []
            vote_details[target_name].append(voter)

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
            # Get confirmation vote before elimination
            is_confirmed, confirmation_votes = self.get_confirmation_vote(
                eliminated_player
            )

            # Store confirmation vote details in the round data
            self.current_round_data["confirmation_votes"] = confirmation_votes

            if not is_confirmed:
                confirmation_text = f"The elimination of {eliminated_player.model_name} was rejected by the town."
                self.current_round_data["outcome"] += f" {confirmation_text}"
                self.logger.event(confirmation_text, Color.YELLOW)

                # No elimination if confirmation vote fails
                eliminated_player = None
                eliminated_players = []

                # Store vote information even if no one was eliminated
                self.current_round_data["vote_counts"] = vote_counts
                self.current_round_data["vote_details"] = vote_details
            else:
                # Get last words from the player before elimination
                last_words = self.get_last_words(
                    eliminated_player, vote_counts[eliminated_player.model_name]
                )

                eliminated_player.alive = False
                eliminated_players.append(eliminated_player)
                self.current_round_data["eliminations"].append(
                    eliminated_player.model_name
                )
                # Add to eliminated_by_vote to track players eliminated by voting
                self.current_round_data["eliminated_by_vote"] = [
                    eliminated_player.model_name
                ]

                # Store vote details in the round data
                self.current_round_data["vote_counts"] = vote_counts
                self.current_round_data["vote_details"] = vote_details

                # Include vote count in the outcome text
                outcome_text = f"{eliminated_player.model_name} was eliminated by vote with {vote_counts[eliminated_player.model_name]} votes."
                self.current_round_data["outcome"] += f" {outcome_text}"
                self.logger.event(outcome_text, Color.YELLOW)

                # Add last words to the outcome and discussion history
                if last_words:
                    last_words_text = (
                        f'{eliminated_player.model_name}\'s last words: "{last_words}"'
                    )
                    self.current_round_data["last_words"] = last_words
                    self.logger.event(last_words_text, Color.CYAN)
                    # Add last words to discussion history
                    self.discussion_history += (
                        f"{eliminated_player.model_name} (last words): {last_words}\n\n"
                    )
                    # Add to messages
                    self.current_round_data["messages"].append(
                        {
                            "speaker": eliminated_player.model_name,
                            "content": last_words,
                            "phase": "day",
                            "role": eliminated_player.role.value,
                        }
                    )

                # Log who voted for the eliminated player
                voters = vote_details.get(eliminated_player.model_name, [])
                if voters:
                    voter_names = [
                        name.split("/")[-1] for name in voters
                    ]  # Extract model names
                    voter_text = f"Voted by: {', '.join(voter_names)}"
                    self.current_round_data["voters"] = voters
                    self.logger.event(voter_text, Color.YELLOW)
        else:
            outcome_text = "No one was eliminated by vote."
            self.current_round_data["outcome"] += f" {outcome_text}"
            self.logger.event(outcome_text, Color.YELLOW)

            # Still store vote information even if no one was eliminated
            self.current_round_data["vote_counts"] = vote_counts
            self.current_round_data["vote_details"] = vote_details

        # Set phase to night and increment round
        self.phase = "night"
        self.rounds_data.append(self.current_round_data)
        self.round_number += 1
        self.current_round_data = {
            "round_number": self.round_number,
            "messages": [],
            "actions": {},
            "eliminations": [],
            "eliminated_by_vote": [],  # Reset for the new round
            "outcome": "",
        }

        return eliminated_players

    def get_last_words(self, player, vote_count):
        """
        Get the last words from a player who is about to be eliminated.

        Args:
            player (Player): The player who is about to be eliminated.
            vote_count (int): The number of votes against the player.

        Returns:
            str: The player's last words.
        """
        self.logger.event(f"Getting last words from {player.model_name}...", Color.CYAN)

        # Generate prompt for last words
        game_state = f"{self.get_game_state()} You have been voted out with {vote_count} votes and will be eliminated. Share your final thoughts before leaving the game."
        prompt = player.generate_prompt(
            game_state,
            self.get_alive_players(),
            self.mafia_players if player.role == Role.MAFIA else None,
            self.discussion_history,
        )

        # Get response
        response = player.get_response(prompt)
        self.logger.player_response(
            player.model_name, f"{player.role.value} (Last Words)", response
        )

        return response

    def get_confirmation_vote(self, player_to_eliminate):
        """
        Get confirmation votes from all alive players on whether to eliminate a player.

        Args:
            player_to_eliminate: The player who is proposed for elimination

        Returns:
            tuple: (bool, dict) - Whether the elimination is confirmed and the vote details
        """
        alive_players = self.get_alive_players()

        # Don't include the player to be eliminated in the voting
        voting_players = [p for p in alive_players if p != player_to_eliminate]

        self.logger.event(
            f"Confirmation vote for eliminating {player_to_eliminate.model_name}",
            Color.YELLOW,
        )

        # Collect votes
        confirmation_votes = {"agree": [], "disagree": []}

        for player in voting_players:
            # Prepare game state for the player
            player_state = self.get_game_state()
            player_state["confirmation_vote_for"] = player_to_eliminate.model_name

            # Get player's vote
            vote = player.get_confirmation_vote(player_state)

            # Validate and record vote
            if vote.lower() in ["agree", "yes", "confirm", "true"]:
                confirmation_votes["agree"].append(player.model_name)
                self.logger.event(
                    f"{player.model_name} voted to CONFIRM elimination", Color.GREEN
                )
            else:
                confirmation_votes["disagree"].append(player.model_name)
                self.logger.event(
                    f"{player.model_name} voted to REJECT elimination", Color.RED
                )

        # Check if more than half of the voting players agreed
        is_confirmed = len(confirmation_votes["agree"]) > len(voting_players) / 2

        return is_confirmed, confirmation_votes

    def run_game(self):
        """
        Run the Mafia game until completion.

        Returns:
            tuple: (winner, rounds_data, participants) where winner is "Mafia" or "Villagers".
                   rounds_data includes all messages (day and night phases) for game details,
                   but players only see day phase messages during the game.
        """
        # Setup game
        if not self.setup_game():
            return None, [], {}

        # Game loop
        game_over = False
        winner = None

        while not game_over:
            # Check if game is over after night phase
            game_over, winner = self.check_game_over()
            if game_over:
                break

            # Execute day phase
            self.execute_day_phase()

            # Check if game is over
            game_over, winner = self.check_game_over()
            if game_over:
                break

            # Execute night phase
            self.execute_night_phase()

        # Add final round data if not already added
        if self.current_round_data["round_number"] > 0:
            self.rounds_data.append(self.current_round_data)

        # Create participants dictionary
        participants = {}
        for player in self.players:
            participants[player.model_name] = player.role.value

        # Log game end
        self.logger.game_end(1, winner, self.round_number)

        return winner, self.rounds_data, participants
