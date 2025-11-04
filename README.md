# 💊 Meds Reminder Bot

# 🔒 Disclaimer

This project is a proof of concept and not a medical device. It should not be used as a substitute for medical advice or for life-critical medication reminders. Always follow professional healthcare guidance.

---

## 🚀 Overview  
**Meds Reminder Bot** is a chatbot that pings you when it’s time to take your meds — but not in a boring “please take 20mg now” way.

You choose:
- what the reminder is for,
- when you want to be pinged,
- and which “voice” should yell at you.

At the scheduled time, the bot DMs you in-character.  
Examples:
- `Gotham needs you. Take your Adderall so you can focus and stop Joker before 9AM.` (Batman voice)
- `Hydrate, you goblin. Drink water right now.` (Gremlin best friend voice)
- `Proud of you. Take your anxiety meds and go be brilliant.` (Soft supportive voice)

This project is built for real brains in chaos: ADHD, Autism, PTSD, Anxiety, & Depression = executive dysfunction, 47 open tasks, and zero working memory. 

It’s not a medical device. It’s: 
    A reminder + do it in a way that gives me a hit of Dopamine = the version of me that actually remembers to take my meds.


## ✨ Key Features
- 🕒 **Custom Reminders by Time:** Set one or more reminders (08:00, 14:00, etc.) for any med / habit / routine.
- 🎭 **Persona-Based Messaging:** Pick the “voice” your reminder arrives in (e.g. Batman, drill sergeant, tender best friend). The bot uses that persona when it DMs you.
- 💾 **Persistent Storage:** Your reminders and persona choices are stored in a NoSQL database (DynamoDB locally, easily portable to Firestore on Google Cloud).
- ✅ **Acknowledge / Taken Flow (optional):** You can reply to confirm you took it, so you can keep yourself honest.
- 📜 **Last Taken Memory:** The bot can keep lightweight state like “last taken at 08:05” so you don’t double-dose.
- 🔐 **Private by Default:** Reminders arrive in DMs. This is built for you, not for an employer, parent, or caregiver.
- 🧩 **Extensible for AI:** The persona lines can be static or generated. The design supports plugging in an LLM later so Batman doesn’t repeat himself forever.

## 🧠 Architecture
**Tech Stack**
- **Language:** Python 3.x
- **Discord SDK:** `discord.py` for commands and DMs (other chat apps to come!)
- **Chat Abstraction:** ChatManager + DiscordChatClient (chat-platform agnostic)
- **AI Abstraction:** AIManager (provider-agnostic; no AI currently active)
- **Scheduler:** Internal async loop (runs every 15 minutes or via HTTP endpoint)
- **Config:** .env managed via python-dotenv
- **Logging:** Standard Python logging

**High-Level Flow:**
```text
User → "!r" → bot stores reminder {time, label, persona} in DB
Scheduler wakes up at that time
↓
Bot DMs the user in that persona’s voice
↓
User can respond "taken" to mark it
```

Example reminder object (conceptual):
{
    "discord_user_id": "1234567890",
    "timezone": "America/New_York",
    "reminders": [
        {
            "label": "Adderall",
            "time": "08:00",
            "persona": "batman",
            "active": true,
            "lastTakenIso": "2025-10-25T12:05:00Z"
        }
    ]
}

## 🧩 Future Enhancements
- 🔊 Dynamic persona text generation so you don’t get the same line every morning.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your_username/meds-reminder-bot.git

2. Install dependencies
   ```bash
   pip install -r requirements.txt

3. Configure the bot:
   - Create a .env file in the config directory.
   - Add your Discord bot token and DB connection details

    # Discord
    DISCORD_BOT_TOKEN=your_discord_token_here
    
    # Google Cloud
    GOOGLE_PROJECT_ID=your_project_id
    GOOGLE_APPLICATION_CREDENTIALS=path/to/service_account.json
    
    # Optional AI
    GEMINI_API_KEY=your_gemini_api_key_here
⚠️ Never commit .env or your service account JSON file. ⚠️

Database schema Explanation
  https://lucid.app/lucidchart/b05ccabb-b5c2-4801-a6a1-cb31ca88e296/edit?invitationId=inv_0c1e1fd0-fe23-4a46-8ec2-5ed6615abf1b&page=0_0#


4. Run the bot:
   ```bash
   python bot.py

## Usage
   Once the bot is running and added to your Discord server, you can interact with it using the following command:

   !r: Set a reminder. The bot will prompt you to enter the desired character/persona for the reminder and the time for the reminder in HH:MM format (24-hour clock).
    !l: Shows all active reminders
    !dr: Delects a specific reminder
    !help: Displays available commands

## 💡 Disclaimer Reminder
    This project is built for people, not patients.
    It’s designed to remind, encourage, and motivate, but never to diagnose or treat.
    Always follow your healthcare provider’s instructions.