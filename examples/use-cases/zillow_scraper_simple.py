#!/usr/bin/env python3
"""
Zillow Real Estate Agent Scraper - Simple HTML Parser
Fetches HTML directly and extracts email/phone from agent profiles

@file purpose: Simple HTTP-based scraper for Zillow agent data
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
import csv
import argparse
import re
from dataclasses import dataclass, asdict
from typing import List
import random
from urllib.parse import unquote

@dataclass
class AgentInfo:
	name: str
	profile_url: str
	email: str = ""  # Priority #1
	phone: str = ""  # Priority #2
	office_phone: str = ""
	brokerage: str = ""
	rating: str = ""
	review_count: str = ""
	price_range: str = ""
	recent_sales: str = ""
	total_sales: str = ""
	bio: str = ""
	license: str = ""
	website: str = ""
	specialties: str = ""
	languages: str = ""

def parse_cookies(cookie_string: str) -> dict:
	"""Parse cookie string into dict"""
	cookies = {}
	if not cookie_string:
		return cookies

	# Handle both semicolon and newline separated cookies
	cookie_string = cookie_string.replace('\n', '; ')

	for cookie in cookie_string.split(';'):
		cookie = cookie.strip()
		if '=' in cookie:
			key, value = cookie.split('=', 1)
			cookies[key.strip()] = unquote(value.strip())

	return cookies

def load_cookies_from_file(filepath: str) -> dict:
	"""Load cookies from file"""
	try:
		with open(filepath, 'r') as f:
			cookie_string = f.read()
		return parse_cookies(cookie_string)
	except Exception as e:
		print(f"❌ Error loading cookies from {filepath}: {e}")
		return {}

def init_csv(filename: str, fieldnames: list):
	"""Initialize CSV file with headers"""
	try:
		with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
			writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
			writer.writeheader()
		return True
	except Exception as e:
		print(f"❌ Error creating CSV: {e}")
		return False

def append_agent_to_csv(agent: AgentInfo, filename: str):
	"""Append a single agent to CSV file"""
	try:
		with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
			fieldnames = list(asdict(agent).keys())
			writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
			writer.writerow(asdict(agent))
		return True
	except Exception as e:
		print(f"  ❌ Error appending to CSV: {e}")
		return False

def save_agents_to_csv(agents: List[AgentInfo], filename: str = "zillow_agents.csv"):
	"""Save agent information to CSV file (legacy function for final save)"""
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

async def fetch_html(url: str, client: httpx.AsyncClient, cookies: dict = None) -> str:
	"""Fetch HTML from URL with proper headers and cookies"""
	headers = {
		'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
		'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
		'Accept-Encoding': 'gzip, deflate, br',
		'Cache-Control': 'max-age=0',
		'DNT': '1',
		'Connection': 'keep-alive',
		'Upgrade-Insecure-Requests': '1',
		'Sec-Fetch-Dest': 'document',
		'Sec-Fetch-Mode': 'navigate',
		'Sec-Fetch-Site': 'same-origin',
		'Sec-Fetch-User': '?1',
		'Sec-Ch-Ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
		'Sec-Ch-Ua-Mobile': '?0',
		'Sec-Ch-Ua-Platform': '"macOS"',
		'Referer': 'https://www.zillow.com/professionals/real-estate-agent-reviews/los-angeles-ca/',
	}

	try:
		response = await client.get(url, headers=headers, cookies=cookies, timeout=30.0)
		response.raise_for_status()
		return response.text
	except Exception as e:
		print(f"❌ Error fetching {url}: {e}")
		return ""

def extract_agents_from_listing(html: str) -> List[str]:
	"""Extract agent profile URLs from listing page HTML"""
	soup = BeautifulSoup(html, 'html.parser')
	profile_urls = []

	# Find all links to profile pages
	for link in soup.find_all('a', href=True):
		href = link['href']
		if '/profile/' in href:
			if not href.startswith('http'):
				href = f"https://www.zillow.com{href}"
			if href not in profile_urls:
				profile_urls.append(href)

	return profile_urls

def extract_basic_info_from_card(card_html: str) -> dict:
	"""Extract basic info from agent card on listing page"""
	soup = BeautifulSoup(card_html, 'html.parser')
	info = {}

	# Extract brokerage
	brokerage_elem = soup.find(['span', 'div'], class_=re.compile('.*'))
	if brokerage_elem and 'HomeServices' in brokerage_elem.text or 'Realty' in brokerage_elem.text:
		info['brokerage'] = brokerage_elem.text.strip()

	# Extract rating
	rating_elem = soup.find('span', class_=re.compile('.*NumberRating.*'))
	if rating_elem:
		rating_text = rating_elem.find('span', class_=re.compile('Text.*'))
		if rating_text:
			info['rating'] = rating_text.text.strip()

	# Extract review count
	review_match = re.search(r'\((\d+)\)', str(soup))
	if review_match:
		info['review_count'] = review_match.group(1)

	# Extract price range
	price_match = re.search(r'\$[\d.]+[MK]?\s*-\s*\$[\d.]+[MK]?', soup.text)
	if price_match:
		info['price_range'] = price_match.group(0)

	# Extract recent sales
	sales_match = re.search(r'(\d+)\s*sales?\s+last\s+12\s+months?', soup.text, re.IGNORECASE)
	if sales_match:
		info['recent_sales'] = f"{sales_match.group(1)} sales last 12 months"

	# Extract total sales
	total_match = re.search(r'(\d+)\s*sales?\s+in\s+', soup.text, re.IGNORECASE)
	if total_match:
		info['total_sales'] = total_match.group(0).strip()

	return info

def extract_agent_from_profile(html: str, profile_url: str) -> AgentInfo | None:
	"""Extract all agent info from profile page HTML"""
	soup = BeautifulSoup(html, 'html.parser')

	# Extract name
	name = ""
	name_elem = soup.find(['h1', 'h2'], class_=re.compile('.*'))
	if name_elem:
		name = name_elem.text.strip()

	if not name:
		# Try to extract from title
		title = soup.find('title')
		if title:
			name = title.text.split('|')[0].strip()

	# Extract email - priority #1
	email = ""
	mailto_links = soup.find_all('a', href=re.compile(r'^mailto:'))
	if mailto_links:
		email = mailto_links[0]['href'].replace('mailto:', '').split('?')[0].strip()
		print(f"  ✅ Found email: {email}")

	# If no mailto link, search for email pattern in text
	if not email:
		email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
		email_match = re.search(email_pattern, html)
		if email_match:
			email = email_match.group(0)
			print(f"  ✅ Found email in HTML: {email}")

	# Extract phone - priority #2
	phone = ""
	office_phone = ""
	tel_links = soup.find_all('a', href=re.compile(r'^tel:'))
	phones = []
	for tel_link in tel_links:
		tel = tel_link['href'].replace('tel:', '').replace('+1', '').strip()
		# Clean and format phone
		tel_clean = re.sub(r'[^0-9]', '', tel)
		if len(tel_clean) >= 10:
			formatted = f"({tel_clean[:3]}) {tel_clean[3:6]}-{tel_clean[6:10]}"
			if formatted not in phones:
				phones.append(formatted)

	if len(phones) > 0:
		phone = phones[0]
		print(f"  ✅ Found phone: {phone}")
	if len(phones) > 1:
		office_phone = phones[1]
		print(f"  ✅ Found office phone: {office_phone}")

	# Extract brokerage
	brokerage = ""
	brokerage_patterns = [
		re.compile(r'Berkshire Hathaway.*', re.IGNORECASE),
		re.compile(r'Keller Williams.*', re.IGNORECASE),
		re.compile(r'Coldwell Banker.*', re.IGNORECASE),
		re.compile(r'RE/MAX.*', re.IGNORECASE),
		re.compile(r'Century 21.*', re.IGNORECASE),
		re.compile(r'Sotheby.*', re.IGNORECASE),
		re.compile(r'Compass.*', re.IGNORECASE),
		re.compile(r'eXp Realty.*', re.IGNORECASE),
	]
	for pattern in brokerage_patterns:
		match = pattern.search(soup.text)
		if match:
			brokerage = match.group(0).strip()
			break

	# Extract rating and reviews
	rating = ""
	review_count = ""
	rating_elem = soup.find(text=re.compile(r'^\d+\.\d+$'))
	if rating_elem:
		rating = rating_elem.strip()
	review_match = re.search(r'\((\d+)\)', soup.text)
	if review_match:
		review_count = review_match.group(1)

	# Extract bio
	bio = ""
	bio_elem = soup.find(['p', 'div'], class_=re.compile(r'.*bio.*|.*description.*|.*about.*', re.IGNORECASE))
	if bio_elem:
		bio = bio_elem.text.strip()[:500]  # Limit to 500 chars

	# Extract license
	license_num = ""
	license_match = re.search(r'(?:DRE|License)\s*#?\s*:?\s*([A-Z0-9]+)', soup.text, re.IGNORECASE)
	if license_match:
		license_num = license_match.group(1)

	# Extract website
	website = ""
	website_links = soup.find_all('a', href=re.compile(r'^https?://(?!.*zillow).*'))
	if website_links:
		for link in website_links:
			href = link['href']
			if 'zillow' not in href.lower() and ('http' in href):
				website = href
				break

	# Extract specialties
	specialties = ""
	spec_keywords = ['Buyer', 'Seller', 'Luxury', 'First-time', 'Investment', 'Residential', 'Commercial']
	found_specs = []
	for keyword in spec_keywords:
		if keyword.lower() in soup.text.lower():
			found_specs.append(keyword)
	if found_specs:
		specialties = ", ".join(found_specs[:5])

	# Extract languages
	languages = ""
	lang_match = re.search(r'(?:Languages?|Speaks?):\s*([A-Za-z,\s]+)', soup.text, re.IGNORECASE)
	if lang_match:
		languages = lang_match.group(1).strip()

	# Extract sales info
	price_range = ""
	price_match = re.search(r'\$[\d.]+[MK]?\s*(?:-|to)\s*\$[\d.]+[MK]?', soup.text)
	if price_match:
		price_range = price_match.group(0)

	recent_sales = ""
	sales_match = re.search(r'(\d+)\s*(?:sales?|transactions?)\s*(?:in\s*)?(?:last|past)?\s*12\s*months?', soup.text, re.IGNORECASE)
	if sales_match:
		recent_sales = f"{sales_match.group(1)} sales last 12 months"

	total_sales = ""
	total_match = re.search(r'(\d+)\s*(?:total\s*)?sales?', soup.text, re.IGNORECASE)
	if total_match:
		total_sales = total_match.group(1)

	if name and profile_url:
		return AgentInfo(
			name=name,
			profile_url=profile_url,
			email=email,
			phone=phone,
			office_phone=office_phone,
			brokerage=brokerage,
			rating=rating,
			review_count=review_count,
			price_range=price_range,
			recent_sales=recent_sales,
			total_sales=total_sales,
			bio=bio,
			license=license_num,
			website=website,
			specialties=specialties,
			languages=languages
		)

	return None

async def scrape_agents(listing_url: str, max_agents: int = 50, max_pages: int = 1, cookies: dict = None, output_file: str = None) -> List[AgentInfo]:
	"""Scrape agents from listing pages and their profiles"""
	agents = []

	# Initialize CSV file if output file is specified
	csv_initialized = False
	if output_file:
		fieldnames = list(asdict(AgentInfo(name="", profile_url="")).keys())
		if init_csv(output_file, fieldnames):
			csv_initialized = True
			print(f"✅ Created CSV file: {output_file}\n")

	async with httpx.AsyncClient(follow_redirects=True) as client:
		# Collect profile URLs from listing pages
		all_profile_urls = []

		for page_num in range(1, max_pages + 1):
			# Handle URL with existing query params
			if '?page=' in listing_url:
				# Replace existing page param
				page_url = re.sub(r'page=\d+', f'page={page_num}', listing_url)
			elif '?' in listing_url:
				page_url = f"{listing_url}&page={page_num}"
			else:
				page_url = f"{listing_url}?page={page_num}"

			print(f"\n📄 Fetching listing page {page_num}...")
			html = await fetch_html(page_url, client, cookies)

			if not html:
				print(f"❌ Failed to fetch page {page_num}")
				continue

			profile_urls = extract_agents_from_listing(html)
			print(f"✅ Found {len(profile_urls)} agent profiles on page {page_num}")

			all_profile_urls.extend(profile_urls)

			# Add delay between pages
			await asyncio.sleep(random.uniform(1, 3))

		# Remove duplicates
		all_profile_urls = list(dict.fromkeys(all_profile_urls))
		print(f"\n📊 Total unique profiles found: {len(all_profile_urls)}")
		print(f"📊 Will scrape: {min(max_agents, len(all_profile_urls))} profiles\n")

		# Scrape each agent profile
		for i, profile_url in enumerate(all_profile_urls[:max_agents], 1):
			print(f"👤 [{i}/{min(max_agents, len(all_profile_urls))}] Scraping {profile_url}")

			html = await fetch_html(profile_url, client, cookies)

			if not html:
				print(f"  ❌ Failed to fetch profile")
				continue

			agent = extract_agent_from_profile(html, profile_url)

			if agent:
				agents.append(agent)

				# Append to CSV immediately
				if csv_initialized and output_file:
					append_agent_to_csv(agent, output_file)

				contact_info = []
				if agent.email:
					contact_info.append("email")
				if agent.phone:
					contact_info.append("phone")
				status = f" ({', '.join(contact_info)})" if contact_info else " (no contact)"
				print(f"  ✅ {agent.name}{status}")
			else:
				print(f"  ❌ Failed to extract agent info")

			# Add delay between profiles
			await asyncio.sleep(random.uniform(2, 4))

	return agents

async def main(listing_url: str, max_agents: int = 50, max_pages: int = 1, output_file: str = "zillow_agents.csv", cookies: dict = None):
	"""Main function"""
	print("🚀 Starting Zillow Agent Scraper (Simple HTML Parser)")
	print(f"📍 URL: {listing_url}")
	print(f"📄 Pages to scrape: {max_pages}")
	print(f"👥 Max agents per page: {max_agents}")
	print(f"💾 Output: {output_file}")
	print(f"🍪 Cookies: {'Loaded' if cookies else 'None'}\n")

	agents = await scrape_agents(listing_url, max_agents, max_pages, cookies, output_file)

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

		print(f"\n🎉 Successfully scraped {len(agents)} agents and saved to {output_file}!")
	else:
		print("\n❌ No agents extracted")

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Zillow Agent Scraper - Simple HTML Parser")
	parser.add_argument("--url", "-u",
		default="https://www.zillow.com/professionals/real-estate-agent-reviews/los-angeles-ca/",
		help="Zillow agent directory URL")
	parser.add_argument("--max-agents", "-m", type=int, default=50,
		help="Maximum agents to scrape per page (default: 50)")
	parser.add_argument("--max-pages", "-p", type=int, default=1,
		help="Number of listing pages to scrape (default: 1)")
	parser.add_argument("--output", "-o", default="zillow_agents.csv",
		help="Output CSV filename")
	parser.add_argument("--cookies", "-c",
		help="Cookie string or path to file containing cookies")

	args = parser.parse_args()

	# Load cookies
	cookies = None
	if args.cookies:
		# Check if it's a file path
		import os
		if os.path.exists(args.cookies):
			cookies = load_cookies_from_file(args.cookies)
			print(f"✅ Loaded cookies from file: {args.cookies}")
		else:
			# Treat as cookie string
			cookies = parse_cookies(args.cookies)
			print(f"✅ Parsed cookies from string")

		if not cookies:
			print("❌ No cookies loaded. Results may be limited.")
	else:
		print("⚠️  No cookies provided. Zillow may block requests.")
		print("   Use --cookies to provide cookies from your browser")

	asyncio.run(main(args.url, args.max_agents, args.max_pages, args.output, cookies))
