# Zillow Real Estate Agent Scraper

Scrapes real estate agent data from Zillow's agent directory pages using Playwright.

## Features

- Scrapes agent listings from any Zillow location
- Extracts basic info: name, profile URL, phone, rating, reviews
- Optionally visits each agent's profile for detailed data:
  - Email address
  - Bio/description
  - Sales count
  - Specialties
  - Office information
  - License number
  - Website
- Saves all data to CSV
- Uses existing Chrome session with CDP for bypassing bot detection
- Human-like delays and scrolling

## Prerequisites

1. **Start Chrome with Remote Debugging:**

   ```bash
   # macOS
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome-debug"

   # Linux
   google-chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome-debug"

   # Windows
   "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\temp\chrome-debug"
   ```

2. **Install Dependencies:**

   ```bash
   pip install playwright pandas
   playwright install chromium
   ```

## Usage

### Basic Usage (Default: Los Angeles)

```bash
python zillow_agent_scraper.py
```

### Custom Location

```bash
python zillow_agent_scraper.py --url "https://www.zillow.com/professionals/real-estate-agent-reviews/new-york-ny/"
```

### Scrape More Agents

```bash
python zillow_agent_scraper.py --max-agents 100
```

### Fast Mode (Skip Profile Scraping)

Only scrape listing page data, don't visit individual profiles:

```bash
python zillow_agent_scraper.py --no-profiles --max-agents 200
```

### Custom Output File

```bash
python zillow_agent_scraper.py --output "la_agents.csv"
```

### Full Example

```bash
python zillow_agent_scraper.py \
  --url "https://www.zillow.com/professionals/real-estate-agent-reviews/miami-fl/" \
  --max-agents 75 \
  --output "miami_agents.csv"
```

## Output Format

CSV file with the following columns:

| Column | Description |
|--------|-------------|
| name | Agent's full name |
| profile_url | Link to agent's Zillow profile |
| phone | Phone number |
| email | Email address (if available) |
| rating | Star rating (e.g., "4.9") |
| review_count | Number of reviews |
| sales_count | Number of sales completed |
| specialties | Agent specialties/expertise |
| bio | Agent bio/description |
| office | Office name/location |
| license | Real estate license number |
| website | Agent's website |
| location | City/area |

## Finding Location URLs

Navigate to Zillow's agent directory for your target location:

1. Go to https://www.zillow.com
2. Search for "real estate agents in [city]"
3. Copy the URL from the agent directory page
4. Use it with the `--url` parameter

Example URLs:
- Los Angeles: `https://www.zillow.com/professionals/real-estate-agent-reviews/los-angeles-ca/`
- New York: `https://www.zillow.com/professionals/real-estate-agent-reviews/new-york-ny/`
- Miami: `https://www.zillow.com/professionals/real-estate-agent-reviews/miami-fl/`
- Chicago: `https://www.zillow.com/professionals/real-estate-agent-reviews/chicago-il/`

## Performance Tips

1. **Fast mode:** Use `--no-profiles` to skip visiting individual profiles (much faster)
2. **Batch processing:** Scrape multiple locations by running the script multiple times with different URLs
3. **Rate limiting:** Built-in random delays prevent rate limiting
4. **Pagination:** Script automatically scrolls to load more agents

## Troubleshooting

### No agents found
- Check that the URL is correct
- Try manually visiting the page in your debug Chrome session first
- Zillow may have updated their HTML structure (check selectors)

### 403 Forbidden errors
- Make sure you're using Chrome with remote debugging
- Try manually visiting Zillow first in the debug session
- Clear cookies/cache and try again

### Missing data fields
- Some agents don't provide all information
- Email addresses are rarely public on Zillow
- Use `--no-profiles` flag if profile scraping is failing

## Notes

- Zillow uses lazy loading, so the script scrolls to load more agents
- Email addresses are rarely available on Zillow profiles
- Phone numbers may be click-to-reveal (script attempts to extract them)
- Respect Zillow's Terms of Service and rate limits
- Don't run at high frequency to avoid IP bans

## Legal Disclaimer

This tool is for educational purposes. Make sure to:
- Review Zillow's Terms of Service
- Respect rate limits and robots.txt
- Only use scraped data for legitimate purposes
- Don't share or sell scraped contact information without consent
