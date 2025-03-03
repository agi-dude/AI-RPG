import os
import sys
import json
import time
import random
import re
from typing import Dict, List, Any, Optional, Tuple

# Use the ollama library instead of requests
import ollama


class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREY = "\033[90m"


class AITextRPG:
    def __init__(self, ollama_host: str = "http://localhost:11434"):
        """Initialize the AI Text RPG game."""
        # Create an Ollama client with custom host if needed
        self.client = ollama.Client(host=ollama_host)
        self.model = "fluffy/magnum-v4-22b:latest"  # Default model, can be changed
        self.world_data = {
            "name": "",
            "description": "",
            "theme": "",
            "plots": [],
            "characters": [],
            "locations": [],
            "enemies": [],
            "items": []
        }
        self.knowledge_base = []  # History of important events
        self.player = {
            "name": "",
            "health": 100,
            "max_health": 100,
            "attack": 10,
            "defense": 5,
            "inventory": [],
            "skills": []
        }
        self.current_location = ""
        self.turn_count = 0
        self.in_combat = False
        self.current_enemy = None
        
    def generate_ai_response(self, prompt: str, system_prompt: str = "") -> str:
        """Generate a response from the Ollama model using the ollama library."""
        try:
            # Use the generate method from the ollama library
            response = self.client.generate(
                model=self.model,
                prompt=f"<s>[INST] {system_prompt}. Lastly, please don't use cliches and AI-slop, try to stay original.\n\n{prompt}[/INST] "
            )
            return re.sub(r'<think>[\s\S]*?<\/think>\s*', '', response.get("response", ""))
        except ollama.ResponseError as e:
            print(f"Error: {e.error}")
            print(f"Status code: {e.status_code}")
            return f"Error communicating with AI model: {e.error}"
        except Exception as e:
            print(f"Error: {str(e)}")
            return "Error communicating with AI model. Please ensure Ollama is running."

    def setup_game(self):
        """Initial game setup and world creation."""
        self.clear_screen()
        print(Colors.WHITE + "=" * 80)
        print(Colors.WHITE + " " * 30 + "AI TEXT RPG")
        print(Colors.WHITE + "=" * 80)
        print(Colors.WHITE + "\nWelcome to the AI-powered text RPG!")
        print(Colors.WHITE + "This game uses Ollama to create a unique world based on your ideas.")
        print(Colors.WHITE + "\nBefore we begin, ensure Ollama is installed and running on your system.")
        print(Colors.WHITE + "Default URL: http://localhost:11434")
        
        # Check Ollama connection
        if not self.check_ollama_connection():
            custom_url = input("\nCould not connect to Ollama at default URL. Enter custom URL or press Enter to retry: ")
            if custom_url:
                # Recreate client with new host
                self.client = ollama.Client(host=custom_url)
            if not self.check_ollama_connection():
                print(Colors.RED + "Could not connect to Ollama. Please ensure it's running and try again.")
                sys.exit(1)
                
        # Set model
        available_models = self.get_available_models()
        if available_models:
            print("\nAvailable models:")
            for i, model in enumerate(available_models, 1):
                print(f"{i}. {model}")
            
            model_choice = input("\nSelect a model number: ")
            if model_choice.isdigit() and 1 <= int(model_choice) <= len(available_models):
                self.model = available_models[int(model_choice) - 1]
            else:
                print("Using default model: deepseek-r1:14b")
        
        # Get player name
        self.player["name"] = input("\nEnter your character's name [Adventurer]: ")
        if not self.player["name"]:
            self.player["name"] = "Adventurer"
            
        # Get world concept from the player
        print("\nDescribe the world you want to explore (be as detailed or vague as you like):")
        world_concept = input(Colors.GREEN + "> ")
        
        print("\nCreating your world... This might take a moment.")
        self.create_world(world_concept)
        
        print("\nGenerating game elements...")
        self.generate_game_elements()
        
        # Ready to start
        input("\nPress Enter to begin your adventure...")
        self.start_game()

    def check_ollama_connection(self) -> bool:
        """Check if Ollama is available using the ollama library."""
        try:
            # Use the list method to check connection
            self.client.list()
            return True
        except:
            return False
            
    def get_available_models(self) -> List[str]:
        """Get list of available models from Ollama using the ollama library."""
        # Use the list method from the ollama library
        models_info = self.client.list()
        return [model["model"] for model in models_info.get("models", [])]

    def create_world(self, concept: str):
        """Generate a world based on the player's concept."""
        system_prompt = """
        You are a creative world-building AI for an RPG game. Create a detailed and cohesive world based on 
        the player's concept. Include the following: world name, theme, brief description, and unique elements.
        Format as JSON with the fields: name, description, theme.
        Keep your response focused only on the JSON output.
        """
        
        prompt = f"Create a world based on this concept: {concept}"
        response = self.generate_ai_response(prompt, system_prompt)
        
        try:
            # Extract JSON from response (in case there's additional text)
            json_str = response.strip()
            if not json_str.startswith('{'):
                # Find the first occurrence of '{'
                start = json_str.find('{')
                if start != -1:
                    json_str = json_str[start:]
                    # Find the matching closing brace
                    depth = 0
                    for i, char in enumerate(json_str):
                        if char == '{':
                            depth += 1
                        elif char == '}':
                            depth -= 1
                            if depth == 0:
                                json_str = json_str[:i+1]
                                break
                else:
                    raise ValueError("No JSON found in response")
            
            world_data = json.loads(json_str)
            self.world_data["name"] = world_data.get("name", "Unknown Realm")
            self.world_data["description"] = world_data.get("description", "A mysterious world.")
            self.world_data["theme"] = world_data.get("theme", "Fantasy")
            
            # Display the world information
            self.clear_screen()
            print("=" * 80)
            print(f" {self.world_data['name'].upper()}")
            print("=" * 80)
            print(f"\nTheme: {self.world_data['theme']}")
            print(f"\n{self.world_data['description']}")
            
        except Exception as e:
            print(f"Error parsing world data: {str(e)}")
            print("Creating a default world instead.")
            self.world_data["name"] = "Mystical Realm"
            self.world_data["description"] = "A world of magic and mystery awaits you."
            self.world_data["theme"] = "Fantasy"
    
    def generate_game_elements(self):
        """Generate game elements like plots, characters, locations, enemies, etc."""
        elements = ["plots", "characters", "locations", "enemies", "items"]
        
        for element in elements:
            print(f"Generating {element}...")
            
            system_prompt = f"""
            You are a creative RPG content creator. Based on the world description, generate a list of 
            {element} that would fit well in this world. Format as a JSON array of objects.
            
            For plots: Include "title" and "description" fields.
            For characters: Include "name", "role", and "description" fields.
            For locations: Include "name", "type", and "description" fields.
            For enemies: Include "name", "difficulty" (1-10), "health", "attack", "defense", and "description" fields.
            For items: Include "name", "type", "effect", and "description" fields. Items should be one of [consumable, weapon,  armor]. If the item is health consumable then it's effect should contain "Heal [AMOUNT TO HEAL]". If it is a weapon and has an attack boost, it's description should contain "Boost [EXTRA DAMAGE]". If it is a armor and has an defense boost, it's description should contain "Boost [EXTRA DEFENSE]". But effects are not limited to these,  you can and should also add items with custom effects.
            
            Generate 15-35 entries. Keep your response focused only on the JSON output.
            """
            
            prompt = f"""
            World name: {self.world_data['name']}
            Theme: {self.world_data['theme']}
            Description: {self.world_data['description']}
            
            Generate {element} for this world.
            """
            
            response = self.generate_ai_response(prompt, system_prompt)
            
            try:
                # Extract JSON from response
                json_str = response.strip()
                if not json_str.startswith('['):
                    start = json_str.find('[')
                    end = json_str.rfind(']')
                    if start != -1 and end != -1:
                        json_str = json_str[start:end+1]
                    else:
                        raise ValueError(f"No JSON array found in {element} response")
                
                element_data = json.loads(json_str)
                self.world_data[element] = element_data
                
                # Print a few examples
                print(f"Generated {len(element_data)} {element}:")
                for i, item in enumerate(element_data[:3], 1):
                    if element == "plots":
                        print(f"{i}. {item.get('title', 'Unnamed')}")
                    else:
                        print(f"{i}. {item.get('name', 'Unnamed')}")
                if len(element_data) > 3:
                    print(f"...and {len(element_data) - 3} more.")
                
            except Exception as e:
                print(f"Error parsing {element} data: {str(e)}")
                self.world_data[element] = []
        
        # Set initial location
        if self.world_data["locations"]:
            self.current_location = self.world_data["locations"][0]["name"]
        else:
            # Create a default location if none were generated
            default_location = {
                "name": "Starting Village",
                "type": "settlement",
                "description": "A small village on the edge of the wilderness."
            }
            self.world_data["locations"].append(default_location)
            self.current_location = default_location["name"]

    def start_game(self):
        """Start the main game loop."""
        # Introduce the player to the game
        self.clear_screen()
        intro_text = self.generate_ai_response(
            f"Create an introductory text for a player named {self.player['name']} " +
            f"who is starting their journey in {self.world_data['name']}. " +
            f"They are currently in {self.current_location}. " +
            f"Make it atmospheric and engaging, about 3-4 paragraphs." +
            f"Describe the world background, a little of who the character is, and why they are where they are, and what they need to do." +
            f"You are a narrative AI for an RPG game. Create immersive, descriptive text."
        )
        
        print(Colors.BLUE + intro_text)
        print("\n" + "=" * 80 + "\n")
        
        # Start the game loop
        self.game_loop()
    
    def game_loop(self):
        """Main game loop."""
        while True:
            if self.in_combat:
                self.combat_turn()
            else:
                self.exploration_turn()
    
    def exploration_turn(self):
        """Handle a turn during exploration mode."""
        # Display prompt for player action
        action = input(Colors.CYAN + "\nWhat would you like to do? > ")
        
        # Check for quit command
        if action.lower() in ['quit', 'exit', 'q']:
            self.quit_game()
        
        # Check for help command
        if action.lower() in ['help', 'h', '?']:
            self.show_help()
            return
            
        # Check for status command
        if action.lower() in ['status', 'stats', 'stat']:
            self.show_status()
            return
            
        # Check for inventory command
        if action.lower() in ['inventory', 'inv', 'i']:
            self.show_inventory()
            return
        
        # Check for knowledge base command
        if action.lower() in ['history', 'events', 'kb']:
            self.show_knowledge_base()
            return
            
        # Process the player's action
        self.process_player_action(action)
    
    def process_player_action(self, action: str):
        """Process the player's action and generate a response."""
        # Increment turn counter
        self.turn_count += 1
        
        # Construct context for the AI
        context = {
            "player_name": self.player["name"],
            "current_location": self.current_location,
            "turn_count": self.turn_count,
            "player_health": f"{self.player['health']}/{self.player['max_health']}",
            "player_inventory": [item["name"] for item in self.player["inventory"]],
            "recent_events": self.knowledge_base[-3:] if self.knowledge_base else []
        }
        
        # Generate system prompt
        system_prompt = """
        You are the AI game master for a text RPG. Respond to the player's action with a
        vivid description of what happens. Keep your response under 2 paragraphs.
        
        If the action leads to:
        1. Combat - indicate this with [COMBAT] at the end of your response, followed by enemy name
        2. Finding an item - indicate this with [ITEM] at the end, followed by item name
        3. Changing location - indicate this with [LOCATION] at the end, followed by new location name
        4. A significant event that should be recorded - indicate with [EVENT] and a brief description
        
        Otherwise, respond naturally without special tags. Do not write any things on behalf of the player, and or their actions.
        """
        
        # Generate prompt for the AI
        locations_str = "\n".join([f"- {loc['name']}: {loc['description']}" for loc in self.world_data["locations"][:5]])
        characters_str = "\n".join([f"- {char['name']} ({char['role']}): {char['description']}" for char in self.world_data["characters"][:5]])
        
        prompt = f"""
        === WORLD INFORMATION ===
        World: {self.world_data['name']} ({self.world_data['theme']})
        Current Location: {self.current_location}
        
        Some key locations:
        {locations_str}
        
        Some key characters:
        {characters_str}
        
        === PLAYER INFORMATION ===
        Name: {self.player['name']}
        Health: {self.player['health']}/{self.player['max_health']}
        Inventory: {', '.join([item["name"] for item in self.player["inventory"]]) if self.player["inventory"] else "Empty"}
        
        === RECENT HISTORY ===
        {chr(10).join(self.knowledge_base[-3:]) if self.knowledge_base else "No significant events yet."}
        
        === CURRENT SITUATION ===
        Turn: {self.turn_count}
        The player is currently at: {self.current_location}
        
        Player's action: "{action}"
        
        Respond to this action with a vivid description of what happens. Consider the worldbuilding, current 
        location, and any relevant characters or items. Be immersive but concise. Refer to the player in second person.
        """
        
        # Get AI response
        response = self.generate_ai_response(prompt, system_prompt)
        
        # Process special tags in the response
        self.process_response_tags(response)
        
        # Display the response to the player (without the tags)
        response_without_tags = self.remove_tags(response)
        print(Colors.GREEN + "\n" + response_without_tags)
    
    def process_response_tags(self, response: str):
        """Process special tags in the AI's response."""
        # Check for combat
        if "[COMBAT]" in response:
            parts = response.split("[COMBAT]")
            if len(parts) > 1:
                enemy_name = parts[1].strip().split("\n")[0].strip()
                self.start_combat(enemy_name)
        
        # Check for item discovery
        if "[ITEM]" in response:
            parts = response.split("[ITEM]")
            if len(parts) > 1:
                item_name = parts[1].strip().split("\n")[0].strip()
                self.find_item(item_name)
        
        # Check for location change
        if "[LOCATION]" in response:
            parts = response.split("[LOCATION]")
            if len(parts) > 1:
                location_name = parts[1].strip().split("\n")[0].strip()
                self.change_location(location_name)
        
        # Check for event
        if "[EVENT]" in response:
            parts = response.split("[EVENT]")
            if len(parts) > 1:
                event_description = parts[1].strip().split("\n")[0].strip()
                self.add_to_knowledge_base(event_description)
    
    def remove_tags(self, text: str) -> str:
        """Remove special tags from a response."""
        for tag in ["[COMBAT]", "[ITEM]", "[LOCATION]", "[EVENT]"]:
            if tag in text:
                parts = text.split(tag)
                # Remove the tagged content
                if len(parts) > 1 and "\n" in parts[1]:
                    parts[1] = parts[1].split("\n", 1)[1]
                text = "".join(parts)
        return text.strip()
    
    def start_combat(self, enemy_name: str):
        """Start combat with an enemy."""
        # Find the enemy in the world data
        enemy = None
        for e in self.world_data["enemies"]:
            if e["name"].lower() == enemy_name.lower():
                enemy = e
                break
        
        # If enemy not found, create a generic one
        if not enemy:
            difficulty = random.randint(1, min(10, self.turn_count // 5 + 1))
            enemy = {
                "name": enemy_name,
                "difficulty": difficulty,
                "health": 20 * difficulty,
                "attack": 5 + difficulty * 2,
                "defense": 2 + difficulty,
                "description": f"A mysterious {enemy_name}."
            }
        
        # Set combat state
        self.in_combat = True
        self.current_enemy = enemy.copy()  # Create a copy to modify during combat
        
        # Display combat start message
        print(Colors.RED + "\n" + "=" * 80)
        print(Colors.RED + f"COMBAT: {self.player['name']} vs {enemy['name']}")
        print(Colors.RED + "=" * 80)
        print(Colors.RED + f"\n{enemy['description']}")
        print(Colors.RED + f"\nThe {enemy['name']} looks ready for battle!")
        print(Colors.RED + f"\nEnemy stats: Health: {enemy['health']}, Attack: {enemy['attack']}, Defense: {enemy['defense']}")
        
        # Add to knowledge base
        self.add_to_knowledge_base(f"Encountered and fought {enemy['name']}")
    
    def combat_turn(self):
        """Handle a turn during combat."""
        # Display combat status
        print(Colors.RED + "\n" + "-" * 40)
        print(Colors.RED + f"YOUR HEALTH: {self.player['health']}/{self.player['max_health']}")
        print(Colors.RED + f"ENEMY HEALTH: {self.current_enemy['health']}")
        print(Colors.RED + "-" * 40)
        
        # Get player action
        print(Colors.GREY + "\nCombat options: attack, use [item], defend, flee")
        action = input(Colors.BOLD + "What will you do? > ")
        
        # Process action
        if action.lower() in ['attack', 'a']:
            self.player_attack()
        elif action.lower().startswith('use '):
            item_name = action[4:].strip()
            self.use_item(item_name)
        elif action.lower() in ['defend', 'd']:
            self.player_defend()
        elif action.lower() in ['flee', 'f', 'run']:
            self.attempt_flee()
        else:
            print(Colors.RED + "Invalid combat action. Try again.")
            return
            
        # Check if enemy is defeated
        if self.current_enemy['health'] <= 0:
            self.resolve_combat(True)
            return
            
        # Enemy turn
        self.enemy_attack()
        
        # Check if player is defeated
        if self.player['health'] <= 0:
            self.resolve_combat(False)
            return
    
    def player_attack(self):
        """Handle player attack during combat."""
        # Calculate damage
        base_damage = random.randint(self.player['attack'] // 2, self.player['attack'])
        damage = max(1, base_damage - self.current_enemy['defense'] // 2)
        
        # Apply damage
        self.current_enemy['health'] -= damage
        
        # Display result
        print(Colors.RED + f"\nYou attack the {self.current_enemy['name']} for {damage} damage!")
        
        # Critical hit (25% chance for 50% extra damage)
        if random.random() < 0.25:
            crit_damage = damage // 2
            self.current_enemy['health'] -= crit_damage
            print(Colors.RED + Colors.BOLD + f"Critical hit! +{crit_damage} bonus damage!")
    
    def enemy_attack(self):
        """Handle enemy attack during combat."""
        # Calculate damage
        base_damage = random.randint(self.current_enemy['attack'] // 2, self.current_enemy['attack'])
        damage = max(1, base_damage - self.player['defense'] // 2)
        
        # Apply damage
        self.player['health'] -= damage
        
        # Display result
        print(Colors.RED + f"\nThe {self.current_enemy['name']} attacks you for {damage} damage!")
    
    def player_defend(self):
        """Handle player defense during combat."""
        # Temporarily increase defense
        temp_defense = self.player['defense'] // 2
        self.player['defense'] += temp_defense
        
        # Recover some health
        heal_amount = self.player['max_health'] // 20
        self.player['health'] = min(self.player['max_health'], self.player['health'] + heal_amount)
        
        # Display result
        print(Colors.RED + f"\nYou take a defensive stance, increasing your defense by {temp_defense}.")
        print(Colors.RED + f"You recover {heal_amount} health.")
        
        # Enemy attack with reduced damage
        base_damage = random.randint(self.current_enemy['attack'] // 3, self.current_enemy['attack'] // 2)
        damage = max(1, base_damage - self.player['defense'] // 2)
        self.player['health'] -= damage
        
        print(Colors.RED + f"The {self.current_enemy['name']} attacks, but you block most of it! {damage} damage taken.")
        
        # Reset defense
        self.player['defense'] -= temp_defense
    
    def attempt_flee(self):
        """Handle player attempt to flee from combat."""
        # Success chance depends on turn count
        flee_chance = 0.6 + (self.turn_count / 100)  # Increases slightly over time
        
        if random.random() < flee_chance:
            print(Colors.RED + f"\nYou successfully escape from the {self.current_enemy['name']}!")
            self.in_combat = False
            self.current_enemy = None
            self.add_to_knowledge_base(f"Fled from combat with {self.current_enemy['name']}")
        else:
            print(Colors.RED + f"\nYou fail to escape! The {self.current_enemy['name']} attacks while you're vulnerable!")
            
            # Take extra damage for failing to flee
            base_damage = random.randint(self.current_enemy['attack'] // 2, self.current_enemy['attack'])
            damage = max(2, base_damage - self.player['defense'] // 3)
            self.player['health'] -= damage
            
            print(Colors.RED + f"You take {damage} damage!")
    
    def resolve_combat(self, player_won: bool):
        """Resolve the combat encounter."""
        if player_won:
            print(Colors.GREEN + f"\nYou defeated the {self.current_enemy['name']}!")
            
            # Reward: chance to find an item
            if random.random() < 0.6:  # 60% chance
                self.generate_combat_reward()
                
            # Recover some health after winning
            heal_amount = self.player['max_health'] // 10
            self.player['health'] = min(self.player['max_health'], self.player['health'] + heal_amount)
            print(Colors.GREEN + f"You recover {heal_amount} health after the battle.")
            
            # Add to knowledge base
            self.add_to_knowledge_base(f"Defeated {self.current_enemy['name']} in combat")
        else:
            print(Colors.RED + "\nYou have been defeated...")
            print(Colors.RED + "\nAs consciousness fades, a mysterious force intervenes...")
            
            # Player doesn't die, but loses some progress
            self.player['health'] = self.player['max_health'] // 4  # Revive with 25% health
            
            # Chance to lose an item
            if self.player['inventory'] and random.random() < 0.5:
                lost_item = random.choice(self.player['inventory'])
                self.player['inventory'].remove(lost_item)
                print(f"\nYou lost your {lost_item['name']} in the battle!")
            
            print(Colors.RED + "\nYou awaken, weakened but alive.")
            
            # Add to knowledge base
            self.add_to_knowledge_base(f"Was defeated by {self.current_enemy['name']} but mysteriously revived")
        
        # Reset combat state
        self.in_combat = False
        self.current_enemy = None
        
        # Pause for player to read
        input(Colors.GREY + "\nPress Enter to continue...")
    
    def generate_combat_reward(self):
        item = {
            "name": "Health Potion",
            "type": "consumable",
            "effect": "Restores 50 health",
            "description": "A small vial containing a red liquid that heals wounds."
        }
        
        # Add to inventory
        self.player["inventory"].append(item)
        
        # Notify player
        print(Colors.GREEN + f"\nYou found: {item['name']} - {item['description']}")
    
    def find_item(self, item_name: str):
        """Handle finding an item."""
        # Find the item in the world data
        item = None
        for i in self.world_data["items"]:
            if i["name"].lower() == item_name.lower():
                item = i
                break
        
        # If item not found, create a generic one
        if not item:
            item = {
                "name": item_name,
                "type": "misc",
                "effect": "Unknown",
                "description": f"A mysterious {item_name}."
            }
            self.world_data["items"].append(item)
        
        # Add to inventory
        self.player["inventory"].append(item)
        
        # Notify player
        print(Colors.GREEN + f"\nYou found: {item['name']} - {item['description']}")
        
        # Add to knowledge base
        self.add_to_knowledge_base(f"Found {item['name']}")
    
    def use_item(self, item_name: str):
        """Use an item from inventory."""
        # Find the item in inventory
        item_index = None
        for i, item in enumerate(self.player["inventory"]):
            if item["name"].lower() == item_name.lower():
                item_index = i
                break
        
        if item_index is None:
            print(Colors.RED + f"\nYou don't have a {item_name} in your inventory.")
            return
        
        # Get the item
        item = self.player["inventory"][item_index]
        
        # Process based on item type
        if item["type"].lower() == "consumable":
            # Remove from inventory
            self.player["inventory"].pop(item_index)
            
            # Apply effect
            if "heal" in item["effect"].lower() or "health" in item["effect"].lower():
                # Extract number from effect text
                import re
                amount_match = re.search(r'\d+', item["effect"])
                heal_amount = int(amount_match.group()) if amount_match else 20
                
                # Apply healing
                old_health = self.player["health"]
                self.player["health"] = min(self.player["max_health"], self.player["health"] + heal_amount)
                actual_heal = self.player["health"] - old_health
                
                print(Colors.GREEN + f"\nYou used {item['name']} and recovered {actual_heal} health!")
            else:
                print(Colors.GREEN + f"\nYou used {item['name']}. {item['effect']}")
        
        elif item["type"].lower() == "weapon":
            print(Colors.GREEN + f"\nYou equip the {item['name']}.")
            # Extract attack bonus
            import re
            bonus_match = re.search(r'\+(\d+)', item["effect"])
            attack_bonus = int(bonus_match.group(1)) if bonus_match else 5
            
            # Apply attack bonus
            old_attack = self.player["attack"]
            self.player["attack"] += attack_bonus
            
            print(Colors.GREEN + f"Your attack increases from {old_attack} to {self.player['attack']}!")
        
        elif item["type"].lower() == "armor":
            print(f"\nYou equip the {item['name']}.")
            # Extract defense bonus
            import re
            bonus_match = re.search(r'\+(\d+)', item["effect"])
            defense_bonus = int(bonus_match.group(1)) if bonus_match else 3
            
            # Apply defense bonus
            old_defense = self.player["defense"]
            self.player["defense"] += defense_bonus
            
            print(Colors.GREEN + f"Your defense increases from {old_defense} to {self.player['defense']}!")
        
        else:
            print(Colors.GREEN + f"\nYou use {item['name']}. Nothing obvious happens.")
    
    def change_location(self, location_name: str):
        """Handle changing the player's location."""
        # Update current location
        old_location = self.current_location
        self.current_location = location_name
        
        # Find location details
        location_details = None
        for loc in self.world_data["locations"]:
            if loc["name"].lower() == location_name.lower():
                location_details = loc
                break
        
        # Create location if it doesn't exist
        if not location_details:
            location_type = random.choice(["settlement", "dungeon", "wilderness", "landmark"])
            
            # Generate location description
            system_prompt = "You are an RPG location designer. Create a vivid description for a new location."
            prompt = f"Create a detailed description for a location called '{location_name}' in a {self.world_data['theme']} world named {self.world_data['name']}. The location is of type {location_type}."
            
            description = self.generate_ai_response(prompt, system_prompt, max_tokens=200)
            
            location_details = {
                "name": location_name,
                "type": location_type,
                "description": description
            }
            
            self.world_data["locations"].append(location_details)
        
        # Display location change message
        print(Colors.GREEN + f"\nYou have moved from {old_location} to {location_name}.")
        
        # Add to knowledge base
        self.add_to_knowledge_base(f"Traveled from {old_location} to {location_name}")
    
    def add_to_knowledge_base(self, event: str):
        """Add an event to the knowledge base."""
        # Format with turn number
        formatted_event = f"Turn {self.turn_count}: {event}"
        
        # Add to knowledge base
        self.knowledge_base.append(formatted_event)
        
        # Limit size of knowledge base
        if len(self.knowledge_base) > 50:
            self.knowledge_base = self.knowledge_base[-50:]
    
    def show_knowledge_base(self):
        """Display the knowledge base to the player."""
        self.clear_screen()
        print(Colors.GREY + "=" * 80)
        print(Colors.GREY + Colors.BOLD + " " * 30 + "ADVENTURE LOG")
        print(Colors.GREY + "=" * 80)
        
        if not self.knowledge_base:
            print(Colors.GREY + "\nNo significant events recorded yet.")
        else:
            for event in self.knowledge_base:
                print(Colors.GREY + f"\n• {event}")
        
        print(Colors.GREY + "\n" + "=" * 80)
        input(Colors.GREY + "\nPress Enter to continue...")
    
    def show_help(self):
        """Display help information."""
        self.clear_screen()
        print(Colors.GREY + "=" * 80)
        print(Colors.GREY + " " * 35 + "HELP")
        print(Colors.GREY + "=" * 80)
        print(Colors.GREY + "\nCommands:")
        print(Colors.GREY + "  help, h, ?         - Show this help menu")
        print(Colors.GREY + "  status, stats      - Show your character's stats")
        print(Colors.GREY + "  inventory, inv, i  - Show your inventory")
        print(Colors.GREY + "  history, events, kb - Show your adventure log")
        print(Colors.GREY + "  quit, exit, q      - Exit the game")
        print(Colors.GREY + "\nDuring exploration:")
        print(Colors.GREY + "  Just type what you want to do naturally, e.g.:")
        print(Colors.GREY + "  - 'look around'")
        print(Colors.GREY + "  - 'talk to the innkeeper'")
        print(Colors.GREY + "  - 'search for tracks'")
        print(Colors.GREY + "  - 'head north towards the mountains'")
        print(Colors.GREY + "\nDuring combat:")
        print(Colors.GREY + "  attack, a          - Attack the enemy")
        print(Colors.GREY + "  defend, d          - Take a defensive stance")
        print(Colors.GREY + "  use [item]         - Use an item from your inventory")
        print(Colors.GREY + "  flee, f, run       - Attempt to escape combat")
        print(Colors.GREY + "\n" + "=" * 80)
        input(Colors.GREY + "\nPress Enter to continue...")
    
    def show_status(self):
        """Display character status."""
        self.clear_screen()
        print(Colors.GREY + "=" * 80)
        print(Colors.GREY + " " * 30 + "CHARACTER STATUS")
        print(Colors.GREY + "=" * 80)
        print(Colors.GREY + f"\nName: {self.player['name']}")
        print(Colors.GREY + f"Health: {self.player['health']}/{self.player['max_health']}")
        print(Colors.GREY + f"Attack: {self.player['attack']}")
        print(Colors.GREY + f"Defense: {self.player['defense']}")
        print(Colors.GREY + f"Location: {self.current_location}")
        print(Colors.GREY + f"Turn: {self.turn_count}")
        
        if self.in_combat:
            print(Colors.GREY + f"\nCurrently in combat with: {self.current_enemy['name']}")
            print(Colors.GREY + f"Enemy health: {self.current_enemy['health']}")
        
        print(Colors.GREY + "\n" + "=" * 80)
        input(Colors.GREY + "\nPress Enter to continue...")
    
    def show_inventory(self):
        """Display inventory contents."""
        self.clear_screen()
        print(Colors.GREY + "=" * 80)
        print(Colors.GREY + " " * 30 + "INVENTORY")
        print(Colors.GREY + "=" * 80)
        
        if not self.player["inventory"]:
            print(Colors.GREY + "\nYour inventory is empty.")
        else:
            for i, item in enumerate(self.player["inventory"], 1):
                print(Colors.GREY + f"\n{i}. {item['name']} ({item['type']})")
                print(Colors.GREY + f"   Effect: {item['effect']}")
                print(Colors.GREY + f"   {item['description']}")
        
        print(Colors.GREY + "\n" + "=" * 80)
        input(Colors.GREY + "\nPress Enter to continue...")
    
    def quit_game(self):
        """Exit the game."""
        print(Colors.GREY + "\nThank you for playing the AI Text RPG!")
        print(Colors.GREY + "Saving game state...")
        
        # Save game state
        try:
            with open('game_save.json', 'w') as f:
                save_data = {
                    "player": self.player,
                    "world_data": self.world_data,
                    "current_location": self.current_location,
                    "knowledge_base": self.knowledge_base,
                    "turn_count": self.turn_count
                }
                json.dump(save_data, f, indent=2)
            print("Game saved successfully!")
        except Exception as e:
            print(f"Error saving game: {str(e)}")
        
        print("Goodbye!")
        sys.exit(0)
    
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

def main():
    """Main function to run the game."""
    game = AITextRPG()
    try:
        game.setup_game()
    except KeyboardInterrupt:
        print("\n\nGame interrupted. Exiting...")
        sys.exit(0)

if __name__ == "__main__":
    main()