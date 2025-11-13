#!/usr/bin/env python3
"""
Multi-page Skool scraper - scrape all 107 pages of members
Uses the same authentication cookies from the original curl command
"""

import subprocess
import time
import random
import os
from pathlib import Path
import csv
import json
from bs4 import BeautifulSoup
import hashlib
from datetime import datetime

# Base curl command with authentication
BASE_CURL_CMD = '''curl 'https://www.skool.com/skoolers/-/members?p={page}' \
  -H 'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7' \
  -H 'accept-language: en-GB,en-US;q=0.9,en;q=0.8' \
  -H 'cache-control: max-age=0' \
  -b 'ext_name=ojplmecpdpgccookcobabopnaifgidhf; client_id=6df8195b051e4c22b7867fdb92c0d2fa; __stripe_mid=4b69fc0f-a953-4cc5-b302-c0353d61b52724f663; _gcl_au=1.1.1511348854.1761706386.1203518421.1761752332.1761752332; muxData==undefined&mux_viewer_id=592b7bfa-2c7e-44c3-8cfe-172e30b76026&msn=0.33854685710027843&sid=34020d55-26e6-4827-b081-98a63b50e2d6&sst=1761931748054&sex=1761933347863; auth_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3OTM0NzI1ODUsImlhdCI6MTc2MTkzNjU4NSwidXNlcl9pZCI6IjUyNzQ0NWU0MGU3NjRiYmE4MTgzYjBlNWExNmZiNGFjIn0.99theV2gJN_uP2wbD-e97B6oFCnuxpCAEYn2VpGxqds; __stripe_sid=a1d79882-864c-46e9-b4a7-18f17dbfd7899a2aa1; AWSALBTG=oXDuWuKiGGr3fBjRhDswP5qF7KJTOoEfeml05axDvt93hJkhDRR9WnlM3lUxRuGNp+CE3BEh8qmLy/z/zl6AB+GTeBB+qRYyt/5PUE1o5xBKSBu5Z08m0TcP48JOIrIx3EvE2iv76tRWnAq+LVS7IFDXmos/Lu/NtR4zxv/BKsMACZjNvvA=; AWSALBTGCORS=oXDuWuKiGGr3fBjRhDswP5qF7KJTOoEfeml05axDvt93hJkhDRR9WnlM3lUxRuGNp+CE3BEh8qmLy/z/zl6AB+GTeBB+qRYyt/5PUE1o5xBKSBu5Z08m0TcP48JOIrIx3EvE2iv76tRWnAq+LVS7IFDXmos/Lu/NtR4zxv/BKsMACZjNvvA=; AWSALB=MgOXGCseINFqMg4wK+UhOyloHfQwEiW+STG1dex1aURTLCpc9a9bZKR5YAGHb/vg/a41Xa3W10SpwZwePTOe3tZy+tMw3SpdCGhyOdg+silvmJZpYSPWCw63MpQT; AWSALBCORS=MgOXGCseINFqMg4wK+UhOyloHfQwEiW+STG1dex1aURTLCpc9a9bZKR5YAGHb/vg/a41Xa3W10SpwZwePTOe3tZy+tMw3SpdCGhyOdg+silvmJZpYSPWCw63MpQT; aws-waf-token=f314dd64-9ec7-4b3d-827f-6674ff8201d0:BQoAsqRx5gVtAQAA:fxvRssWfDUBEjlBPhhAGlJlXBr0+7Iv+9q+4jbPcOwMBfGu7YfONOsaHHWyC+WcjjA9+wcjVpEr6B/xYw+y8OYLuNq/a64uVomh1KK5+f4r9dZUsOa27oryx/uUODR41oZqqBhtPqY9w8RaIe/+FWKCXCBduMor4bW8CzZLSm9nJvSV2oMGqz6tCX6047zm9Z4HNvendnzBXRXyR0n5+px1atbc0cn9vaUkR5z9cctubdLmkhe0ioQ7UlbByVhlKBtV9Pw==' \
  -H 'priority: u=0, i' \
  -H 'sec-ch-ua: "Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'sec-fetch-dest: document' \
  -H 'sec-fetch-mode: navigate' \
  -H 'sec-fetch-site: same-origin' \
  -H 'sec-fetch-user: ?1' \
  -H 'upgrade-insecure-requests: 1' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36' \
  -o 'page_{page}.html' \
  --connect-timeout 30 \
  --max-time 60'''

def generate_id(name: str) -> str:
	"""Generate a consistent ID for a user based on their name"""
	return hashlib.md5(name.encode()).hexdigest()

def parse_join_date(date_str: str) -> str:
	"""Parse join date string and convert to ISO format"""
	try:
		clean_date = date_str.replace("Joined", "").strip()
		for fmt in ["%b %d, %Y", "%B %d, %Y"]:
			try:
				parsed_date = datetime.strptime(clean_date, fmt)
				return parsed_date.isoformat() + "Z"
			except ValueError:
				continue
		return datetime.now().isoformat() + "Z"
	except:
		return datetime.now().isoformat() + "Z"

