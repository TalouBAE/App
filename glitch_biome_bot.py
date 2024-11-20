import tkinter as tk
from tkinter import messagebox
import webbrowser
import json
import discord
import re
import requests
import threading

# Constants
CONFIG_FILE = "user_config.json"
TARGET_CHANNEL_ID_BIOMES = 1282542323590496277  # The #biomes channel ID
KEYWORDS = ["GLITCHED", "GLITCH BIOME", "OMG GLITCH", "REAL GLITCH", "GLITCHED BIOME", "GLITCH"]
LINK_REGEX = r"https:\/\/www\.roblox\.com\/share\?code=[a-zA-Z0-9]+&type=Server"
SUPPORT_SERVER_LINK = "https://discord.gg/sFqzpzmk"  # Support Discord server link


class BiomeMonitorClient(discord.Client):
    def __init__(self, token, webhook_url):
        super().__init__()
        self.token = token
        self.webhook_url = webhook_url
        self.running = True  # Track whether the bot should keep running

    async def on_ready(self):
        print(f"Logged in as {self.user}. Monitoring channel ID {TARGET_CHANNEL_ID_BIOMES}.")

    async def on_message(self, message):
        if not self.running:
            await self.close()
            return

        if message.channel.id != TARGET_CHANNEL_ID_BIOMES or message.author.bot:
            return

        # Check for Roblox private server link
        link_match = re.search(LINK_REGEX, message.content)
        if not link_match:
            return

        # Check for relevant keywords (case-insensitive)
        content_upper = message.content.upper()
        for keyword in KEYWORDS:
            if keyword.upper() in content_upper:
                # Send message to the Discord webhook
                payload = {
                    "content": f"**Detected a potential glitch biome post:**\n{message.content}\n**Link:** {link_match.group(0)}"
                }
                response = requests.post(self.webhook_url, json=payload)
                if response.status_code == 204:
                    print(f"Sent to webhook: {message.content}")
                else:
                    print(f"Failed to send to webhook. Status Code: {response.status_code}")
                break

    def run_bot(self):
        try:
            self.run(self.token)
        except discord.LoginFailure:
            messagebox.showerror("Error", "Invalid Discord Token. Please check your input and try again.")
            print("Failed to log in. Check the token.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def stop_bot(self):
        self.running = False
        print("Stopping bot...")


def save_config(token, webhook_url):
    """Save user input to a JSON file."""
    config = {
        "token": token,
        "webhook_url": webhook_url,
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)


def load_config():
    """Load user input from the JSON file."""
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"token": "", "webhook_url": ""}


def start_bot():
    global bot_thread, bot  # Track the bot instance and thread
    # Get user inputs
    token = token_entry.get().strip()
    webhook_url = webhook_entry.get().strip()

    # Validate inputs
    if not token or not webhook_url:
        messagebox.showerror("Error", "All fields must be filled out.")
        return

    try:
        # Save the user input
        save_config(token, webhook_url)

        # Initialize and start the bot in a separate thread
        bot = BiomeMonitorClient(token, webhook_url)
        bot_thread = threading.Thread(target=bot.run_bot)
        bot_thread.start()
        messagebox.showinfo("Success", "The bot is now running! Use the Stop button to stop it.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")


def stop_bot():
    global bot
    if bot:
        bot.stop_bot()
        bot_thread.join()  # Ensure the bot thread stops completely
        messagebox.showinfo("Success", "The bot has been stopped.")
        print("Bot stopped.")


def show_disclaimer():
    def open_support_server():
        webbrowser.open(SUPPORT_SERVER_LINK)

    disclaimer_message = (
        "Disclaimer:\n\n"
        "This application is safe and secure. It does not store or transmit your Discord token, channel ID, "
        "or webhook URL to any external services.\n\n"
        "If you have any questions or concerns, please contact me on Discord by sending a message to `taloubi`.\n\n"
        "Alternatively, click 'Contact Me' to join my support Discord server."
    )

    # Create a disclaimer popup
    disclaimer_popup = tk.Toplevel(root)
    disclaimer_popup.title("Disclaimer")
    disclaimer_label = tk.Label(disclaimer_popup, text=disclaimer_message, wraplength=400, justify="left")
    disclaimer_label.pack(padx=20, pady=10)

    # Add buttons for acknowledgment and contact
    button_frame = tk.Frame(disclaimer_popup)
    button_frame.pack(pady=10)

    tk.Button(button_frame, text="OK", command=disclaimer_popup.destroy).pack(side="left", padx=5)
    tk.Button(button_frame, text="Contact Me", command=open_support_server).pack(side="left", padx=5)

    # Wait for the user to acknowledge before continuing
    root.wait_window(disclaimer_popup)


# Load existing configuration
config = load_config()

# Create the GUI
root = tk.Tk()
root.title("Glitch Biome Bot Setup")

# Show the disclaimer at the start
root.after(100, show_disclaimer)

# Discord Token
tk.Label(root, text="Discord Token:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
token_entry = tk.Entry(root, width=50)
token_entry.insert(0, config.get("token", ""))  # Pre-fill with saved data
token_entry.grid(row=0, column=1, padx=10, pady=5)

# Webhook URL
tk.Label(root, text="Webhook URL:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
webhook_entry = tk.Entry(root, width=50)
webhook_entry.insert(0, config.get("webhook_url", ""))  # Pre-fill with saved data
webhook_entry.grid(row=1, column=1, padx=10, pady=5)

# Start Bot Button
start_button = tk.Button(root, text="Start Bot", command=start_bot)
start_button.grid(row=2, column=0, pady=10)

# Stop Bot Button
stop_button = tk.Button(root, text="Stop Bot", command=stop_bot)
stop_button.grid(row=2, column=1, pady=10)

# Run the GUI loop
root.mainloop()
