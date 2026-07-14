# Author: Timothy J Thormann
#
# Farm Adventure — fan-out movement, delivery rules, interactive fishing,
# and contextual room item display (items disappear after pickup).

import random
from typing import Dict, List

# ----------------------------
# Map layout (directions -> rooms)
# ----------------------------
ROOMS: Dict[str, Dict[str, object]] = {
    "House":       {"south": "Crop Fields", "item": "Fishing Rod"},
    "Town":        {"south": "Crop Fields", "villain": "Mayor"},  # delivery target
    "Pond":        {"south": "Crop Fields"},
    "Stable":      {"west": "Crop Fields", "item": "Horse & Cart"},
    "Silo":        {"north": "Crop Fields"},
    "Barn":        {"north": "Crop Fields"},
    "Chicken Coop":{"north": "Crop Fields"},
    # Crop Fields is the hub — fan-out north & south, single edges east & west
    "Crop Fields": {
        "north": ["House", "Town", "Pond"],            # fan-out menu
        "south": ["Chicken Coop", "Barn", "Silo"],     # fan-out menu
        "east":  "Stable",
        "west":  "Chicken Coop",
        "item":  "Crops",   # one-time pickup
    },
}

START_ROOM = "House"
REQUIRED_ITEMS = {"Eggs", "Milk", "Crops", "Fish"}
VILLAIN_ROOM = "Town"  # where the Mayor is


# ----------------------------
# UI helpers
# ----------------------------
def show_instructions() -> None:
    print("\n=== Farm Adventure ===")
    print("The Mayor is waiting in Town for you to deliver the goods.")
    print("Collect: Eggs (Coop), Milk (Barn), Crops (Field), Fish (Pond).")
    print("You haven't been a productive farmer, so if you fail you will be evicted.")
    print("Get 2× Feed from Silo BEFORE collecting Eggs or Milk.")
    print("Get Fishing Rod at House BEFORE fishing. At the Pond, use: fish")
    print("Fishing mini-game: watch for 'BITE!' and type 'hook' at the right time.")
    print("Get Horse & Cart at Stable, then deliver everything to the Mayor in Town.")
    print("Commands: go <north|south|east|west> | get <item> | fish | inventory | help | quit")
    print("Fan-out: From Crop Fields, 'go south' or 'go north' prompts a destination menu.")
    print("--------------------------------------------------------------------------")


def show_status(current_room: str, inv: List[str], feed: int, has_cart: bool) -> None:
    """Context-aware room description that hides items once obtained and shows Coop/Barn logic."""
    print(f"\nYou are in the {current_room}")
    print(f"Inventory: {sorted(inv)}  |  Feed: {feed}/2  |  Cart: {has_cart}")

    room_info = ROOMS.get(current_room, {})
    room_item = room_info.get("item")

    # Context-sensitive visibility for general room items
    if isinstance(room_item, str):
        # Hide Fishing Rod once obtained
        if room_item == "Fishing Rod" and "Fishing Rod" not in inv:
            print("You see a Fishing Rod")
        # Hide Crops once obtained
        elif room_item == "Crops" and "Crops" not in inv:
            print("You see Crops")
        # Hide Horse & Cart once obtained
        elif room_item == "Horse & Cart" and not has_cart:
            print("You see your Horse & Cart")

    # Special, dynamic rooms:
    if current_room == "Silo":
        if feed < 2:
            print("There is Feed here. You need a total of 2.")
        else:
            print("You have enough Feed for your animals.")
    elif current_room == "Chicken Coop":
        if feed < 2:
            print("The hens look hungry. No eggs yet — collect more Feed (need 2 total).")
        elif "Eggs" not in inv:
            print("You see some Eggs.")
    elif current_room == "Barn":
        if feed < 2:
            print("The cows need more Feed (2 total) before they can be milked.")
        elif "Milk" not in inv:
            print("The cows are ready — you can collect Milk.")
    elif current_room == "Pond":
        if "Fish" in inv:
            print("A peaceful pond. You've already caught a Fish here.")
        else:
            print("You can fish here — type 'fish'. Watch for 'BITE!' and type 'hook' to catch.")
    elif current_room == VILLAIN_ROOM:
        print("The Mayor awaits your delivery.")


def parse_cmd(s: str) -> List[str]:
    return s.strip().lower().split()


