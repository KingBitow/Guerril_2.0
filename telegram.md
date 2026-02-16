Setup Instructions
1. Install Requirements
bash
Copy
pip install python-telegram-bot requests
2. Configure Bot Token
Replace YOUR_BOT_TOKEN_HERE with your actual token from @BotFather
3. Optional: Whitelist Users
Change ALLOWED_USERS = [] to ALLOWED_USERS = [123456789] (your user ID)
4. Run
bash
Copy
python telegram_bot.py
How Users Interact
Table
Copy
User Action	Bot Response
Send /start	Generates email, starts monitoring
Wait	Bot auto-detects codes/links
Receive code	Message: "🔢 Code: 123456"
Receive link	Message with button "🔗 Open Verification Link"
Tap button	Opens link in browser
Send /stop	Stops monitoring
For 24/7 Hosting (Free)
PythonAnywhere:
Upload code
Open Bash console
pip3 install python-telegram-bot requests --user
python3 telegram_bot.py
Render:
Create Web Service
Connect GitHub repo
Set environment variable BOT_TOKEN
Change last line to use webhook instead of polling
Want me to add the webhook version for Render deployment?
