import logging
import asyncio
import requests
import re
import time
import json
import os
from urllib.parse import unquote
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, JobQueue
from datetime import datetime

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============ CONFIGURATION ============
# Replace with your actual bot token from @BotFather
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# Optional: Add your Telegram user ID here to restrict access
# Leave empty [] to allow anyone, or add [123456789] to whitelist
ALLOWED_USERS = []

# ============ GUERRILLA MAIL API ============
class GuerrillaMailAPI:
    def __init__(self):
        self.session = requests.Session()
        self.email_user = None
        self.email_domain = None
        self.sid_token = None
        self.api_url = "https://api.guerrillamail.com/ajax.php"
        
    def generate_email(self):
        """Generate a new temporary email address"""
        try:
            response = self.session.get(f"{self.api_url}?f=get_email_address", timeout=10)
            data = response.json()
            
            self.email_user = data.get('email_addr').split('@')[0]
            self.email_domain = data.get('email_addr').split('@')[1]
            self.sid_token = data.get('sid_token')
            
            return data.get('email_addr')
        except Exception as e:
            logger.error(f"Error generating email: {e}")
            return None
    
    def check_inbox(self):
        """Check for new emails"""
        try:
            if not self.sid_token:
                return []
                
            response = self.session.get(
                f"{self.api_url}?f=check_email&sid_token={self.sid_token}&seq=0",
                timeout=10
            )
            data = response.json()
            return data.get('list', [])
        except Exception as e:
            logger.error(f"Error checking inbox: {e}")
            return []
    
    def fetch_email(self, email_id):
        """Fetch full email content"""
        try:
            response = self.session.get(
                f"{self.api_url}?f=fetch_email&sid_token={self.sid_token}&email_id={email_id}",
                timeout=10
            )
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching email: {e}")
            return {}