def extract_level_from_badge(badge_html: str) -> int:
	"""Extract level number from badge HTML"""
	try:
		level_match = __import__('re').search(r'>(\d+)<', badge_html)
		if level_match:
			return int(level_match.group(1))
	except:
		pass
	return 1

def scrape_page(page_num: int) -> bool:
	"""Scrape a single page using curl"""
	try:
		print(f"📄 Scraping page {page_num}...")
		
		# Execute curl command
		cmd = BASE_CURL_CMD.format(page=page_num)
		result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
		
		if result.returncode == 0:
			print(f"✅ Page {page_num} downloaded")
			return True
		else:
			print(f"❌ Error downloading page {page_num}: {result.stderr}")
			return False
			
	except Exception as e:
		print(f"❌ Exception on page {page_num}: {e}")
		return False

def parse_page_html(page_num: int) -> list:
	"""Parse HTML from a single page and extract user data"""
	filename = f"page_{page_num}.html"
	
	if not os.path.exists(filename):
		print(f"⚠️  File {filename} not found")
		return []
	
	try:
		with open(filename, 'r', encoding='utf-8') as f:
			content = f.read()
		
		soup = BeautifulSoup(content, 'html.parser')
		users = []
		
		# Find all member items
		member_items = soup.find_all('div', class_='styled__MemberItemWrapper-sc-qwyv4g-0')
		
		for i, member in enumerate(member_items):
			try:
				# Extract profile link and handle
				profile_link = member.find('a', href=__import__('re').compile(r'/@[^?]+'))
				if not profile_link:
					continue
					
				href = profile_link.get('href', '')
				handle = href.split('/@')[1].split('?')[0] if '/@' in href else f"user-{page_num}-{i}"
				
				# Extract name
				name_element = member.find('span', class_='styled__UserNameText-sc-24o0l3-1')
				if name_element:
					name_text = name_element.get_text(strip=True)
					name_parts = name_text.split()
					first_name = name_parts[0] if name_parts else handle.split('-')[0]
					last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else name_parts[-1] if name_parts else ""
				else:
					first_name = handle.split('-')[0]
					last_name = ""
				
				# Extract bio
				bio_element = member.find('div', class_='styled__MemberBio-sc-qwyv4g-6')
				bio = bio_element.get_text(strip=True) if bio_element else ""
				
				# Extract online status
				online_dot = member.find('div', class_='styled__OnlineDot-sc-qwyv4g-10')
				is_online = 1 if online_dot else 0
				
				# Extract join date
				join_date_element = member.find('span', string=__import__('re').compile(r'Joined'))
				join_date = ""
				if join_date_element:
					join_date_text = join_date_element.get_text(strip=True)
					join_date = parse_join_date(join_date_text)
				
				# Extract level from badge
				badge_element = member.find('div', class_='styled__BadgeWrapper-sc-1o1lx2q-2')
				level = 1
				if badge_element:
					level = extract_level_from_badge(str(badge_element))
				
				# Extract location
				location = ""
				location_icons = member.find_all('svg')
				for icon in location_icons:
					if 'M13.3327 6.66658C13.3327 9.61192' in str(icon):
						location_span = icon.find_parent().find_next_sibling('span')
						if location_span and not any(keyword in location_span.get_text().lower() 
													for keyword in ['joined', 'online', 'ago']):
							location = location_span.get_text(strip=True)
							break
				
				# Generate IDs
				user_id = generate_id(handle)
				member_id = generate_id(f"{handle}-member")
				group_id = "e44528d24bfe4d65b0a412441feaa489"
				
				# Create user data
				user_data = {
					"id": user_id,
					"name": handle,
					"firstName": first_name,
					"lastName": last_name,
					"email": "",
					"bio": bio,
					"online": is_online,
					"level": level,
					"location": location,
					"joinDate": join_date,
					"profileUrl": f"https://www.skool.com/@{handle}?g=skoolers",
					"memberId": member_id,
					"groupId": group_id,
					"role": "member",
					"page": page_num  # Track which page this came from
				}
				
				users.append(user_data)
				
			except Exception as e:
				print(f"❌ Error parsing member {i} on page {page_num}: {e}")
				continue
		
		print(f"📊 Extracted {len(users)} users from page {page_num}")
		return users
		
	except Exception as e:
		print(f"❌ Error parsing page {page_num}: {e}")
		return []

