# LinkedIn Automation Example

This example demonstrates how to use Browser Use to automate LinkedIn interactions, including logging in and sending messages to connections.

## Prerequisites

1. Python 3.11 or higher
2. Browser Use installed (`pip install browser-use`)
3. OpenAI API key
4. LinkedIn account credentials

## Setup

1. Create a `.env` file in your project root with the following variables:
```bash
OPENAI_API_KEY=your_openai_api_key
LINKEDIN_EMAIL=your_linkedin_email
LINKEDIN_PASSWORD=your_linkedin_password
```

2. Install the required dependencies:
```bash
pip install browser-use python-dotenv langchain-openai
```

## Usage

Run the example:
```bash
python linkedin_messaging.py
```

## Features

The example demonstrates:
- LinkedIn login automation
- Searching for people by job title and location
- Sending personalized messages
- Tracking message history
- Error handling and retries

## Customization

You can modify the script to:
- Change the search criteria (job title, location)
- Adjust the number of people to message
- Customize the message template
- Add more sophisticated tracking
- Implement additional LinkedIn features

## Important Notes

1. **Rate Limiting**: Be mindful of LinkedIn's rate limits and terms of service
2. **Privacy**: Never share your `.env` file or credentials
3. **Testing**: Always test with a small number of messages first
4. **Headless Mode**: Set `headless=True` for production use

## Safety Considerations

- Always respect LinkedIn's terms of service
- Don't spam or send unsolicited messages
- Use appropriate delays between actions
- Monitor your account for any warning signs
- Keep your credentials secure

## Troubleshooting

If you encounter issues:
1. Check your credentials in the `.env` file
2. Ensure you have the latest version of Browser Use
3. Verify your OpenAI API key is valid
4. Check LinkedIn's login page for any changes
5. Monitor the browser for any CAPTCHA or verification requests 