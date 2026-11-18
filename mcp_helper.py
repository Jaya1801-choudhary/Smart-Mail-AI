import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def _call_tool_async(tool_name, arguments=None):
    if arguments is None:
        arguments = {}
        
    # Server ka path batao
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"]
    )
    
    # Server se connect karke tool run karo
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments=arguments)
            return result.content[0].text

# Ye function hum Streamlit me call karenge
def run_mcp_tool(tool_name, arguments=None):
    """Streamlit se direct call karne ke liye synchronous function"""
    return asyncio.run(_call_tool_async(tool_name, arguments))