# ----------------------------
# Interactive fishing mini-game
# ----------------------------
def fishing_minigame() -> bool:
    """
    A small text mini-game:
    - Random sequence length (5–8 beats)
    - A single random line shows 'BITE!'
    - Player must type 'hook' exactly on that line
    Returns True if fish is caught.
    """
    beats = random.randint(5, 8)
    bite_on = random.randint(2, beats - 1)  # never first or last beat
    print("\nYou cast your line...")
    print("Watch the water... when you see 'BITE!', type: hook")
    print("(Press Enter to wait; type 'hook' to set the hook.)")

    for i in range(1, beats + 1):
        splash = random.choice(["ripples...", "bubbles...", "still water...", "a gentle tug..."])
        if i == bite_on:
            prompt = input(f"BITE! ({i}/{beats}) ").strip().lower()
            if prompt == "hook":
                print("You set the hook perfectly!")
                if random.random() < 0.85:
                    print("After a brief struggle, you land the fish. 🎣")
                    return True
                else:
                    print("It shakes the hook at the last second! The fish got away.")
                    return False
            else:
                print("You hesitated — the fish spit the lure!")
                return False
        else:
            early = input(f"{splash} ({i}/{beats}) ").strip().lower()
            if early == "hook":
                print("Too early! Nothing on the line. The fish got away.")
                return False

    print("No bites yet... Try again!")
    return False


# ----------------------------
# Movement with fan-out and Town check
# ----------------------------
def move_player(current_room: str, direction_token: str, state: dict) -> str:
    """
    Move from current_room via a direction. Supports fan-out lists for a direction.
    When going to Town, requires Horse & Cart and asks for confirmation.
    """
    direction = direction_token.lower()
    options = ROOMS.get(current_room, {}).get(direction)

    if options is None:
        print("You can't go that way.")
        return current_room

    # Simple edge: single destination string
    if isinstance(options, str):
        dest = options
        return _maybe_gate_town(current_room, dest, state)

    # Fan-out edge: list of destinations -> prompt
    if isinstance(options, list) and options:
        print("Where to?")
        for i, name in enumerate(options, start=1):
            print(f"  {i}) {name}")
        choice = input("Choose a destination (number or name): ").strip()

        dest = None
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(options):
                dest = options[idx - 1]
        else:
            for name in options:
                if choice.lower() == name.lower():
                    dest = name
                    break

        if dest is None:
            print("That destination isn't in the list.")
            return current_room

        return _maybe_gate_town(current_room, dest, state)

    print("No destinations available that way.")
    return current_room


def _maybe_gate_town(current_room: str, dest: str, state: dict) -> str:
    """Enforce Town requirements and confirmation."""
    if dest != "Town":
        return dest
    if not state.get("cart", False):
        print("You don't expect to carry all that to town do you?")
        return current_room
    ans = input("Ready to deliver to the mayor? (y/n): ").strip().lower()
    if ans.startswith('y'):
        print("My cart is loaded and ready — let's go!")
        return "Town"
    print("Okay, we’ll hold off for now.")
    return current_room


# ----------------------------
# Item collection logic
# ----------------------------
def try_get(current_room: str, request: str, inv: List[str], state: dict) -> None:
    """Handle 'get' command with prerequisites and special rules."""
    feed = state["feed"]

    # Normalize common names
    synonyms = {
        "egg": "Eggs", "eggs": "Eggs",
        "milk": "Milk",
        "crops": "Crops", "crop": "Crops",
        "fish": "Fish",
        "fishing rod": "Fishing Rod", "rod": "Fishing Rod",
        "horse": "Horse & Cart", "cart": "Horse & Cart", "horse & cart": "Horse & Cart",
        "feed": "Feed", "feeds": "Feed"
    }
    item = synonyms.get(request.lower(), request.title())

    # Special: Feed (can be taken up to 2 times from Silo)
    if item == "Feed":
        if current_room != "Silo":
            print("There is no Feed here.")
            return
        if feed >= 2:
            print("You already have enough Feed (2).")
            return
        state["feed"] += 1
        print(f"You collected Feed ({state['feed']}/2).")
        return

    # Fishing Rod (House)
    if item == "Fishing Rod":
        if current_room != "House":
            print("The Fishing Rod is at the House.")
            return
        if "Fishing Rod" in inv:
            print("You already have the Fishing Rod.")
            return
        inv.append("Fishing Rod")
        print("You picked up the Fishing Rod.")
        # Remove from room so it no longer displays
        if ROOMS["House"].get("item") == "Fishing Rod":
            del ROOMS["House"]["item"]
        return

    # Crops (Crop Fields)
    if item == "Crops":
        if current_room != "Crop Fields":
            print("Crops are in the Crop Fields.")
            return
        if "Crops" in inv:
            print("You already collected the Crops.")
            return
        inv.append("Crops")
        print("You picked up the Crops.")
        # remove one-time item from room display
        if ROOMS["Crop Fields"].get("item") == "Crops":
            del ROOMS["Crop Fields"]["item"]
        return

    # Horse & Cart (Stable)
    if item == "Horse & Cart":
        if current_room != "Stable":
            print("Your Horse & Cart are at the Stable.")
            return
        if state["cart"]:
            print("You already have your Horse & Cart.")
            return
        state["cart"] = True
        print("You got your Horse & Cart. You can now haul goods to Town.")
        # remove from room so it no longer displays
        if ROOMS["Stable"].get("item") == "Horse & Cart":
            del ROOMS["Stable"]["item"]
        return

    # Egg (Coop) — needs 2× Feed
    if item == "Eggs":
        if current_room != "Chicken Coop":
            print("Eggs are at the Chicken Coop.")
            return
        if "Eggs" in inv:
            print("You already collected the Eggs.")
            return
        if state["feed"] < 2:
            print("You need 2× Feed from the Silo before the hens will lay eggs.")
            return
        inv.append("Eggs")
        print("You collected Eggs.")
        return

    # Milk (Barn) — needs 2× Feed
    if item == "Milk":
        if current_room != "Barn":
            print("Milk is at the Barn.")
            return
        if "Milk" in inv:
            print("You already collected the Milk.")
            return
        if state["feed"] < 2:
            print("You need 2× Feed from the Silo before the cows will give milk.")
            return
        inv.append("Milk")
        print("You collected Milk.")
        return

    # Fish (Pond) — interactive fishing mini-game (requires Fishing Rod)
    if item == "Fish":
        if current_room != "Pond":
            print("You can catch Fish at the Pond.")
            return
        if "Fish" in inv:
            print("You already caught a Fish, don't over do it.")
            return
        if "Fishing Rod" not in inv:
            print("You need the Fishing Rod from the House before you can fish.")
            return
        if fishing_minigame():
            inv.append("Fish")
        return

    print("That item can't be collected here.")


