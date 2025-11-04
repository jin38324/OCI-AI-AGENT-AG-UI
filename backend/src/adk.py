from oci.addons.adk import Agent, AgentClient
from tool import return_tools
from dotenv import load_dotenv
import os

load_dotenv()

agent_endpoint_id = os.getenv("AGENT_ENDPOINT_ID")
print("agent_endpoint_id: ", agent_endpoint_id)



def main():
    client = AgentClient(
        auth_type=os.getenv("OCI_AUTH_MODE",default="api_key"),
        profile=os.getenv("CONFIG_PROFILE",default="DEFAULT"),
        region=os.getenv("OCI_REGION",default="us-chicago-1")
    )
    
    instructions = """
    You are customer support agent.
    Use RAG tool to answer product questions.
    Use function tools to fetch user and org info by id.
    Only orgs of Enterprise plan can use Responses API.
    """

    # Assuming the knowledge base is already provisioned  

    # Create a RAG tool that uses the knowledge base
    # The tool name and description are optional, but strongly recommended for LLM to understand the tool.
   
    # Create the agent with the RAG tool
    agent = Agent(
        client=client,
        agent_endpoint_id=agent_endpoint_id,
        instructions=instructions,
        tools=return_tools()
            
    )

    # Set up the agent once
    agent.setup()

    # # Run the agent with a user query
    # input = "Tell me about Oracle Cloud Infrastructure."
    # response = agent.run(input)
    # response.pretty_print()

if __name__ == "__main__":
    main()