# ============ LINK EXTRACTOR ============
class LinkExtractor:
    LINK_PATTERNS = [
        r'https?://[^\s<>"{}|\\^`\[\]]+?(?:verify|confirm|activate|validate|auth|verification|confirmation)[^\s<>"{}|\\^`\[\]]*',
        r'https?://[^\s<>"{}|\\^`\[\]]+?(?:token|code|key|auth|verify)=[a-zA-Z0-9_-]+[^\s<>"{}|\\^`\[\]]*',
        r'https?://(?:instagram|twitter|x|facebook|meta|google|gmail|youtube|tiktok|snapchat|reddit|discord|github|linkedin|telegram)\.com/[^\s<>"{}|\\^`\[\]]*',
        r'https?://(?:bit\.ly|tinyurl|t\.co|goo\.gl|ow\.ly|short\.link)/[a-zA-Z0-9]+',
        r'https?://[^\s<>"{}|\\^`\[\]]+?/verify/[a-zA-Z0-9_-]+',
        r'https?://[^\s<>"{}|\\^`\[\]]+?/confirm/[a-zA-Z0-9_-]+',
        r'https?://[^\s<>"{}|\\^`\[\]]+?\?[^\s<>"{}|\\^`\[\]]*token=[^\s<>"{}|\\^`\[\]]+',
        r'https?://[^\s<>"{}|\\^`\[\]]+?\?[^\s<>"{}|\\^`\[\]]*code=[^\s<>"{}|\\^`\[\]]+',
    ]
    
    def extract_links(self, text):
        if not text:
            return []
            
        links = []
        text = unquote(text)
        
        for pattern in self.LINK_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                clean_link = match.strip('.,;:"\'<>()[]{}|\\')
                if clean_link.startswith('http') and len(clean_link) > 10 and '.' in clean_link:
                    links.append(clean_link)
        
        seen = set()
        unique_links = []
        for link in links:
            if link.lower() not in seen:
                seen.add(link.lower())
                unique_links.append(link)
        
        return unique_links
    
    def extract_code(self, text):
        if not text:
            return None
            
        patterns = [
            r'\b(\d{4,6})\b(?![\d])',
            r'code[:\s]*(\d{4,6})',
            r'code is[:\s]*(\d{4,6})',
            r'verification[:\s]*(\d{4,6})',
            r'OTP[:\s]*(\d{4,6})',
            r'password[:\s]*(\d{4,6})',
            r'(\d{4,6})[:\s]*is your',
            r'(\d{4,6})[:\s]*is the',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                code = match.group(1)
                if 1000 <= int(code) <= 999999:
                    return code
        return None

# ============ USER SESSIONS ============
# Store user data: {user_id: {'api': GuerrillaMailAPI, 'email': str, 'checked_ids': set, 'found_codes': set, 'found_links': set}}
user_sessions = {}

# ============ BOT COMMANDS ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - generate new email"""
    user_id = update.effective_user.id
    
    # Check whitelist
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        await update.message.reply_text("⛔ Access denied. This bot is private.")
        return
    
    # Initialize session
    api = GuerrillaMailAPI()
    email = api.generate_email()
    
    if not email:
        await update.message.reply_text("❌ Failed to generate email. Please try again.")
        return
    
    # Store session
    user_sessions[user_id] = {
        'api': api,
        'email': email,
        'checked_ids': set(),
        'found_codes': set(),
        'found_links': set(),
        'active': True
    }
    
    # Create stop button
    keyboard = [[InlineKeyboardButton("🛑 Stop Monitoring", callback_data='stop')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        f"✅ *Email Generated!*\n\n"
        f"📧 `{email}`\n\n"
        f"Use this email for signup.\n"
        f"I'm monitoring for codes and links...\n\n"
        f"⏱ Auto-checking every 5 seconds"
    )
    
    await update.message.reply_text(
        message, 
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    
    # Start monitoring job
    context.job_queue.run_repeating(
        check_email_job, 
        interval=5, 
        first=5,
        data={'user_id': user_id},
        name=f"monitor_{user_id}"
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop monitoring"""
    user_id = update.effective_user.id
    
    if user_id in user_sessions:
        user_sessions[user_id]['active'] = False
        del user_sessions[user_id]
    
    # Remove job
    current_jobs = context.job_queue.get_jobs_by_name(f"monitor_{user_id}")
    for job in current_jobs:
        job.schedule_removal()
    
    await update.message.reply_text("🛑 Monitoring stopped. Email discarded.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check current status"""
    user_id = update.effective_user.id
    
    if user_id not in user_sessions:
        await update.message.reply_text("No active session. Use /start to generate email.")
        return
    
    session = user_sessions[user_id]
    email = session['email']
    codes = len(session['found_codes'])
    links = len(session['found_links'])
    
    await update.message.reply_text(
        f"📊 *Status*\n\n"
        f"📧 Email: `{email}`\n"
        f"🔢 Codes found: {codes}\n"
        f"🔗 Links found: {links}\n"
        f"✅ Active: {'Yes' if session['active'] else 'No'}",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help"""
    help_text = (
        "*📱 Guerrilla Mail Bot Commands*\n\n"
        "/start - Generate new email and start monitoring\n"
        "/stop - Stop monitoring and discard email\n"
        "/status - Check current session status\n"
        "/help - Show this help message\n\n"
        "*How it works:*\n"
        "1. Click /start to get temp email\n"
        "2. Copy the email address\n"
        "3. Use it on any website\n"
        "4. Wait for verification email\n"
        "5. I'll send you the code or link automatically!\n\n"
        "When I find a link, I'll send a button you can tap to open it."
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

# ============ CALLBACK HANDLER ============
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if query.data == 'stop':
        await stop(update, context)
        await query.edit_message_text("🛑 Monitoring stopped. Use /start to create new email.")
    
    elif query.data.startswith('open_link_'):
        # Extract link index
        try:
            idx = int(query.data.split('_')[-1])
            if user_id in user_sessions and idx < len(user_sessions[user_id].get('links_list', [])):
                link = user_sessions[user_id]['links_list'][idx]
                await query.edit_message_text(
                    f"🔗 *Opening Link...*\n\n{link}",
                    parse_mode='Markdown'
                )
                # Note: We can't actually open browser on user's device
                # User needs to click the URL in the message
        except:
            pass

# ============ EMAIL MONITORING JOB ============
async def check_email_job(context: ContextTypes.DEFAULT_TYPE):
    """Background job to check emails"""
    job_data = context.job.data
    user_id = job_data['user_id']
    
    if user_id not in user_sessions:
        return
    
    session = user_sessions[user_id]
    if not session['active']:
        return
    
    api = session['api']
    link_extractor = LinkExtractor()
    
    try:
        emails = api.check_inbox()
        
        for email in emails:
            email_id = email.get('mail_id')
            
            if email_id not in session['checked_ids']:
                session['checked_ids'].add(email_id)
                
                # Fetch full email
                full_email = api.fetch_email(email_id)
                subject = full_email.get('mail_subject', 'No Subject')
                body = full_email.get('mail_body', '')
                sender = full_email.get('mail_from', 'Unknown')
                
                full_text = f"{subject} {body}"
                
                # Check for verification code
                code = link_extractor.extract_code(full_text)
                if code and code not in session['found_codes']:
                    session['found_codes'].add(code)
                    
                    message = (
                        f"🔢 *Verification Code Found!*\n\n"
                        f"Code: `{code}`\n"
                        f"From: {sender}\n"
                        f"Subject: {subject}"
                    )
                    
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                
                # Check for verification links
                links = link_extractor.extract_links(full_text)
                new_links = [link for link in links if link not in session['found_links']]
                
                if new_links:
                    for i, link in enumerate(new_links):
                        session['found_links'].add(link)
                        
                        # Store links for callback
                        if 'links_list' not in session:
                            session['links_list'] = []
                        session['links_list'].append(link)
                        
                        # Create button to open link
                        keyboard = [[
                            InlineKeyboardButton("🔗 Open Verification Link", url=link)
                        ]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        # Truncate long links for display
                        display_link = link if len(link) < 100 else link[:97] + "..."
                        
                        message = (
                            f"🔗 *Verification Link Found!*\n\n"
                            f"From: {sender}\n"
                            f"Subject: {subject}\n\n"
                            f"Tap the button below to open:"
                        )
                        
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=message,
                            parse_mode='Markdown',
                            reply_markup=reply_markup
                        )
                        
                        # Also send raw link as backup
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=f"`{link}`",
                            parse_mode='Markdown'
                        )
                        
    except Exception as e:
        logger.error(f"Error in check_email_job for user {user_id}: {e}")

# ============ ERROR HANDLER ============
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.error(f"Update {update} caused error {context.error}")

# ============ MAIN ============
def main():
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    print("🤖 Bot is running...")
    print("Press Ctrl+C to stop")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
