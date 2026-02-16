import tkinter as tk
from tkinter import ttk, messagebox
import requests
import re
import threading
import time
import random
import string
import webbrowser
from urllib.parse import unquote
import pyperclip

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
            # Get session token first
            response = self.session.get(f"{self.api_url}?f=get_email_address")
            data = response.json()
            
            self.email_user = data.get('email_addr').split('@')[0]
            self.email_domain = data.get('email_addr').split('@')[1]
            self.sid_token = data.get('sid_token')
            
            return data.get('email_addr')
        except Exception as e:
            print(f"Error generating email: {e}")
            return None
    
    def check_inbox(self):
        """Check for new emails"""
        try:
            if not self.sid_token:
                return []
                
            response = self.session.get(
                f"{self.api_url}?f=check_email&sid_token={self.sid_token}&seq=0"
            )
            data = response.json()
            return data.get('list', [])
        except Exception as e:
            print(f"Error checking inbox: {e}")
            return []
    
    def fetch_email(self, email_id):
        """Fetch full email content including body"""
        try:
            response = self.session.get(
                f"{self.api_url}?f=fetch_email&sid_token={self.sid_token}&email_id={email_id}"
            )
            return response.json()
        except Exception as e:
            print(f"Error fetching email: {e}")
            return {}

class LinkExtractor:
    """Extract and handle verification links from emails"""
    
    # Comprehensive patterns for verification links
    LINK_PATTERNS = [
        # Generic verification patterns
        r'https?://[^\s<>"{}|\\^`\[\]]+?(?:verify|confirm|activate|validate|auth|verification|confirmation)[^\s<>"{}|\\^`\[\]]*',
        # Token/Code based links
        r'https?://[^\s<>"{}|\\^`\[\]]+?(?:token|code|key|auth|verify)=[a-zA-Z0-9_-]+[^\s<>"{}|\\^`\[\]]*',
        # Major platform specific patterns
        r'https?://(?:instagram|twitter|x|facebook|meta|google|gmail|youtube|tiktok|snapchat|reddit|discord|github|linkedin)\.com/[^\s<>"{}|\\^`\[\]]*',
        # Shortened URLs (bit.ly, tinyurl, etc)
        r'https?://(?:bit\.ly|tinyurl|t\.co|goo\.gl|ow\.ly|short\.link)/[a-zA-Z0-9]+',
        # Email service verification links
        r'https?://[^\s<>"{}|\\^`\[\]]+?/verify/[a-zA-Z0-9_-]+',
        r'https?://[^\s<>"{}|\\^`\[\]]+?/confirm/[a-zA-Z0-9_-]+',
        # Generic secure links with tokens
        r'https?://[^\s<>"{}|\\^`\[\]]+?\?[^\s<>"{}|\\^`\[\]]*token=[^\s<>"{}|\\^`\[\]]+',
        r'https?://[^\s<>"{}|\\^`\[\]]+?\?[^\s<>"{}|\\^`\[\]]*code=[^\s<>"{}|\\^`\[\]]+',
    ]
    
    def __init__(self):
        self.verified_links = []
    
    def extract_links(self, text):
        """Extract all potential verification links from text"""
        if not text:
            return []
            
        links = []
        text = unquote(text)  # URL decode first
        
        for pattern in self.LINK_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Clean the link
                clean_link = match.strip('.,;:"\'<>()[]{}|\\')
                if clean_link.startswith('http'):
                    # Validate it's a proper URL
                    if len(clean_link) > 10 and '.' in clean_link:
                        links.append(clean_link)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_links = []
        for link in links:
            if link.lower() not in seen:
                seen.add(link.lower())
                unique_links.append(link)
        
        return unique_links
    
    def is_verification_link(self, link):
        """Check if a link is likely a verification link"""
        verification_keywords = [
            'verify', 'confirm', 'activate', 'validate', 'auth',
            'verification', 'confirmation', 'activation', 'validation',
            'secure', 'token', 'code', 'key', 'auth'
        ]
        link_lower = link.lower()
        return any(keyword in link_lower for keyword in verification_keywords)
    
    def open_link(self, link):
        """Open link in default browser"""
        try:
            webbrowser.open(link)
            return True
        except Exception as e:
            print(f"Error opening link: {e}")
            return False

class GuerrillaMailApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Shikamaru Nara 2.0→ (奈良シカマル)")
        self.root.geometry("600x700")
        self.root.configure(bg="#0d0d0d")
        self.root.resizable(False, False)
        
        # Initialize API and Link Extractor
        self.guerrilla = GuerrillaMailAPI()
        self.link_extractor = LinkExtractor()
        
        # State variables
        self.is_running = False
        self.monitor_thread = None
        self.current_email = None
        self.found_codes = set()
        self.found_links = set()
        
        # Theme colors
        self.themes = {
            "cyan": {
                "bg": "#0d0d0d",
                "fg": "#00ff9f",
                "accent": "#00d4ff",
                "secondary": "#1a1a2e",
                "highlight": "#00ff9f"
            },
            "purple": {
                "bg": "#0d0d0d",
                "fg": "#ff00ff",
                "accent": "#9d00ff",
                "secondary": "#1a0a2e",
                "highlight": "#ff00ff"
            }
        }
        self.current_theme = "cyan"
        self.colors = self.themes[self.current_theme]
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the cyberpunk-themed UI"""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="◄ MAIL CODE & LINK EXTRACTOR ►",
            font=("Courier New", 14, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["accent"]
        )
        title_label.pack(pady=(0, 20))
        
        # RUN/STOP Toggle Switch
        self.toggle_var = tk.BooleanVar(value=False)
        toggle_frame = tk.Frame(main_frame, bg=self.colors["bg"])
        toggle_frame.pack(pady=10)
        
        self.toggle_canvas = tk.Canvas(
            toggle_frame, 
            width=100, 
            height=40, 
            bg=self.colors["secondary"],
            highlightthickness=2,
            highlightbackground=self.colors["fg"]
        )
        self.toggle_canvas.pack()
        
        self.toggle_canvas.create_oval(5, 5, 35, 35, fill="#333", tags="switch")
        self.toggle_text = self.toggle_canvas.create_text(
            50, 20, 
            text="RUN", 
            fill=self.colors["fg"],
            font=("Courier New", 12, "bold")
        )
        
        self.toggle_canvas.bind("<Button-1>", self.toggle_switch)
        
        # Email Address Section
        email_frame = tk.LabelFrame(
            main_frame,
            text=" EMAIL ADDRESS ",
            font=("Courier New", 10, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["accent"],
            padx=10,
            pady=10
        )
        email_frame.pack(fill=tk.X, pady=10)
        
        self.email_entry = tk.Entry(
            email_frame,
            font=("Consolas", 12),
            bg=self.colors["secondary"],
            fg=self.colors["fg"],
            insertbackground=self.colors["fg"],
            relief=tk.FLAT,
            justify=tk.CENTER
        )
        self.email_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.email_entry.insert(0, "Click RUN to generate email")
        self.email_entry.config(state=tk.DISABLED)
        
        # Copy button
        self.copy_btn = tk.Button(
            email_frame,
            text="📋",
            font=("Segoe UI", 12),
            bg=self.colors["secondary"],
            fg=self.colors["fg"],
            relief=tk.FLAT,
            command=self.copy_email,
            cursor="hand2"
        )
        self.copy_btn.pack(side=tk.RIGHT)
        
        # Verification Code Section
        code_frame = tk.LabelFrame(
            main_frame,
            text=" VERIFICATION CODE ",
            font=("Courier New", 10, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["accent"],
            padx=10,
            pady=10
        )
        code_frame.pack(fill=tk.X, pady=10)
        
        self.code_display = tk.Text(
            code_frame,
            height=3,
            font=("Consolas", 24, "bold"),
            bg=self.colors["secondary"],
            fg=self.colors["highlight"],
            relief=tk.FLAT,
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        self.code_display.pack(fill=tk.X)
        self.code_display.insert(tk.END, "----")
        self.code_display.config(state=tk.DISABLED)
        
        # Copy code button
        self.copy_code_btn = tk.Button(
            code_frame,
            text="COPY CODE",
            font=("Courier New", 9, "bold"),
            bg=self.colors["secondary"],
            fg=self.colors["fg"],
            relief=tk.FLAT,
            command=self.copy_code,
            cursor="hand2"
        )
        self.copy_code_btn.pack(pady=(5, 0))
        
        # Verification Links Section (NEW)
        links_frame = tk.LabelFrame(
            main_frame,
            text=" VERIFICATION LINKS ",
            font=("Courier New", 10, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["accent"],
            padx=10,
            pady=10
        )
        links_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Links display area with scrollbar
        links_scroll = tk.Scrollbar(links_frame)
        links_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.links_text = tk.Text(
            links_frame,
            height=6,
            font=("Consolas", 9),
            bg=self.colors["secondary"],
            fg=self.colors["fg"],
            relief=tk.FLAT,
            wrap=tk.WORD,
            yscrollcommand=links_scroll.set,
            padx=5,
            pady=5
        )
        self.links_text.pack(fill=tk.BOTH, expand=True)
        self.links_text.config(state=tk.DISABLED)
        links_scroll.config(command=self.links_text.yview)
        
        # Link buttons frame
        self.links_buttons_frame = tk.Frame(links_frame, bg=self.colors["bg"])
        self.links_buttons_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Open All Links button
        self.open_links_btn = tk.Button(
            self.links_buttons_frame,
            text="OPEN ALL LINKS",
            font=("Courier New", 9, "bold"),
            bg=self.colors["secondary"],
            fg=self.colors["fg"],
            relief=tk.FLAT,
            command=self.open_all_links,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.open_links_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Clear Links button
        self.clear_links_btn = tk.Button(
            self.links_buttons_frame,
            text="CLEAR",
            font=("Courier New", 9, "bold"),
            bg=self.colors["secondary"],
            fg=self.colors["fg"],
            relief=tk.FLAT,
            command=self.clear_links,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.clear_links_btn.pack(side=tk.LEFT)
        
        # Store current links
        self.current_links = []
        
        # Theme Switcher
        theme_frame = tk.Frame(main_frame, bg=self.colors["bg"])
        theme_frame.pack(fill=tk.X, pady=5)
        
        self.theme_btn = tk.Button(
            theme_frame,
            text="SWITCH THEME",
            font=("Courier New", 8),
            bg=self.colors["secondary"],
            fg=self.colors["fg"],
            relief=tk.FLAT,
            command=self.switch_theme,
            cursor="hand2"
        )
        self.theme_btn.pack(side=tk.RIGHT)
        
        # Log Console
        log_frame = tk.LabelFrame(
            main_frame,
            text=" SYSTEM LOG ",
            font=("Courier New", 10, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["accent"],
            padx=10,
            pady=10
        )
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        log_scroll = tk.Scrollbar(log_frame)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(
            log_frame,
            height=8,
            font=("Consolas", 9),
            bg=self.colors["secondary"],
            fg=self.colors["fg"],
            relief=tk.FLAT,
            state=tk.DISABLED,
            yscrollcommand=log_scroll.set,
            padx=5,
            pady=5
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        log_scroll.config(command=self.log_text.yview)
        
        # Status bar
        self.status_label = tk.Label(
            main_frame,
            text="■ STOPPED",
            font=("Courier New", 10, "bold"),
            bg=self.colors["bg"],
            fg="#ff4444"
        )
        self.status_label.pack(pady=(10, 0))
        
    def toggle_switch(self, event=None):
        """Handle RUN/STOP toggle"""
        if not self.is_running:
            self.start_monitoring()
        else:
            self.stop_monitoring()
    
    def start_monitoring(self):
        """Start email monitoring"""
        self.is_running = True
        self.toggle_var.set(True)
        
        # Update toggle UI
        self.toggle_canvas.delete("switch")
        self.toggle_canvas.create_oval(65, 5, 95, 35, fill=self.colors["highlight"], tags="switch")
        self.toggle_canvas.itemconfig(self.toggle_text, text="STOP")
        self.toggle_canvas.config(highlightbackground="#ff4444")
        
        self.status_label.config(text="■ RUNNING", fg=self.colors["highlight"])
        self.log("System initialized...")
        self.log("Generating temporary email address...")
        
        # Clear previous data
        self.found_codes.clear()
        self.found_links.clear()
        self.current_links = []
        self.clear_links_display()
        
        # Generate email in separate thread
        thread = threading.Thread(target=self.generate_and_monitor)
        thread.daemon = True
        thread.start()
    
    def stop_monitoring(self):
        """Stop email monitoring"""
        self.is_running = False
        self.toggle_var.set(False)
        
        # Update toggle UI
        self.toggle_canvas.delete("switch")
        self.toggle_canvas.create_oval(5, 5, 35, 35, fill="#333", tags="switch")
        self.toggle_canvas.itemconfig(self.toggle_text, text="RUN")
        self.toggle_canvas.config(highlightbackground=self.colors["fg"])
        
        self.status_label.config(text="■ STOPPED", fg="#ff4444")
        self.log("Monitoring stopped.")
        
        # Reset email display
        self.email_entry.config(state=tk.NORMAL)
        self.email_entry.delete(0, tk.END)
        self.email_entry.insert(0, "Click RUN to generate email")
        self.email_entry.config(state=tk.DISABLED)
        self.current_email = None
    
    def generate_and_monitor(self):
        """Generate email and start monitoring"""
        # Generate new email
        email = self.guerrilla.generate_email()
        
        if email:
            self.current_email = email
            self.root.after(0, self.update_email_display, email)
            self.log(f"Email generated: {email}")
            self.log("Waiting for incoming messages...")
            
            # Start monitoring loop
            self.monitor_emails()
        else:
            self.log("ERROR: Failed to generate email")
            self.root.after(0, self.stop_monitoring)
    
    def update_email_display(self, email):
        """Update email entry with generated email"""
        self.email_entry.config(state=tk.NORMAL)
        self.email_entry.delete(0, tk.END)
        self.email_entry.insert(0, email)
        self.email_entry.config(state=tk.DISABLED)
    
    def monitor_emails(self):
        """Monitor inbox for new emails"""
        checked_ids = set()
        
        while self.is_running:
            try:
                emails = self.guerrilla.check_inbox()
                
                for email in emails:
                    email_id = email.get('mail_id')
                    
                    if email_id not in checked_ids:
                        checked_ids.add(email_id)
                        
                        # Fetch full email content
                        full_email = self.guerrilla.fetch_email(email_id)
                        
                        subject = full_email.get('mail_subject', '')
                        body = full_email.get('mail_body', '')
                        sender = full_email.get('mail_from', '')
                        
                        self.log(f"New email from: {sender}")
                        self.log(f"Subject: {subject}")
                        
                        # Combine subject and body for extraction
                        full_text = f"{subject} {body}"
                        
                        # Extract verification code
                        code = self.extract_verification_code(full_text)
                        if code and code not in self.found_codes:
                            self.found_codes.add(code)
                            self.root.after(0, self.display_code, code)
                            self.log(f"✓ Verification code found: {code}")
                        
                        # Extract verification links (NEW)
                        links = self.link_extractor.extract_links(full_text)
                        new_links = [link for link in links if link not in self.found_links]
                        
                        if new_links:
                            for link in new_links:
                                self.found_links.add(link)
                                self.current_links.append(link)
                                self.log(f"✓ Verification link found: {link[:60]}...")
                            
                            self.root.after(0, self.display_links, new_links)
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.log(f"Error: {str(e)}")
                time.sleep(5)
    
    def extract_verification_code(self, text):
        """Extract 4-6 digit verification code from text"""
        if not text:
            return None
            
        # Patterns for verification codes
        patterns = [
            r'\b(\d{4,6})\b(?![\d])',  # 4-6 digit numbers
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
                # Validate code (not a year, not part of phone number context)
                if 1000 <= int(code) <= 999999:
                    return code
        
        return None
    
    def display_code(self, code):
        """Display extracted code"""
        self.code_display.config(state=tk.NORMAL)
        self.code_display.delete(1.0, tk.END)
        self.code_display.insert(tk.END, code)
        self.code_display.config(state=tk.DISABLED)
    
    def display_links(self, links):
        """Display extracted verification links"""
        self.links_text.config(state=tk.NORMAL)
        
        for link in links:
            # Truncate long links for display
            display_link = link if len(link) < 70 else link[:67] + "..."
            self.links_text.insert(tk.END, f"► {display_link}\n\n")
        
        self.links_text.see(tk.END)
        self.links_text.config(state=tk.DISABLED)
        
        # Enable link buttons
        self.open_links_btn.config(state=tk.NORMAL)
        self.clear_links_btn.config(state=tk.NORMAL)
        
        # Create individual open buttons for each link
        for i, link in enumerate(links):
            btn = tk.Button(
                self.links_buttons_frame,
                text=f"LINK {len(self.current_links) - len(links) + i + 1}",
                font=("Courier New", 8),
                bg=self.colors["accent"],
                fg=self.colors["bg"],
                relief=tk.FLAT,
                command=lambda l=link: self.open_single_link(l),
                cursor="hand2"
            )
            btn.pack(side=tk.LEFT, padx=(0, 3))
    
    def open_single_link(self, link):
        """Open a single verification link"""
        self.log(f"Opening link: {link[:50]}...")
        success = self.link_extractor.open_link(link)
        if success:
            self.log("✓ Link opened in browser")
        else:
            self.log("✗ Failed to open link")
    
    def open_all_links(self):
        """Open all found verification links"""
        if not self.current_links:
            return
            
        self.log(f"Opening {len(self.current_links)} link(s)...")
        for link in self.current_links:
            self.link_extractor.open_link(link)
            time.sleep(0.5)  # Small delay between opening
        
        self.log("✓ All links opened in browser")
    
    def clear_links(self):
        """Clear all links from display"""
        self.current_links = []
        self.found_links.clear()
        self.clear_links_display()
        self.log("Links cleared")
    
    def clear_links_display(self):
        """Clear links display area"""
        self.links_text.config(state=tk.NORMAL)
        self.links_text.delete(1.0, tk.END)
        self.links_text.config(state=tk.DISABLED)
        
        # Remove individual link buttons
        for widget in self.links_buttons_frame.winfo_children():
            if isinstance(widget, tk.Button) and widget != self.open_links_btn and widget != self.clear_links_btn:
                widget.destroy()
        
        self.open_links_btn.config(state=tk.DISABLED)
        self.clear_links_btn.config(state=tk.DISABLED)
    
    def copy_email(self):
        """Copy email to clipboard"""
        if self.current_email:
            pyperclip.copy(self.current_email)
            self.log("Email copied to clipboard")
    
    def copy_code(self):
        """Copy code to clipboard"""
        self.code_display.config(state=tk.NORMAL)
        code = self.code_display.get(1.0, tk.END).strip()
        self.code_display.config(state=tk.DISABLED)
        
        if code and code != "----":
            pyperclip.copy(code)
            self.log("Code copied to clipboard")
    
    def log(self, message):
        """Add message to log"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def switch_theme(self):
        """Switch between cyan and purple themes"""
        if self.current_theme == "cyan":
            self.current_theme = "purple"
        else:
            self.current_theme = "cyan"
        
        self.colors = self.themes[self.current_theme]
        self.apply_theme()
        self.log(f"Theme switched to {self.current_theme}")
    
    def apply_theme(self):
        """Apply current theme to all widgets"""
        # This is a simplified theme application
        # In a full implementation, you'd update all widget colors
        self.root.configure(bg=self.colors["bg"])

def main():
    root = tk.Tk()
    app = GuerrillaMailApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()