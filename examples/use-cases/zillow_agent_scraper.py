#!/usr/bin/env python3
"""
Zillow Real Estate Agent Scraper using Playwright
Scrapes agent listings and individual agent profile data

@file purpose: Direct Playwright automation for Zillow agent data extraction
"""

import asyncio
from playwright.async_api import async_playwright
import csv
import argparse
from dataclasses import dataclass, asdict
from typing import List
import random

@dataclass
class AgentInfo:
	name: str
	profile_url: str
	email: str = ""  # Priority #1
	phone: str = ""  # Priority #2
	office: str = ""
	office_phone: str = ""
	rating: str = ""
	review_count: str = ""
	sales_count: str = ""
	recent_sales: str = ""
	years_experience: str = ""
	specialties: str = ""
	areas_served: str = ""
	languages: str = ""
	bio: str = ""
	license: str = ""
	brokerage: str = ""
	website: str = ""
	location: str = ""
	zillow_profile_views: str = ""

def save_agents_to_csv(agents: List[AgentInfo], filename: str = "zillow_agents.csv"):
	"""Save agent information to CSV file"""
	try:
		with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
			fieldnames = list(asdict(agents[0]).keys())
			writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

			writer.writeheader()
			for agent in agents:
				writer.writerow(asdict(agent))

		print(f"✅ Saved {len(agents)} agents to {filename}")
		return True

	except Exception as e:
		print(f"❌ Error saving to CSV: {e}")
		return False

async def extract_agent_from_card(page, card_element) -> AgentInfo | None:
	"""Extract basic agent info from a listing card"""
	try:
		# Extract name
		name = ""
		name_selectors = [
			'[data-test="agent-name"]',
			'h2 a',
			'h3 a',
			'.Text-c11n-8-105-2__sc-aiai24-0',
			'a[href*="/profile/"]'
		]
		for selector in name_selectors:
			try:
				name_elem = card_element.locator(selector).first
				if await name_elem.count() > 0:
					name = await name_elem.text_content()
					name = name.strip() if name else ""
					if name:
						break
			except:
				continue

		# Extract profile URL
		profile_url = ""
		url_selectors = [
			'a[href*="/profile/"]',
			'a[data-test="agent-name"]',
			'h2 a',
			'h3 a'
		]
		for selector in url_selectors:
			try:
				url_elem = card_element.locator(selector).first
				if await url_elem.count() > 0:
					href = await url_elem.get_attribute('href')
					if href:
						if not href.startswith('http'):
							profile_url = f"https://www.zillow.com{href}"
						else:
							profile_url = href
						break
			except:
				continue

		# Extract rating
		rating = ""
		rating_selectors = [
			'[data-test="rating"]',
			'[aria-label*="rating"]',
			'.rating',
			'span[aria-label*="star"]'
		]
		for selector in rating_selectors:
			try:
				rating_elem = card_element.locator(selector).first
				if await rating_elem.count() > 0:
					rating_text = await rating_elem.text_content()
					rating = rating_text.strip() if rating_text else ""
					if rating:
						break
			except:
				continue

		# Extract review count
		review_count = ""
		review_selectors = [
			'[data-test="review-count"]',
			'text=/\\d+ review/i',
			'span:has-text("review")'
		]
		for selector in review_selectors:
			try:
				review_elem = card_element.locator(selector).first
				if await review_elem.count() > 0:
					review_text = await review_elem.text_content()
					review_count = review_text.strip() if review_text else ""
					if review_count:
						break
			except:
				continue

		# Extract phone
		phone = ""
		phone_selectors = [
			'[data-test="agent-phone"]',
			'a[href^="tel:"]',
			'text=/\\(\\d{3}\\) \\d{3}-\\d{4}/'
		]
		for selector in phone_selectors:
			try:
				phone_elem = card_element.locator(selector).first
				if await phone_elem.count() > 0:
					phone_text = await phone_elem.text_content()
					if not phone_text:
						phone_text = await phone_elem.get_attribute('href')
						if phone_text and phone_text.startswith('tel:'):
							phone_text = phone_text.replace('tel:', '')
					phone = phone_text.strip() if phone_text else ""
					if phone:
						break
			except:
				continue

		if name and profile_url:
			return AgentInfo(
				name=name,
				profile_url=profile_url,
				phone=phone,
				rating=rating,
				review_count=review_count
			)

		return None

	except Exception as e:
		print(f"❌ Error extracting agent from card: {e}")
		return None