# Dedicated 'fish' command for convenience
def do_fish(current_room: str, inv: List[str]) -> None:
    if current_room != "Pond":
        print("You can only fish at the Pond.")
        return
    if "Fishing Rod" not in inv:
        print("You need the Fishing Rod from the House before you can fish.")
        return
    if "Fish" in inv:
        print("You already caught a Fish.")
        return
    if fishing_minigame():
        inv.append("Fish")


# ----------------------------
# End conditions (in Town with cart)
# ----------------------------
def end_state_if_any(current_room: str, inv: List[str], state: dict) -> str:
    """
    Return 'win', 'lose', or '' (continue).
    Win: in Town with cart and all required items.
    Lose: in Town with cart but missing any required item.
    """
    if current_room != VILLAIN_ROOM or not state["cart"]:
        return ""
    have = set(x for x in inv if x in REQUIRED_ITEMS)
    if have == REQUIRED_ITEMS:
        return "win"
    return "lose"


# ----------------------------
# Game loop
# ----------------------------
def main() -> None:
    current_room = START_ROOM
    inventory: List[str] = []
    state = {"feed": 0, "cart": False}

    show_instructions()

    while True:
        show_status(current_room, inventory, state["feed"], state["cart"])
        raw = input("Enter your move: ").strip()
        if not raw:
            print("Please enter a command. Type 'help' for options.")
            continue

        tokens = parse_cmd(raw)
        cmd = tokens[0]

        if cmd in ("quit", "exit"):
            print("Thanks for playing. Goodbye!")
            break

        if cmd in ("help", "?"):
            show_instructions()
            continue

        if cmd in ("inventory", "inv"):
            have = sorted([x for x in inventory if x in REQUIRED_ITEMS])
            print(f"Inventory: {sorted(inventory)}")
            print(f"Delivery set ready: {have} ({len(have)}/{len(REQUIRED_ITEMS)})")
            print(f"Feed: {state['feed']}/2  |  Cart: {state['cart']}")
            continue

        # Movement
        if cmd == "go":
            if len(tokens) < 2:
                print("Usage: go <north|south|east|west>")
                continue
            next_room = move_player(current_room, tokens[1], state)
            if next_room != current_room:
                current_room = next_room
                print(f"You walk to the {current_room}.")

        # Item pickup
        elif cmd == "get":
            if len(tokens) < 2:
                print("Usage: get <item>")
                continue
            request = " ".join(tokens[1:])
            try_get(current_room, request, inventory, state)

        # Interactive fishing command
        elif cmd == "fish":
            do_fish(current_room, inventory)

        else:
            print("Invalid command. Try 'go <dir>' or 'get <item>' or 'fish' or 'help'.")
            continue

        # Check end conditions when entering Town with the cart
        outcome = end_state_if_any(current_room, inventory, state)
        if outcome == "win":
            print("\n🎉 Congratulations! You delivered Eggs, Milk, Crops, and Fish to the Mayor.")
            print("You avoided eviction, You win! Thanks for playing.")
            break
        elif outcome == "lose":
            missing = sorted(list(REQUIRED_ITEMS - set(x for x in inventory if x in REQUIRED_ITEMS)))
            print("\n😬 The Mayor expected a full delivery, but you're missing:", ", ".join(missing))
            print("It's time to move out, GAME OVER! (Return fully prepared next time.)")
            break

    input("\nPress Enter to exit...")
if __name__ == "__main__":
    main()
