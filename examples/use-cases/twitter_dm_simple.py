#!/usr/bin/env python3
"""
Simple Twitter DM Script - Connect to Your Existing Chrome Session
"""

import asyncio
import csv
import random
from playwright.async_api import async_playwright

# Your CSV file
CSV_FILE = "/Users/shashank/Documents/GitHub/browser-use/Untitled spreadsheet - https___x.com_Anubhavhing_verif.csv"

# Your message template
MESSAGE_TEMPLATE = """Hey {name},

I'm Shashank — I help founders turn ideas into successful MVPs that get traction fast.
At Leanstart, we only take on 5 clients per month so we can stay hands-on and focused.

If you're serious about building your MVP, let's hop on a quick free call (no strings attached) to discuss how we can help.

📂 Portfolio: leanstart.agency

📅 Book a call: https://cal.com/shashank-t-zcyxsj/15min"""

def read_users_from_csv():
    """Read users from CSV file"""
    users = []
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                profile_url = row.get('Profile', '')
                name = row.get('Name', '')
                if profile_url and name:
                    users.append((profile_url, name))
    except Exception as e:
        print(f"Error reading CSV: {e}")
    return users

async def send_dm(page, profile_url, name):
    """Send DM to a user"""
    try:
        print(f"📱 Going to {profile_url}")
        await page.goto(profile_url)
        await page.wait_for_timeout(3000)
        
        # Look for message button
        message_button = page.locator('//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div[1]/div/div[3]/div/div/div[1]/div/div[1]/div[2]/button[2]')
        
        if await message_button.is_visible():
            print(f"✅ Found message button for {name}")
            await message_button.click()
            await page.wait_for_timeout(2000)  # Wait 2 seconds after clicking message button
            
            # Try multiple selectors for the message input
            message_input = None
            selectors = [
                'div[data-testid="tweetTextarea_0"]',
                'div[contenteditable="true"]',
                'div.DraftEditor-editorContainer div[contenteditable="true"]',
                'div[role="textbox"]'
            ]
            
            for selector in selectors:
                try:
                    message_input = page.locator(selector).first
                    if await message_input.is_visible():
                        print(f"✅ Found message input with selector: {selector}")
                        break
                except:
                    continue
            
            if message_input and await message_input.is_visible():
                await message_input.click()
                await page.wait_for_timeout(1000)
                await message_input.fill(MESSAGE_TEMPLATE.format(name=name))
                await page.wait_for_timeout(1000)
            else:
                print(f"❌ Could not find message input field for {name}")
                return False
            
            # Send - use the correct XPath you provided
            send_button = page.locator('//*[@id="react-root"]/div/div/div[2]/main/div/div/div/section[2]/div/div/div[2]/div[1]/div/aside/div[2]/button')
            
            if await send_button.is_visible():
                print(f"✅ Found send button for {name}")
                await send_button.click()
                await page.wait_for_timeout(3000)
                print(f"✅ Message sent to {name}")
            else:
                print(f"❌ Could not find send button for {name}")
                return False
            
            print(f"✅ Sent DM to {name}")
            return True
        else:
            print(f"❌ No message button for {name}")
            return False
            
    except Exception as e:
        print(f"❌ Error with {name}: {e}")
        return False

async def main():
    print("🚀 Twitter DM Script - Using Your Existing Chrome Session")
    
    # Read users
    users = read_users_from_csv()
    print(f"📊 Found {len(users)} users")
    
    # Connect to your existing Chrome
    async with async_playwright() as p:
        try:
            print("🔗 Connecting to your Chrome...")
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("✅ Connected!")
            
            # Get existing page or create new one
            contexts = browser.contexts
            if contexts and contexts[0].pages:
                page = contexts[0].pages[0]
            else:
                page = await browser.new_page()
            
            # Go to Twitter
            await page.goto("https://x.com/home")
            await page.wait_for_timeout(2000)
            
            # Send DMs
            success_count = 0
            for i, (profile_url, name) in enumerate(users, 1):
                print(f"\n📝 {i}/{len(users)}: {name}")
                
                if await send_dm(page, profile_url, name):
                    success_count += 1
                
                # Wait between messages (random 2-5 seconds)
                if i < len(users):
                    wait_time = random.randint(2000, 5000)
                    print(f"⏳ Waiting {wait_time/1000:.1f} seconds...")
                    await page.wait_for_timeout(wait_time)
            
            print(f"\n🎉 Done! Sent {success_count}/{len(users)} messages")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print("💡 Make sure Chrome is running with: --remote-debugging-port=9222")

if __name__ == "__main__":
    asyncio.run(main())
