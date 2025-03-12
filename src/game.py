"""
Game logic for the LLM Mafia Game Competition.
"""

import random
import uuid
from player import Player
from game_templates import Role
import config
from logger import GameLogger, Color
import re
import json
from openrouter import get_llm_response


class MafiaGame:
    """Represents a Mafia game with LLM players."""

    def __init__(self, models=None, language=None):
        """
        Initialize a Mafia game.

        Args:
            models (list, optional): List of model names to use as players.
            language (str, optional): Language for game prompts and interactions. Defaults to config.LANGUAGE.
        """
        self.game_id = str(uuid.uuid4())
        self.round_number = 0
        self.phase = "setup"  # setup, night, day
        self.players: list[Player] = []
        self.mafia_players: list[Player] = []
        self.doctor_player: Player | None = None
        self.villager_players: list[Player] = []
        self.discussion_history = ""
        self.rounds_data = []
        self.language = language if language is not None else config.LANGUAGE
        self.current_round_data = {
            "round_number": 0,
            "messages": [],
            "actions": {},
            "eliminations": [],
            "eliminated_by_vote": [],  # Reset for the new round
            "targeted_by_mafia": [],  # Reset for the new round
            "protected_by_doctor": [],  # Reset for the new round
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
        self.logger.game_start(1, self.game_id, self.language)

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
            # Generate a player name if not using model name
            # For now, we'll use the model name as the player name
            # This can be enhanced to use more creative names
            player_name = model_name.split("/")[
                -1
            ]  # Use the last part of the model name

            # Create player with both model_name and player_name
            player = Player(model_name, player_name, roles[i], language=self.language)
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
            "targeted_by_mafia": [],  # Reset for the new round
            "protected_by_doctor": [],  # Reset for the new round
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

    def discussion_history_without_thinkings(self):
        """
        Get the discussion history for the current round, excluding thinking messages.
        Removes any <think></think> or <THINK></THINK> tags and their contents.
        If a closing tag is missing, removes everything from the opening tag to the end of the string.
        """
        # First handle properly closed tags (both lowercase and uppercase)
        discussion_history_without_thinkings = re.sub(
            r"<[tT][hH][iI][nN][kK]>.*?</[tT][hH][iI][nN][kK]>",
            "",
            self.discussion_history,
            flags=re.DOTALL,
        )

        # Then handle any unclosed tags - remove from opening tag to the end of the string
        discussion_history_without_thinkings = re.sub(
            r"<[tT][hH][iI][nN][kK]>.*$",
            "",
            discussion_history_without_thinkings,
            flags=re.DOTALL,
        )

        return discussion_history_without_thinkings

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
                game_state = f"{self.get_game_state()} It's night time (Round {self.round_number}). As the Mafia, you MUST choose exactly one player to kill tonight. You cannot skip this action. End your response with ACTION: Kill [player]."
                prompt = player.generate_prompt(
                    game_state,
                    self.get_alive_players(),
                    self.mafia_players,
                    self.discussion_history_without_thinkings(),
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

            # Record the final mafia target
            if kill_target:
                self.current_round_data["targeted_by_mafia"].append(
                    kill_target.model_name
                )

        # Get action from Doctor
        protected_player = None
        if self.doctor_player and self.doctor_player.alive:
            # Generate prompt with language-specific instructions
            night_instructions = {
                "English": f"It's night time (Round {self.round_number}). As the Doctor, you MUST choose exactly one player to protect from the Mafia tonight. You cannot skip this action. End your response with ACTION: Protect [player].",
                "Spanish": f"Es hora de noche (Ronda {self.round_number}). Como Doctor, DEBES elegir exactamente a un jugador para proteger de la Mafia esta noche. No puedes omitir esta acción. Termina tu respuesta con ACCIÓN: Proteger [jugador].",
                "French": f"C'est la nuit (Tour {self.round_number}). En tant que Docteur, vous DEVEZ choisir exactement un joueur à protéger de la Mafia ce soir. Vous ne pouvez pas ignorer cette action. Terminez votre réponse par ACTION: Protéger [joueur].",
                "Korean": f"밤 시간입니다 (라운드 {self.round_number}). 의사로서, 당신은 오늘 밤 마피아로부터 보호할 플레이어를 정확히 한 명 선택해야 합니다. 이 행동을 건너뛸 수 없습니다. 응답 끝에 행동: 보호하기 [플레이어]를 포함하세요.",
            }

            # Get the appropriate instruction based on the doctor's language
            instruction = night_instructions.get(
                self.doctor_player.language, night_instructions["English"]
            )

            game_state = f"{self.get_game_state()} {instruction}"
            prompt = self.doctor_player.generate_prompt(
                game_state,
                self.get_alive_players(),
                None,
                self.discussion_history_without_thinkings(),
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
                self.current_round_data["protected_by_doctor"].append(target.model_name)
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
            # We already added to targeted_by_mafia above
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

        # First round: Discussion without voting
        self.logger.event("Discussion Round - Players share their thoughts", Color.CYAN)
        self._conduct_player_interactions(
            alive_players,
            "day_discussion",
            f"It's day time (Round {self.round_number}). Discuss with other players about who might be Mafia. This is the DISCUSSION PHASE ONLY - DO NOT VOTE YET. You will vote in the next round.",
            messages,
            collect_votes=False,
        )

        # Second round: Discussion with voting
        self.logger.event(
            "Voting Round - Players make their final arguments and vote", Color.CYAN
        )
        self._conduct_player_interactions(
            alive_players,
            "day_voting",
            f"It's now the VOTING PHASE (Round {self.round_number}). Make your final arguments and YOU MUST VOTE to eliminate a suspected Mafia member. End your message with VOTE: [player name].",
            messages,
            collect_votes=True,
            votes=votes,
        )

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
                            "type": "last_words",
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
            "targeted_by_mafia": [],  # Reset for the new round
            "protected_by_doctor": [],  # Reset for the new round
            "outcome": "",
        }

        return eliminated_players

    def _conduct_player_interactions(
        self,
        alive_players,
        phase_type,
        instruction,
        messages,
        collect_votes=False,
        votes=None,
    ):
        """
        Conduct interactions with all alive players during the day phase.

        Args:
            alive_players (list): List of alive players
            phase_type (str): Type of phase (day_discussion or day_voting)
            instruction (str): Specific instruction for this interaction round
            messages (list): List to collect all messages
            collect_votes (bool): Whether to collect votes in this round
            votes (dict): Dictionary to store votes if collect_votes is True
        """
        for player in alive_players:
            # Generate prompt
            game_state = f"{self.get_game_state()} {instruction}"

            # Add special instruction for doctor during day phase
            if player.role == Role.DOCTOR:
                day_warnings = {
                    "English": " IMPORTANT: This is the DAY phase. Do NOT use your protection ability now. Only use ACTION: Protect during night phase.",
                    "Spanish": " IMPORTANTE: Esta es la fase DIURNA. NO uses tu habilidad de protección ahora. Solo usa ACCIÓN: Proteger durante la fase nocturna.",
                    "French": " IMPORTANT: C'est la phase de JOUR. N'utilisez PAS votre capacité de protection maintenant. Utilisez ACTION: Protéger uniquement pendant la phase de nuit.",
                    "Korean": " 중요: 지금은 낮 단계입니다. 지금은 보호 능력을 사용하지 마세요. 행동: 보호하기는 밤 단계에서만 사용하세요.",
                }

                # Get the appropriate warning based on the doctor's language
                warning = day_warnings.get(player.language, day_warnings["English"])
                game_state += warning

            # Add special instruction for mafia players during day phase
            elif player.role == Role.MAFIA:
                day_warnings = {
                    "English": " IMPORTANT: This is the DAY phase. Do NOT use 'ACTION: Kill' now. Instead, use 'VOTE: [player]' to vote like other villagers.",
                    "Spanish": " IMPORTANTE: Esta es la fase DIURNA. NO uses 'ACCIÓN: Matar' ahora. En su lugar, usa 'VOTO: [jugador]' para votar como los demás aldeanos.",
                    "French": " IMPORTANT: C'est la phase de JOUR. N'utilisez PAS 'ACTION: Tuer' maintenant. À la place, utilisez 'VOTE: [joueur]' pour voter comme les autres villageois.",
                    "Korean": " 중요: 지금은 낮 단계입니다. '행동: 죽이기'를 사용하지 마세요. 대신 다른 마을 사람들처럼 '투표: [플레이어]'를 사용하여 투표하세요.",
                }

                # Get the appropriate warning based on the mafia player's language
                warning = day_warnings.get(player.language, day_warnings["English"])
                game_state += warning

            # Add voting reminder for all players during voting phase
            if phase_type == "day_voting":
                voting_reminders = {
                    "English": " REMINDER: This is the VOTING PHASE. You MUST end your message with 'VOTE: [player]' to cast your vote.",
                    "Spanish": " RECORDATORIO: Esta es la fase de VOTACIÓN. DEBES terminar tu mensaje con 'VOTO: [jugador]' para emitir tu voto.",
                    "French": " RAPPEL: C'est la phase de VOTE. Vous DEVEZ terminer votre message par 'VOTE: [joueur]' pour exprimer votre vote.",
                    "Korean": " 알림: 지금은 투표 단계입니다. 반드시 메시지 끝에 '투표: [플레이어]'를 포함하여 투표해야 합니다.",
                }

                # Get the appropriate reminder based on the player's language
                reminder = voting_reminders.get(
                    player.language, voting_reminders["English"]
                )
                game_state += reminder

            prompt = player.generate_prompt(
                game_state,
                alive_players,
                self.mafia_players if player.role == Role.MAFIA else None,
                self.discussion_history_without_thinkings(),
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
                    "phase": phase_type,
                    "role": player.role.value,
                }
            )

            # Parse vote if in voting round
            if collect_votes and votes is not None:
                vote_target = player.parse_day_vote(response, alive_players)
                if vote_target:
                    votes[player.model_name] = vote_target.model_name
                    action_text = f"Vote {vote_target.model_name}"
                    self.current_round_data["actions"][player.model_name] = action_text
                    self.logger.player_action(
                        player.model_name, player.role.value, action_text
                    )
                else:
                    self.logger.warning(
                        f"{player.model_name} failed to cast a valid vote during voting phase"
                    )
                    self.current_round_data["actions"][
                        player.model_name
                    ] = "Invalid vote"

            # Update discussion history
            self.discussion_history += f"{player.model_name}: {response}\n\n"

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
            self.discussion_history_without_thinkings(),
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
            game_state_str = self.get_game_state()
            # Create a dictionary with the game state and the player to eliminate
            player_state = {
                "game_state": game_state_str,
                "confirmation_vote_for": player_to_eliminate.model_name,
            }

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
            tuple: (winner, rounds_data, participants, language) where winner is "Mafia" or "Villagers".
                   rounds_data includes all messages (day and night phases) for game details,
                   but players only see day phase messages during the game.
                   language is the language used for the game.
        """
        # Setup game
        if not self.setup_game():
            return None, [], {}, self.language

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

        # Create participants dictionary with both model_name and player_name
        participants = {}
        for player in self.players:
            participants[player.model_name] = {
                "role": player.role.value,
                "player_name": player.player_name,
            }

        # Generate game critic review
        critic_review = self.generate_critic_review(winner)

        # Log game end
        self.logger.game_end(1, winner, self.round_number)

        return winner, self.rounds_data, participants, self.language, critic_review

    def generate_critic_review(self, winner):
        """
        Generate a game critic review using Claude via OpenRouter.

        Args:
            winner (str): The winning team ("Mafia" or "Villagers").

        Returns:
            dict: A dictionary containing the critic review with title, content, and one-sentence summary.
        """
        # Get the game summary information
        game_summary = {
            "winner": winner,
            "rounds": self.round_number,
            "participants": {
                player.model_name: player.role.value for player in self.players
            },
            "eliminations": [],
        }

        # Collect eliminations by round
        for round_data in self.rounds_data:
            if "eliminations" in round_data and round_data["eliminations"]:
                for player in round_data["eliminations"]:
                    game_summary["eliminations"].append(
                        {
                            "player": player,
                            "round": round_data["round_number"],
                            "phase": round_data.get("phase", "unknown"),
                        }
                    )

        # Create a prompt for Claude to generate a critic review
        prompt = f"""You are a professional game critic reviewing a Mafia game played by AI language models. 
        
Game summary:
- Winner: {winner}
- Number of rounds: {self.round_number}
- Players and roles: {game_summary['participants']}
- Eliminations: {game_summary['eliminations']}

Write a short, entertaining critic review of this game. Include:
1. A catchy title for your review (max 50 characters)
2. A concise review (max 200 words) that analyzes:
   - The game's pacing and length
   - Interesting strategic moves or blunders
   - The performance of the winning team
   - Any particularly noteworthy moments
3. A one-sentence intense summary that captures the essence of the game in a dramatic way (max 100 characters)

Your tone should be professional but entertaining, like a game critic. Be specific about this particular game.
Format your response as a JSON object with 'title', 'content', and 'one_liner' fields.
"""

        try:
            model_name = config.CLAUDE_3_7_SONNET
            response_content = get_llm_response(model_name, prompt)

            if response_content == "ERROR: Could not get response":
                return {
                    "title": "Game Review Unavailable",
                    "content": "The critic was unable to review this game due to API issues.",
                    "one_liner": "Technical difficulties prevented our critic from witnessing this showdown.",
                }

            # Look for JSON in the response
            json_match = re.search(r"({.*})", response_content, re.DOTALL)

            if json_match:
                try:
                    review_json = json.loads(json_match.group(1))
                    # Ensure one_liner exists
                    if "one_liner" not in review_json:
                        review_json["one_liner"] = (
                            "A game that defies simple description!"
                        )
                    return review_json
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    return {
                        "title": "AI Mafia Game Review",
                        "content": response_content[
                            :300
                        ],  # Truncate to reasonable length
                        "one_liner": "A game that left our critic speechless!",
                    }
            else:
                # If no JSON found, create a simple structure
                return {
                    "title": "AI Mafia Game Review",
                    "content": response_content[:300],  # Truncate to reasonable length
                    "one_liner": "A game that defies conventional criticism!",
                }

        except Exception as e:
            print(f"Error generating critic review: {e}")
            return {
                "title": "Game Review Unavailable",
                "content": "The critic was unable to review this game due to technical difficulties.",
                "one_liner": "Technical issues prevented our critic from delivering judgment.",
            }
