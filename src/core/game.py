"""Main game logic for the LLM Mafia Game."""

import random
import uuid
import re
import json
from typing import List, Tuple, Optional

import config
from models.enums import Role, GamePhase
from models.player import Player
from models.templates import PLAYER_NAMES
from utils.logger import GameLogger
from api.openrouter_client import get_llm_response


class MafiaGame:
    """Represents a Mafia game with LLM players."""

    def __init__(self, models: List[str] = None, language: str = None):
        self.game_id = str(uuid.uuid4())
        self.round_number = 0
        self.phase = GamePhase.SETUP
        self.players: List[Player] = []
        self.mafia_players: List[Player] = []
        self.doctor_player: Optional[Player] = None
        self.villager_players: List[Player] = []
        self.discussion_history = ""
        self.rounds_data = []
        self.language = language or config.LANGUAGE
        self.current_round_data = self._init_round_data()
        
        self.models = models or config.MODELS
        
        if config.RANDOM_SEED is not None:
            random.seed(config.RANDOM_SEED)
        
        self.logger = GameLogger()

    def _init_round_data(self) -> dict:
        """Initialize round data structure."""
        return {
            "round_number": 0,
            "messages": [],
            "actions": {},
            "eliminations": [],
            "eliminated_by_vote": [],
            "targeted_by_mafia": [],
            "protected_by_doctor": [],
            "outcome": "",
        }

    def setup_game(self) -> bool:
        """Set up the game by assigning roles to players."""
        if len(self.models) < config.PLAYERS_PER_GAME and config.UNIQUE_MODELS:
            self.logger.error(f"Not enough models. Need {config.PLAYERS_PER_GAME}, but only have {len(self.models)}.")
            return False

        self.logger.game_start(1, self.game_id, self.language)

        # Select models
        if config.UNIQUE_MODELS:
            selected_models = random.sample(self.models, config.PLAYERS_PER_GAME)
        else:
            selected_models = random.choices(self.models, k=config.PLAYERS_PER_GAME)

        # Create roles
        roles = ([Role.MAFIA] * config.MAFIA_COUNT + 
                [Role.DOCTOR] * config.DOCTOR_COUNT + 
                [Role.VILLAGER] * (config.PLAYERS_PER_GAME - config.MAFIA_COUNT - config.DOCTOR_COUNT))
        random.shuffle(roles)

        # Create players
        self.logger.header("PLAYER SETUP", self.logger.Color.CYAN)
        used_names = []
        
        for i, model_name in enumerate(selected_models):
            available_names = [name for name in PLAYER_NAMES if name not in used_names]
            player_name = random.choice(available_names) if available_names else f"Player_{i+1}"
            used_names.append(player_name)
            
            player = Player(model_name, player_name, roles[i], self.language)
            self.players.append(player)
            
            # Add to role-specific lists
            if player.role == Role.MAFIA:
                self.mafia_players.append(player)
            elif player.role == Role.DOCTOR:
                self.doctor_player = player
            else:
                self.villager_players.append(player)
            
            self.logger.player_setup(player.model_name, player.role.value, player.player_name)

        # Set phase to night
        self.phase = GamePhase.NIGHT
        self.round_number = 1
        self.current_round_data = self._init_round_data()
        self.current_round_data["round_number"] = self.round_number

        return True

    def get_game_state(self) -> str:
        """Get the current state of the game as a string."""
        alive_count = sum(1 for p in self.players if p.alive)
        mafia_count = sum(1 for p in self.mafia_players if p.alive)
        doctor_count = 1 if self.doctor_player and self.doctor_player.alive else 0
        villager_count = sum(1 for p in self.villager_players if p.alive)

        state = f"Round {self.round_number}, {self.phase.value.capitalize()} phase. "
        state += f"{alive_count} players alive ({mafia_count} Mafia, {villager_count + doctor_count} Villagers/Doctor). "

        if self.round_number > 1 and self.current_round_data["eliminations"]:
            eliminated = ', '.join(self.current_round_data['eliminations'])
            state += f"In the previous round, {eliminated} {'was' if len(self.current_round_data['eliminations']) == 1 else 'were'} eliminated. "

        return state

    def get_alive_players(self) -> List[Player]:
        """Get a list of alive players."""
        return [p for p in self.players if p.alive]

    def check_game_over(self) -> Tuple[bool, Optional[str]]:
        """Check if the game is over."""
        mafia_alive = sum(1 for p in self.mafia_players if p.alive)
        villagers_alive = sum(1 for p in self.villager_players if p.alive)
        doctor_alive = 1 if self.doctor_player and self.doctor_player.alive else 0

        if mafia_alive == 0:
            return True, "Villagers"
        elif mafia_alive >= (villagers_alive + doctor_alive):
            return True, "Mafia"
        elif self.round_number >= config.MAX_ROUNDS:
            return True, "Villagers" if villagers_alive + doctor_alive > mafia_alive else "Mafia"

        return False, None

    def _remove_thinking_tags(self, text: str) -> str:
        """Remove thinking tags from discussion history."""
        cleaned = re.sub(r"<[tT][hH][iI][nN][kK]>.*?</[tT][hH][iI][nN][kK]>", "", text, flags=re.DOTALL)
        cleaned = re.sub(r"<[tT][hH][iI][nN][kK]>.*$", "", cleaned, flags=re.DOTALL)
        return cleaned

    def execute_night_phase(self) -> List[Player]:
        """Execute the night phase of the game."""
        self.logger.phase_header("Night", self.round_number)
        
        # Reset protected status
        for player in self.players:
            player.protected = False

        eliminated_players = []
        
        # Mafia actions
        kill_target = self._execute_mafia_actions()
        
        # Doctor actions
        self._execute_doctor_actions()
        
        # Process eliminations
        if kill_target and not kill_target.protected:
            kill_target.alive = False
            eliminated_players.append(kill_target)
            self.current_round_data["eliminations"].append(kill_target.model_name)
            outcome = f"{kill_target.player_name} [{kill_target.model_name}] was killed by the Mafia."
            self.current_round_data["outcome"] = outcome
            self.logger.event(outcome, self.logger.Color.RED)
        elif kill_target and kill_target.protected:
            outcome = f"The Doctor protected {kill_target.player_name} [{kill_target.model_name}] from the Mafia."
            self.current_round_data["outcome"] = outcome
            self.logger.event(outcome, self.logger.Color.BLUE)
        else:
            outcome = "No one was killed during the night."
            self.current_round_data["outcome"] = outcome
            self.logger.event(outcome, self.logger.Color.YELLOW)

        self.phase = GamePhase.DAY
        return eliminated_players

    def _execute_mafia_actions(self) -> Optional[Player]:
        """Execute mafia actions and return the kill target."""
        mafia_targets = []
        
        for player in self.mafia_players:
            if not player.alive:
                continue
                
            game_state = f"{self.get_game_state()} It's night time (Round {self.round_number}). As the Mafia, you MUST choose exactly one player to kill tonight. You cannot skip this action. End your response with ACTION: Kill [player]."
            prompt = player.generate_prompt(
                game_state, 
                self.get_alive_players(), 
                self.mafia_players, 
                self._remove_thinking_tags(self.discussion_history)
            )

            response = player.get_response(prompt)
            self.logger.player_response(player.model_name, "Mafia", response, player.player_name)

            self.current_round_data["messages"].append({
                "speaker": player.model_name,
                "content": response,
                "phase": "night",
                "role": "Mafia",
                "player_name": player.player_name,
            })

            action_type, target = player.parse_night_action(response, self.get_alive_players())
            
            if action_type == "kill" and target:
                mafia_targets.append(target)
                action_text = f"Kill {target.player_name}"
                self.current_round_data["actions"][player.model_name] = action_text
                self.logger.player_action(player.model_name, "Mafia", action_text, player.player_name)
            else:
                self.logger.error(f"Invalid action from {player.model_name} (Mafia)")
                self.current_round_data["actions"][player.model_name] = "Invalid action"

        # Determine kill target by majority vote
        if mafia_targets:
            target_counts = {}
            for target in mafia_targets:
                target_counts[target.model_name] = target_counts.get(target.model_name, 0) + 1

            max_votes = max(target_counts.values())
            for target_name, votes in target_counts.items():
                if votes == max_votes:
                    kill_target = next(p for p in self.get_alive_players() if p.model_name == target_name)
                    self.current_round_data["targeted_by_mafia"].append(kill_target.model_name)
                    return kill_target

        return None

    def _execute_doctor_actions(self):
        """Execute doctor actions."""
        if not self.doctor_player or not self.doctor_player.alive:
            return

        game_state = f"{self.get_game_state()} It's night time (Round {self.round_number}). As the Doctor, you MUST choose exactly one player to protect from the Mafia tonight. You cannot skip this action. End your response with ACTION: Protect [player]."
        prompt = self.doctor_player.generate_prompt(
            game_state,
            self.get_alive_players(),
            None,
            self._remove_thinking_tags(self.discussion_history),
        )

        response = self.doctor_player.get_response(prompt)
        self.logger.player_response(self.doctor_player.model_name, "Doctor", response, self.doctor_player.player_name)

        self.current_round_data["messages"].append({
            "speaker": self.doctor_player.model_name,
            "content": response,
            "phase": "night",
            "role": "Doctor",
            "player_name": self.doctor_player.player_name,
        })

        action_type, target = self.doctor_player.parse_night_action(response, self.get_alive_players())

        if action_type == "protect" and target:
            target.protected = True
            action_text = f"Protect {target.player_name}"
            self.current_round_data["actions"][self.doctor_player.model_name] = action_text
            self.current_round_data["protected_by_doctor"].append(target.model_name)
            self.logger.player_action(self.doctor_player.model_name, "Doctor", action_text, self.doctor_player.player_name)
        else:
            self.logger.error(f"Invalid action from {self.doctor_player.model_name} (Doctor)")
            self.current_round_data["actions"][self.doctor_player.model_name] = "Invalid action"

    def execute_day_phase(self) -> List[Player]:
        """Execute the day phase of the game."""
        self.logger.phase_header("Day", self.round_number)
        
        alive_players = self.get_alive_players()
        
        # Discussion round
        self.logger.event("Discussion Round - Players share their thoughts", self.logger.Color.CYAN)
        self._conduct_discussion(alive_players)
        
        # Voting round
        self.logger.event("Voting Round - Players make their final arguments and vote", self.logger.Color.CYAN)
        eliminated_players = self._conduct_voting(alive_players)
        
        # Prepare for next round
        self.phase = GamePhase.NIGHT
        self.rounds_data.append(self.current_round_data)
        self.round_number += 1
        self.current_round_data = self._init_round_data()
        self.current_round_data["round_number"] = self.round_number
        
        return eliminated_players

    def _conduct_discussion(self, alive_players: List[Player]):
        """Conduct the discussion phase."""
        for player in alive_players:
            instruction = f"It's day time (Round {self.round_number}). Discuss with other players about who might be Mafia. This is the DISCUSSION PHASE ONLY - DO NOT VOTE YET. You will vote in the next round."
            game_state = f"{self.get_game_state()} {instruction}"
            
            prompt = player.generate_prompt(
                game_state, 
                alive_players, 
                self.mafia_players if player.role == Role.MAFIA else None, 
                self._remove_thinking_tags(self.discussion_history)
            )
            
            response = player.get_response(prompt)
            self.logger.player_response(player.model_name, player.role.value, response, player.player_name)
            
            self.current_round_data["messages"].append({
                "speaker": player.model_name,
                "content": response,
                "phase": "day_discussion",
                "role": player.role.value,
                "player_name": player.player_name,
            })
            
            self.discussion_history += f"{player.player_name}: {response}\n\n"

    def _conduct_voting(self, alive_players: List[Player]) -> List[Player]:
        """Conduct the voting phase."""
        votes = {}
        
        for player in alive_players:
            instruction = f"It's now the VOTING PHASE (Round {self.round_number}). Make your final arguments and YOU MUST VOTE to eliminate a suspected Mafia member. End your message with VOTE: [player name]."
            game_state = f"{self.get_game_state()} {instruction}"
            
            prompt = player.generate_prompt(
                game_state,
                alive_players,
                self.mafia_players if player.role == Role.MAFIA else None,
                self._remove_thinking_tags(self.discussion_history),
            )
            
            response = player.get_response(prompt)
            self.logger.player_response(player.model_name, player.role.value, response, player.player_name)
            
            self.current_round_data["messages"].append({
                "speaker": player.model_name,
                "content": response,
                "phase": "day_voting",
                "role": player.role.value,
                "player_name": player.player_name,
            })
            
            # Parse vote
            vote_target = player.parse_day_vote(response, alive_players)
            if vote_target:
                votes[player.model_name] = vote_target.model_name
                action_text = f"Vote {vote_target.player_name}"
                self.current_round_data["actions"][player.model_name] = action_text
                self.logger.player_action(player.model_name, player.role.value, action_text, player.player_name)
            else:
                self.logger.warning(f"{player.model_name} failed to cast a valid vote")
                self.current_round_data["actions"][player.model_name] = "Invalid vote"
            
            self.discussion_history += f"{player.player_name}: {response}\n\n"

        # Count votes and eliminate player
        return self._process_elimination(votes, alive_players)

    def _process_elimination(self, votes: dict, alive_players: List[Player]) -> List[Player]:
        """Process the elimination based on votes."""
        vote_counts = {}
        vote_details = {}
        
        for voter, target_name in votes.items():
            vote_counts[target_name] = vote_counts.get(target_name, 0) + 1
            if target_name not in vote_details:
                vote_details[target_name] = []
            vote_details[target_name].append(voter)

        # Find player with most votes
        eliminated_player = None
        if vote_counts:
            max_votes = max(vote_counts.values())
            for target_name, vote_count in vote_counts.items():
                if vote_count == max_votes:
                    eliminated_player = next(p for p in alive_players if p.model_name == target_name)
                    break

        eliminated_players = []
        if eliminated_player:
            # Get confirmation vote
            is_confirmed, confirmation_votes = self._get_confirmation_vote(eliminated_player)
            self.current_round_data["confirmation_votes"] = confirmation_votes
            
            if is_confirmed:
                # Get last words
                last_words = self._get_last_words(eliminated_player, vote_counts[eliminated_player.model_name])
                
                eliminated_player.alive = False
                eliminated_players.append(eliminated_player)
                self.current_round_data["eliminations"].append(eliminated_player.model_name)
                self.current_round_data["eliminated_by_vote"] = [eliminated_player.model_name]
                
                outcome = f"{eliminated_player.player_name} [{eliminated_player.model_name}] was eliminated by vote with {vote_counts[eliminated_player.model_name]} votes."
                self.current_round_data["outcome"] += f" {outcome}"
                self.logger.event(outcome, self.logger.Color.YELLOW)
                
                if last_words:
                    self.current_round_data["last_words"] = last_words
                    last_words_text = f'{eliminated_player.player_name} [{eliminated_player.model_name}]\'s last words: "{last_words}"'
                    self.logger.event(last_words_text, self.logger.Color.CYAN)
                    self.discussion_history += f"{eliminated_player.player_name}: {last_words}\n\n"
            else:
                outcome = f"The elimination of {eliminated_player.model_name} was rejected by the town."
                self.current_round_data["outcome"] += f" {outcome}"
                self.logger.event(outcome, self.logger.Color.YELLOW)

        self.current_round_data["vote_counts"] = vote_counts
        self.current_round_data["vote_details"] = vote_details
        
        return eliminated_players

    def _get_confirmation_vote(self, player_to_eliminate: Player) -> Tuple[bool, dict]:
        """Get confirmation votes from all alive players."""
        alive_players = self.get_alive_players()
        voting_players = [p for p in alive_players if p != player_to_eliminate]
        
        self.logger.event(f"Confirmation vote for eliminating {player_to_eliminate.player_name} [{player_to_eliminate.model_name}]", self.logger.Color.YELLOW)
        
        confirmation_votes = {"agree": [], "disagree": []}
        
        for player in voting_players:
            game_state = {
                "game_state": self.get_game_state(),
                "confirmation_vote_for": player_to_eliminate.player_name,
                "confirmation_vote_for_model": player_to_eliminate.model_name,
            }
            
            vote = player.get_confirmation_vote(game_state)
            
            if vote == "agree":
                confirmation_votes["agree"].append(player.model_name)
                self.logger.event(f"{player.player_name} [{player.model_name}] voted to CONFIRM elimination", self.logger.Color.GREEN)
            else:
                confirmation_votes["disagree"].append(player.model_name)
                self.logger.event(f"{player.player_name} [{player.model_name}] voted to REJECT elimination", self.logger.Color.RED)

        is_confirmed = len(confirmation_votes["agree"]) > len(voting_players) / 2
        return is_confirmed, confirmation_votes

    def _get_last_words(self, player: Player, vote_count: int) -> str:
        """Get the last words from a player who is about to be eliminated."""
        self.logger.event(f"Getting last words from {player.player_name} [{player.model_name}]...", self.logger.Color.CYAN)
        
        game_state = f"{self.get_game_state()} You have been voted out with {vote_count} votes and will be eliminated. Share your final thoughts before leaving the game."
        prompt = player.generate_prompt(
            game_state,
            self.get_alive_players(),
            self.mafia_players if player.role == Role.MAFIA else None,
            self._remove_thinking_tags(self.discussion_history),
        )
        
        response = player.get_response(prompt)
        self.logger.player_response(player.model_name, f"{player.role.value} (Last Words)", response, player.player_name)
        
        return response

    def run_game(self) -> Tuple[Optional[str], list, dict, str, dict]:
        """Run the Mafia game until completion."""
        if not self.setup_game():
            return None, [], {}, self.language, {}

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
            participants[player.player_name] = {
                "role": player.role.value,
                "model_name": player.model_name,
                "player_name": player.player_name,
            }

        # Generate game critic review
        critic_review = self._generate_critic_review(winner)

        # Log game end
        self.logger.game_end(1, winner, self.round_number)

        return winner, self.rounds_data, participants, self.language, critic_review

    def _generate_critic_review(self, winner: str) -> dict:
        """Generate a game critic review using Claude."""
        game_summary = {
            "winner": winner,
            "rounds": self.round_number,
            "participants": {player.model_name: player.role.value for player in self.players},
            "eliminations": []
        }

        # Collect eliminations by round
        for round_data in self.rounds_data:
            if "eliminations" in round_data and round_data["eliminations"]:
                for player in round_data["eliminations"]:
                    game_summary["eliminations"].append({
                        "player": player,
                        "round": round_data["round_number"],
                        "phase": round_data.get("phase", "unknown"),
                    })

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
Format your response as a JSON object with 'title', 'content', and 'one_liner' fields."""

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
                    if "one_liner" not in review_json:
                        review_json["one_liner"] = "A game that defies simple description!"
                    return review_json
                except json.JSONDecodeError:
                    return {
                        "title": "AI Mafia Game Review",
                        "content": response_content[:300],
                        "one_liner": "A game that left our critic speechless!",
                    }
            else:
                return {
                    "title": "AI Mafia Game Review",
                    "content": response_content[:300],
                    "one_liner": "A game that defies conventional criticism!",
                }

        except Exception as e:
            print(f"Error generating critic review: {e}")
            return {
                "title": "Game Review Unavailable",
                "content": "The critic was unable to review this game due to technical difficulties.",
                "one_liner": "Technical issues prevented our critic from delivering judgment.",
            }