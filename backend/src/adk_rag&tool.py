from oci.addons.adk import Agent, AgentClient
from oci.addons.adk.tool.prebuilt import AgenticRagTool
from tools import AccountToolkit

import os
from dotenv import load_dotenv
load_dotenv()

agent_endpoint_id = os.getenv("AGENT_ENDPOINT_ID")
knowledge_base_id = os.getenv("KNOWLEDGE_BASE_ID")
print("agent_endpoint_id: ", agent_endpoint_id)
print("knowledge_base_id: ", knowledge_base_id)


def main():
    client = AgentClient(
        auth_type="api_key",
        profile="DEFAULT",
        region="us-chicago-1"
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
    rag_tool = AgenticRagTool(
        name="OCI RAG tool",
        description="Use this tool to answer questions about Oracle Cloud Infrastructure (OCI).",
        knowledge_base_ids=[knowledge_base_id],
    )

    # Create the agent with the RAG tool
    agent = Agent(
        client=client,
        agent_endpoint_id=agent_endpoint_id,
        instructions=instructions,
        tools=[
            rag_tool,
            AccountToolkit()
            ]
    )

    # Set up the agent once
    agent.setup()

    # # Run the agent with a user query
    # input = "Tell me about Oracle Cloud Infrastructure."
    # response = agent.run(input)
    # response.pretty_print()

if __name__ == "__main__":
    main()