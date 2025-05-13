from langchain_openai import ChatOpenAI
from browser_use import Agent
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

# Job details
JOB_LINK = "https://www.google.com/about/careers/applications/jobs/results/78013920337371846-software-engineer-ii"
JOB_TITLE = "Software Engineer II, Site Reliability Engineering"
TEAM = "Google Cloud"

async def main():
    # Initialize the agent with LinkedIn automation task
    agent = Agent(
        task=f"""1. Log in to LinkedIn using the provided credentials from environment variables
2. Search for people who work at Google
3. For each person found:
   - Check their connection status:
     * If already connected: Send referral message directly
     * If not connected: Send connection request
     * If connection pending: Skip and move to next person

   - For existing connections, send this message:
     Hi [Name],

     I came across this opening at Google that seems like a strong match with my background and interests:

     {JOB_LINK}

     {JOB_TITLE} {TEAM}

     If you're connected to this team or could refer me, I'd be truly grateful for your support!

     Thanks so much,
4. Make sure to:
   - Replace [Name] with their actual name
   - Keep track of:
     * People messaged
     * Connection requests sent
     * Pending connections (to check later)
   - Don't send more than 10 connection requests per day
   - Don't send more than 10 messages per day""",
        llm=ChatOpenAI(
            model="gpt-4-turbo-preview",  # Using the latest GPT-4 model
            temperature=0.7  # Adding some creativity to responses
        )
    )
    
    # Run the agent
    result = await agent.run()
    print("Task completed:", result)

if __name__ == "__main__":
    asyncio.run(main()) 