from oci.addons.adk.tool.prebuilt import AgenticRagTool
from tools import AccountToolkit
from oci.addons.adk import tool 
from typing import Dict,Any
import os


#Definition of our tool and do not forget the @tool decorator
@tool(description="Get the season for a location")
def check_season(location:str) -> Dict[str, Any]:
    """Get the season for a given location

    Args:
      location(str): The location for which season her is queried
    """
    data = {
        "India":"Monsoon",
        "USA":"Summer",
        "Europe":"Summer",
        "Brazil":"Winter"

    }
    try:
        return {"location": location, "season": data[location]}
    except Exception as error:
         return {"location": "Unknown", "season": "Unknown"}
    

def return_tools() -> list:
    """Check the knowledge base id and append the tool list name"""
    tool_list = [AccountToolkit(),check_season]
    knowledge_base_id = os.getenv("KNOWLEDGE_BASE_ID")
    print("knowledge_base_id: ", knowledge_base_id)
    if  knowledge_base_id is not None:
        rag_tool = AgenticRagTool(
            name="OCI RAG tool",
            description="Use this tool to answer questions about Oracle Cloud Infrastructure (OCI).",
            knowledge_base_ids=[knowledge_base_id],
            )
        tool_list.append("rag_tool")
    print(tool_list)
    return tool_list
 
