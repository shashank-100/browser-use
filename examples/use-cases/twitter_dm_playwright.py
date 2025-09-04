#!/usr/bin/env python3
"""
Twitter DM Automation Script using Playwright
Sends personalized DMs to users from a CSV file

@file purpose: Direct Playwright automation for Twitter DM sending
"""

import asyncio
import csv
import os
from playwright.async_api import async_playwright
from typing import List, Tuple
import time

# Configuration
CSV_FILE = "/Users/shashank/Documents/GitHub/browser-use/cleaned_x_profiles.csv"
MESSAGE_TEMPLATE = """Hey {name},

I'm Shashank — I help founders turn ideas into successful MVPs that get traction fast.
At Leanstart, we only take on 5 clients per month so we can stay hands-on and focused.

If you're serious about building your MVP, let's hop on a quick free call (no strings attached) to discuss how we can help.

📂 Portfolio: leanstart.agency

📅 Book a call: https://cal.com/shashank-t-zcyxsj/15min"""

# XPath selectors
MESSAGE_BUTTON_XPATH = '//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div[1]/div/div[3]/div/div/div[1]/div/div[1]/div[2]/button[2]'
MESSAGE_INPUT_XPATH = '//*[@id="react-root"]/div/div/div[2]/main/div/div/div/section[2]/div/div/div[2]/div[1]/div/aside/div[2]/div[2]/div/div/div/div/div/div/div[1]/div/div/div/div/div/div[2]'
SEND_BUTTON_SELECTOR = 'div[data-testid="tweetButtonInline"]'

def read_users_from_csv(csv_file_path: str) -> List[Tuple[str, str, str]]:
    """Read users from CSV file and return list of (profile_url, username, name) tuples"""
    users = []
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                profile_url = row.get('profile_link', '')
                if not profile_url:
                    continue
                username = profile_url.split('/')[-1] if '/' in profile_url else profile_url.replace('@', '')
                name = row.get('first_name', username)
                if profile_url and username and name:
                    users.append((profile_url, username, name))
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return []
    return users

async def send_dm_to_user(page, profile_url: str, username: str, name: str) -> bool:
    """Send DM to a specific user"""
    try:
        print(f"📱 Navigating to @{username} profile...")
        
        # Navigate to user's profile
        await page.goto(profile_url, timeout=10000)
        await page.wait_for_timeout(2000)
        
        # Look for message button
        print(f"🔍 Looking for message button...")
        message_button = page.locator(MESSAGE_BUTTON_XPATH)
        
        if await message_button.is_visible():
            print(f"✅ Found message button for @{username}")
            await message_button.click()
            await page.wait_for_timeout(2000)
            
            # Look for message input field - try multiple selectors
            print(f"🔍 Looking for message input field...")
            message_input = None
            
            # Try different selectors for the message input
            selectors = [
                'div[data-testid="tweetTextarea_0"]',
                'div[contenteditable="true"]',
                'div[role="textbox"]',
                'div[aria-label="Tweet text"]',
                MESSAGE_INPUT_XPATH
            ]
            
            for selector in selectors:
                try:
                    message_input = page.locator(selector)
                    if await message_input.is_visible():
                        print(f"✅ Found message input field with selector: {selector}")
                        break
                except:
                    continue
            
            if message_input and await message_input.is_visible():
                # Type the personalized message
                personalized_message = MESSAGE_TEMPLATE.format(name=name)
                await message_input.click()
                await message_input.fill(personalized_message)
                print(f"⏳ Waiting 10 seconds after typing message...")
                await page.wait_for_timeout(10000)
                
                # Send the message
                print(f"📤 Sending message to @{username}...")
                
                # Try different send button selectors
                send_selectors = [
                    '//*[@id="react-root"]/div/div/div[2]/main/div/div/div/section[2]/div/div/div[2]/div[1]/div/aside/div[2]/button',
                    'div[data-testid="tweetButtonInline"]',
                    'button[data-testid="tweetButtonInline"]',
                    'div[data-testid="tweetButton"]',
                    'button[data-testid="tweetButton"]',
                    'button[type="button"]:has-text("Send")',
                    'button:has-text("Send")',
                    SEND_BUTTON_SELECTOR
                ]
                
                sent = False
                for selector in send_selectors:
                    try:
                        send_button = page.locator(selector)
                        if await send_button.is_visible():
                            await send_button.click()
                            print(f"✅ Clicked send button with selector: {selector}")
                            sent = True
                            break
                    except:
                        continue
                
                if not sent:
                    print(f"❌ Could not find send button for @{username}")
                    return False
                
                await page.wait_for_timeout(3000)
                
                print(f"✅ Successfully sent DM to @{username}")
                return True
            else:
                print(f"❌ Message input field not found for @{username}")
                return False
        else:
            print(f"❌ Message button not found for @{username} - skipping")
            return False
            
    except Exception as e:
        print(f"❌ Error sending DM to @{username}: {str(e)}")
        return False

async def main():
    """Main function to run the DM automation"""
    print("🚀 Starting Twitter DM Automation with Playwright")
    
    # Read users from CSV
    users = read_users_from_csv(CSV_FILE)
    if not users:
        print("❌ No users found in CSV file")
        return
    
    print(f"📊 Found {len(users)} users to message")
    
    # Connect to existing Chrome debug session
    async with async_playwright() as p:
        try:
            # Connect to existing Chrome session with remote debugging
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            pages = browser.contexts[0].pages
            page = pages[0] if pages else await browser.new_page()
            
            print("✅ Connected to existing Chrome session")
            
            # Navigate to Twitter home first
            print("🌐 Navigating to Twitter...")
            await page.goto("https://x.com/home", timeout=60000)
            await page.wait_for_timeout(5000)
            
            # Check if we're logged in
            if "login" in page.url.lower():
                print("❌ Not logged in to Twitter. Please log in manually and run the script again.")
                return
            
            print("✅ Successfully logged in to Twitter")
            
        except Exception as e:
            print(f"❌ Failed to connect to Chrome session: {e}")
            print("💡 Make sure Chrome is running with: --remote-debugging-port=9222")
            return
        
        # Send DMs to each user
        successful_messages = 0
        failed_messages = 0
        
        for i, (profile_url, username, name) in enumerate(users, 1):
            print(f"\n📝 Processing {i}/{len(users)}: @{username} ({name})")
            
            success = await send_dm_to_user(page, profile_url, username, name)
            
            if success:
                successful_messages += 1
            else:
                failed_messages += 1
            
            # Rate limiting - wait 2-3 seconds between messages
            if i < len(users):  # Don't wait after the last message
                print("⏳ Waiting 2-3 seconds before next message...")
                await page.wait_for_timeout(3000)
        
        # Final summary
        print(f"\n🎉 DM Automation Complete!")
        print(f"✅ Successfully sent: {successful_messages} messages")
        print(f"❌ Failed: {failed_messages} messages")
        print(f"📊 Total processed: {len(users)} users")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
