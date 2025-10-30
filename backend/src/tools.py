from oci.addons.adk import Toolkit, tool

class AccountToolkit(Toolkit):

    @tool
    def get_user_info(self, user_id: str) -> str:
        """Get information about a user by user_id

        Args:
            user_id (str): The user ID to get information about

        Returns:
            Dict[str, Any]: A dictionary containing the user information
        """
        # Here is a mock implementation
        data = {
            "user_id": user_id,
            "account_id": "acc_111",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "org_id": "org_222",
        }
        return str(data)

    @tool
    def get_org_info(self, org_id: str) -> str:
        """Get information about an organization by org_id

        Args:
            org_id (str): The organization ID to get information about

        Returns:
            Dict[str, Any]: A dictionary containing the organization information
        """
        # Here is a mock implementation
        data = {
            "org_id": org_id,
            "name": "Acme Inc",
            "admin_email": "admin@acme.com",
            "plan": "Enterprise",
        }
        return str(data)

AGENT_TOOLS = {
    "get_user_info": AccountToolkit().get_user_info,
    "get_org_info": AccountToolkit().get_org_info
}