async def scrape_agent_profile(page, agent: AgentInfo) -> AgentInfo:
	"""Visit agent profile and extract detailed information"""
	try:
		print(f"  🔍 Visiting profile: {agent.name}")

		await page.goto(agent.profile_url, timeout=15000)
		await page.wait_for_timeout(3000)

		# Try to click "Show phone" or "Call" buttons first
		show_phone_selectors = [
			'button:has-text("Show phone")',
			'button:has-text("Call")',
			'button[aria-label*="phone"]',
			'button[aria-label*="Call"]',
			'a:has-text("Show phone")',
			'span:has-text("Show phone")'
		]
		for selector in show_phone_selectors:
			try:
				show_button = page.locator(selector).first
				if await show_button.count() > 0 and await show_button.is_visible():
					print(f"  📞 Clicking show phone button...")
					await show_button.click()
					await page.wait_for_timeout(1500)
					break
			except Exception as e:
				continue

		# Extract phone - search for tel: links first (most reliable)
		# We'll collect multiple phone numbers and try to identify personal vs office
		phone_numbers = []
		if not agent.phone:
			try:
				all_tel_links = await page.locator('a[href^="tel:"]').all()
				for link in all_tel_links:
					href = await link.get_attribute('href')
					if href:
						phone_text = href.replace('tel:', '').replace('+1', '').replace('-', '').replace('.', '').replace('(', '').replace(')', '').replace(' ', '')
						# Reformat to (XXX) XXX-XXXX
						if len(phone_text) >= 10:
							formatted = f"({phone_text[:3]}) {phone_text[3:6]}-{phone_text[6:10]}"
							phone_numbers.append(formatted)

				# Set first phone as main phone, second as office phone (if exists)
				if len(phone_numbers) > 0:
					agent.phone = phone_numbers[0]
					print(f"  ✅ Found phone: {agent.phone}")
				if len(phone_numbers) > 1:
					agent.office_phone = phone_numbers[1]
					print(f"  ✅ Found office phone: {agent.office_phone}")
			except:
				pass

		# If no phone found, try other selectors
		if not agent.phone:
			phone_selectors = [
				'[data-test="agent-phone"]',
				'button[aria-label*="Call"]',
				'text=/\\(\\d{3}\\) \\d{3}-\\d{4}/',
				'text=/\\d{3}-\\d{3}-\\d{4}/',
				'text=/\\d{3}\\.\\d{3}\\.\\d{4}/',
				'[class*="phone"]',
				'[id*="phone"]',
				'span:has-text("Phone")',
				'div:has-text("Phone")'
			]
			for selector in phone_selectors:
				try:
					phone_elem = page.locator(selector).first
					if await phone_elem.count() > 0:
						phone_text = await phone_elem.text_content()
						if not phone_text:
							phone_text = await phone_elem.get_attribute('href')
							if phone_text and phone_text.startswith('tel:'):
								phone_text = phone_text.replace('tel:', '').replace('-', '').replace('.', '').replace('(', '').replace(')', '').replace(' ', '')
								# Reformat to (XXX) XXX-XXXX
								if len(phone_text) == 10:
									phone_text = f"({phone_text[:3]}) {phone_text[3:6]}-{phone_text[6:]}"

						# Clean up phone number
						if phone_text:
							phone_text = phone_text.strip()
							# Check if it looks like a valid phone number
							import re
							if re.search(r'\d{3}.*\d{3}.*\d{4}', phone_text):
								agent.phone = phone_text
								print(f"  ✅ Found phone: {agent.phone}")
								break
				except Exception as e:
					continue

		# Try to click "Contact" or "Email" buttons
		show_email_selectors = [
			'button:has-text("Contact")',
			'button:has-text("Email")',
			'a:has-text("Contact")',
			'a:has-text("Email")',
			'button[aria-label*="Email"]',
			'button[aria-label*="Contact"]'
		]
		for selector in show_email_selectors:
			try:
				show_button = page.locator(selector).first
				if await show_button.count() > 0 and await show_button.is_visible():
					print(f"  📧 Clicking contact/email button...")
					await show_button.click()
					await page.wait_for_timeout(1500)
					break
			except:
				continue

		# Extract email - search for mailto links first (most reliable)
		try:
			all_mailto_links = await page.locator('a[href^="mailto:"]').all()
			for link in all_mailto_links:
				href = await link.get_attribute('href')
				if href:
					agent.email = href.replace('mailto:', '').strip().split('?')[0]
					print(f"  ✅ Found email: {agent.email}")
					break
		except:
			pass

		# If no email found, try other selectors
		if not agent.email:
			email_selectors = [
				'[data-test="agent-email"]',
				'text=/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}/',
				'[class*="email"]',
				'[id*="email"]',
				'span:has-text("Email")',
				'div:has-text("Email")'
			]
			for selector in email_selectors:
				try:
					email_elem = page.locator(selector).first
					if await email_elem.count() > 0:
						email_text = await email_elem.get_attribute('href')
						if email_text and email_text.startswith('mailto:'):
							agent.email = email_text.replace('mailto:', '').strip().split('?')[0]  # Remove query params
							print(f"  ✅ Found email: {agent.email}")
							break
						else:
							email_text = await email_elem.text_content()
							if email_text:
								# Extract email from text using regex
								import re
								email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', email_text)
								if email_match:
									agent.email = email_match.group(0).strip()
									print(f"  ✅ Found email: {agent.email}")
									break
				except:
					continue

		# If still no email, check page source for any mailto links or email patterns
		if not agent.email:
			try:
				page_content = await page.content()
				import re
				# Find mailto links
				mailto_match = re.search(r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', page_content)
				if mailto_match:
					agent.email = mailto_match.group(1).strip()
					print(f"  ✅ Found email in source: {agent.email}")
			except:
				pass

		# Extract sales count and recent sales
		sales_selectors = [
			'[data-test="sales-count"]',
			'text=/\\d+\\s+sale/i',
			'text=/\\d+\\s+transaction/i',
			'span:has-text("sale")',
			'text=/sold \\d+/i',
			'text=/\\d+\\s+closed/i'
		]
		for selector in sales_selectors:
			try:
				sales_elem = page.locator(selector).first
				if await sales_elem.count() > 0:
					sales_text = await sales_elem.text_content()
					sales_text = sales_text.strip() if sales_text else ""
					if sales_text:
						# Check if it mentions "recent" or "last year" or "in 2024"
						if "recent" in sales_text.lower() or "last" in sales_text.lower() or "2024" in sales_text or "2025" in sales_text:
							agent.recent_sales = sales_text
						else:
							agent.sales_count = sales_text
						break
			except:
				continue

		# Extract profile views
		views_selectors = [
			'text=/\\d+\\s+profile views?/i',
			'text=/viewed.*\\d+\\s+times?/i',
			'[data-test="profile-views"]'
		]
		for selector in views_selectors:
			try:
				views_elem = page.locator(selector).first
				if await views_elem.count() > 0:
					views_text = await views_elem.text_content()
					agent.zillow_profile_views = views_text.strip() if views_text else ""
					if agent.zillow_profile_views:
						break
			except:
				continue

		# Extract bio
		bio_selectors = [
			'[data-test="agent-bio"]',
			'[data-test="agent-description"]',
			'.agent-bio',
			'p[class*="bio"]',
			'div[class*="description"]'
		]
		for selector in bio_selectors:
			try:
				bio_elem = page.locator(selector).first
				if await bio_elem.count() > 0:
					bio_text = await bio_elem.text_content()
					agent.bio = bio_text.strip().replace('\n', ' ').replace('\r', ' ') if bio_text else ""
					if agent.bio:
						break
			except:
				continue

		# Extract specialties
		specialty_selectors = [
			'[data-test="agent-specialties"]',
			'[data-test="specialties"]',
			'text=/Specialties:/i',
			'span:has-text("Specialties")'
		]
		for selector in specialty_selectors:
			try:
				specialty_elem = page.locator(selector).first
				if await specialty_elem.count() > 0:
					specialty_text = await specialty_elem.text_content()
					agent.specialties = specialty_text.strip() if specialty_text else ""
					if agent.specialties:
						break
			except:
				continue

		# Extract office/brokerage info
		office_selectors = [
			'[data-test="agent-office"]',
			'text=/Office:/i',
			'text=/Brokerage:/i',
			'span:has-text("Office")',
			'span:has-text("Brokerage")',
			'div:has-text("Works at")',
			'[class*="brokerage"]'
		]
		for selector in office_selectors:
			try:
				office_elem = page.locator(selector).first
				if await office_elem.count() > 0:
					office_text = await office_elem.text_content()
					if office_text:
						office_text = office_text.strip()
						# Try to separate brokerage from office
						if "Works at" in office_text or "Brokerage" in office_text:
							agent.brokerage = office_text.replace("Works at", "").replace("Brokerage:", "").strip()
						else:
							agent.office = office_text.replace("Office:", "").strip()
						break
			except:
				continue

		# Extract years of experience
		experience_selectors = [
			'text=/\\d+\\s+years?\\s+(of\\s+)?experience/i',
			'text=/Experience:\\s*\\d+/i',
			'[data-test="years-experience"]'
		]
		for selector in experience_selectors:
			try:
				exp_elem = page.locator(selector).first
				if await exp_elem.count() > 0:
					exp_text = await exp_elem.text_content()
					agent.years_experience = exp_text.strip() if exp_text else ""
					if agent.years_experience:
						break
			except:
				continue

		# Extract languages
		language_selectors = [
			'text=/Languages?:/i',
			'[data-test="languages"]',
			'span:has-text("Language")'
		]
		for selector in language_selectors:
			try:
				lang_elem = page.locator(selector).first
				if await lang_elem.count() > 0:
					lang_text = await lang_elem.text_content()
					agent.languages = lang_text.replace("Languages:", "").replace("Language:", "").strip() if lang_text else ""
					if agent.languages:
						break
			except:
				continue

		# Extract areas served
		areas_selectors = [
			'text=/Areas? served/i',
			'text=/Service areas?/i',
			'[data-test="service-areas"]'
		]
		for selector in areas_selectors:
			try:
				areas_elem = page.locator(selector).first
				if await areas_elem.count() > 0:
					areas_text = await areas_elem.text_content()
					agent.areas_served = areas_text.strip() if areas_text else ""
					if agent.areas_served:
						break
			except:
				continue

		# Extract license
		license_selectors = [
			'[data-test="agent-license"]',
			'text=/License/i',
			'text=/DRE #/i'
		]
		for selector in license_selectors:
			try:
				license_elem = page.locator(selector).first
				if await license_elem.count() > 0:
					license_text = await license_elem.text_content()
					agent.license = license_text.strip() if license_text else ""
					if agent.license:
						break
			except:
				continue

		# Extract website
		website_selectors = [
			'a[data-test="agent-website"]',
			'a[href*="http"]:has-text("Website")',
			'a[href*="http"]:has-text("Visit")'
		]
		for selector in website_selectors:
			try:
				website_elem = page.locator(selector).first
				if await website_elem.count() > 0:
					website_url = await website_elem.get_attribute('href')
					agent.website = website_url.strip() if website_url else ""
					if agent.website:
						break
			except:
				continue

		# Log what contact info we found
		contact_status = []
		if agent.phone:
			contact_status.append("phone")
		if agent.email:
			contact_status.append("email")

		if contact_status:
			print(f"  ✅ Profile scraped: {agent.name} ({', '.join(contact_status)})")
		else:
			print(f"  ⚠️  Profile scraped: {agent.name} (no contact info found)")

		return agent

	except Exception as e:
		print(f"  ❌ Error scraping profile for {agent.name}: {e}")
		return agent

async def scrape_agent_listing(page, location_url: str, max_agents: int = 50, scrape_profiles: bool = True) -> List[AgentInfo]:
	"""Scrape agents from a location listing page"""
	agents = []

	try:
		print(f"🌐 Going to {location_url}...")
		await page.goto(location_url, timeout=15000)
		await page.wait_for_timeout(3000)

		# Scroll to load more agents (Zillow uses lazy loading)
		print("📜 Scrolling to load agents...")
		for _ in range(5):  # Scroll a few times to load more
			await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
			await page.wait_for_timeout(2000)

		# Find all agent cards
		card_selectors = [
			'[data-test="agent-card"]',
			'article[data-test*="agent"]',
			'div[class*="agent-card"]',
			'li[data-test*="agent"]',
			'div[class*="AgentCard"]'
		]

		agent_cards = None
		for selector in card_selectors:
			try:
				cards = page.locator(selector)
				count = await cards.count()
				if count > 0:
					agent_cards = cards
					print(f"✅ Found {count} agent cards using selector: {selector}")
					break
			except:
				continue

		if not agent_cards:
			print("❌ Could not find any agent cards")
			return agents

		total_cards = await agent_cards.count()
		agents_to_process = min(max_agents, total_cards)

		print(f"📊 Processing {agents_to_process} agents...")

		for i in range(agents_to_process):
			try:
				print(f"👤 Processing agent {i+1}/{agents_to_process}")

				card = agent_cards.nth(i)
				agent_info = await extract_agent_from_card(page, card)

				if agent_info:
					if scrape_profiles:
						# Visit profile for detailed info
						agent_info = await scrape_agent_profile(page, agent_info)
						# Go back to listing page
						await page.goto(location_url, timeout=15000)
						await page.wait_for_timeout(2000)
						# Re-scroll to the same position
						for _ in range(i // 10):
							await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
							await page.wait_for_timeout(1000)

					agents.append(agent_info)
					print(f"✅ Extracted: {agent_info.name}")
				else:
					print(f"❌ Failed to extract agent {i+1}")

				# Small delay between agents
				await page.wait_for_timeout(random.randint(500, 1500))

			except Exception as agent_error:
				print(f"❌ Error processing agent {i+1}: {agent_error}")
				continue

		print(f"\n🎉 Successfully extracted {len(agents)} agents!")
		return agents

	except Exception as e:
		print(f"❌ Error scraping listing: {str(e)}")
		return agents

async def main(location_url: str, max_agents: int = 50, scrape_profiles: bool = True, output_file: str = "zillow_agents.csv"):
	"""Main function to run the Zillow agent scraper"""
	print("🚀 Starting Zillow Agent Scraper")

	# Connect to existing Chrome debug session
	async with async_playwright() as p:
		try:
			# Connect to existing Chrome session with remote debugging
			browser = await p.chromium.connect_over_cdp("http://localhost:9222")
			pages = browser.contexts[0].pages
			page = pages[0] if pages else await browser.contexts[0].new_page()

			print("✅ Connected to Chrome")

			# Scrape agents
			agents = await scrape_agent_listing(page, location_url, max_agents, scrape_profiles)

			if agents:
				# Generate contact info summary
				agents_with_phone = sum(1 for a in agents if a.phone)
				agents_with_email = sum(1 for a in agents if a.email)
				agents_with_both = sum(1 for a in agents if a.phone and a.email)

				print(f"\n📊 Contact Info Summary:")
				print(f"   Total agents: {len(agents)}")
				print(f"   With phone: {agents_with_phone} ({agents_with_phone/len(agents)*100:.1f}%)")
				print(f"   With email: {agents_with_email} ({agents_with_email/len(agents)*100:.1f}%)")
				print(f"   With both: {agents_with_both} ({agents_with_both/len(agents)*100:.1f}%)")

				if save_agents_to_csv(agents, output_file):
					print(f"\n🎉 Successfully scraped {len(agents)} agents and saved to {output_file}")
				else:
					print("❌ Failed to save CSV file")
			else:
				print("❌ No agents extracted")

		except Exception as e:
			print(f"❌ Error: {e}")
			print("💡 Make sure Chrome is running with: --remote-debugging-port=9222")
			print("   Example: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Zillow Real Estate Agent Scraper")
	parser.add_argument("--url", "-u",
		default="https://www.zillow.com/professionals/real-estate-agent-reviews/los-angeles-ca/",
		help="Zillow agent directory URL")
	parser.add_argument("--max-agents", "-m", type=int, default=50,
		help="Maximum number of agents to scrape (default: 50)")
	parser.add_argument("--no-profiles", action="store_true",
		help="Skip visiting individual agent profiles (faster, less data)")
	parser.add_argument("--output", "-o", default="zillow_agents.csv",
		help="Output CSV filename (default: zillow_agents.csv)")

	args = parser.parse_args()

	print(f"📍 Location URL: {args.url}")
	print(f"📊 Max agents: {args.max_agents}")
	print(f"🔍 Scrape profiles: {not args.no_profiles}")
	print(f"💾 Output file: {args.output}")

	asyncio.run(main(args.url, args.max_agents, not args.no_profiles, args.output))
