import random

def play_game():
    print("=" * 40)
    print("   Welcome to the Number Guessing Game!")
    print("=" * 40)

    difficulty = input("\nPick a difficulty:\n  1. Easy   (1-10)\n  2. Medium (1-50)\n  3. Hard   (1-100)\nYour choice (1/2/3): ").strip()

    if difficulty == "1":
        max_num, max_tries = 10, 5
    elif difficulty == "3":
        max_num, max_tries = 100, 7
    else:
        max_num, max_tries = 50, 6

    secret = random.randint(1, max_num)
    tries = 0

    print(f"\nI'm thinking of a number between 1 and {max_num}.")
    print(f"You have {max_tries} tries. Good luck!\n")

    while tries < max_tries:
        remaining = max_tries - tries
        try:
            guess = int(input(f"[{remaining} tries left] Your guess: "))
        except ValueError:
            print("  Please enter a whole number!\n")
            continue

        tries += 1

        if guess == secret:
            print(f"\n  *** You got it in {tries} tries! The number was {secret}. ***\n")
            return True
        elif guess < secret:
            print("  Too low! Try higher.\n")
        else:
            print("  Too high! Try lower.\n")

    print(f"\n  Game over! The number was {secret}. Better luck next time!\n")
    return False

def main():
    while True:
        play_game()
        again = input("Play again? (yes/no): ").strip().lower()
        if again not in ("yes", "y"):
            print("\nThanks for playing! Bye!\n")
            break
        print()

if __name__ == "__main__":
    main()