def scrape_all_pages(start_page: int = 1, end_page: int = 107, delay_range: tuple = (2, 5)) -> list:
	"""Scrape all pages from start_page to end_page"""
	all_users = []
	failed_pages = []
	
	print(f"🚀 Starting scrape of pages {start_page} to {end_page}")
	print(f"⏱️  Using {delay_range[0]}-{delay_range[1]} second delays between requests")
	
	for page_num in range(start_page, end_page + 1):
		try:
			# Download page
			if scrape_page(page_num):
				# Parse page
				users = parse_page_html(page_num)
				all_users.extend(users)
				
				print(f"📈 Total users so far: {len(all_users)}")
			else:
				failed_pages.append(page_num)
			
			# Add delay to be respectful to the server
			if page_num < end_page:  # Don't delay after the last page
				delay = random.uniform(delay_range[0], delay_range[1])
				print(f"⏳ Waiting {delay:.1f} seconds...")
				time.sleep(delay)
				
		except KeyboardInterrupt:
			print(f"\n⏸️  Scraping interrupted at page {page_num}")
			print(f"📊 Scraped {len(all_users)} users from {page_num - start_page} pages")
			break
		except Exception as e:
			print(f"❌ Unexpected error on page {page_num}: {e}")
			failed_pages.append(page_num)
			continue
	
	if failed_pages:
		print(f"⚠️  Failed pages: {failed_pages}")
	
	print(f"🎉 Scraping complete! Total users: {len(all_users)}")
	return all_users

def save_results(users: list, filename_base: str = "skool_all_users"):
	"""Save results to CSV and JSON"""
	if not users:
		print("❌ No users to save")
		return
	
	# Clean fieldnames (without pictures)
	fieldnames = [
		'id', 'name', 'firstName', 'lastName', 'email', 'bio', 
		'online', 'level', 'location', 'joinDate', 'profileUrl', 
		'memberId', 'groupId', 'role', 'page'
	]
	
	# Save CSV
	csv_filename = f"{filename_base}_{len(users)}.csv"
	with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
		writer = csv.DictWriter(f, fieldnames=fieldnames)
		writer.writeheader()
		for user in users:
			clean_row = {field: user.get(field, '') for field in fieldnames}
			writer.writerow(clean_row)
	
	# Save JSON
	json_filename = f"{filename_base}_{len(users)}.json"
	with open(json_filename, 'w', encoding='utf-8') as f:
		json.dump({
			"users": users, 
			"total": len(users),
			"scraped_at": datetime.now().isoformat(),
			"pages_scraped": len(set(user.get('page', 0) for user in users))
		}, f, indent=2, ensure_ascii=False)
	
	print(f"✅ Saved {len(users)} users to:")
	print(f"   📄 {csv_filename}")
	print(f"   📄 {json_filename}")

def cleanup_temp_files():
	"""Clean up temporary page HTML files"""
	page_files = [f for f in os.listdir('.') if f.startswith('page_') and f.endswith('.html')]
	for file in page_files:
		try:
			os.remove(file)
		except:
			pass
	print(f"🧹 Cleaned up {len(page_files)} temporary files")

if __name__ == "__main__":
	import argparse
	
	parser = argparse.ArgumentParser(description="Scrape all Skool member pages")
	parser.add_argument("--start", type=int, default=1, help="Start page number (default: 1)")
	parser.add_argument("--end", type=int, default=107, help="End page number (default: 107)")
	parser.add_argument("--delay-min", type=float, default=2.0, help="Minimum delay between requests (default: 2.0)")
	parser.add_argument("--delay-max", type=float, default=5.0, help="Maximum delay between requests (default: 5.0)")
	parser.add_argument("--keep-files", action="store_true", help="Keep temporary HTML files")
	parser.add_argument("--test", action="store_true", help="Test mode: only scrape first 3 pages")
	
	args = parser.parse_args()
	
	if args.test:
		print("🧪 TEST MODE: Scraping only pages 1-3")
		args.start = 1
		args.end = 3
	
	try:
		# Scrape all pages
		all_users = scrape_all_pages(
			start_page=args.start,
			end_page=args.end,
			delay_range=(args.delay_min, args.delay_max)
		)
		
		# Save results
		if all_users:
			save_results(all_users)
			
			# Show summary
			online_users = sum(1 for u in all_users if u.get('online'))
			levels = {}
			for user in all_users:
				level = user.get('level', 1)
				levels[level] = levels.get(level, 0) + 1
			
			print(f"\n📊 SUMMARY:")
			print(f"   👥 Total users: {len(all_users)}")
			print(f"   🟢 Online: {online_users}")
			print(f"   🔴 Offline: {len(all_users) - online_users}")
			print(f"   📈 Levels: {dict(sorted(levels.items()))}")
		
		# Cleanup
		if not args.keep_files:
			cleanup_temp_files()
			
	except KeyboardInterrupt:
		print("\n⏸️  Scraping stopped by user")
	except Exception as e:
		print(f"❌ Scraping failed: {e}")