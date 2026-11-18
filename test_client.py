import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_mcp_test():
    print("🔌 Connecting to MCP Server...")
    
    # 1. Client ko batana ki server kahan hai (Client khud isko background me run karega)
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"], # Tumhare server file ka naam
    )
    
    # 2. Secure Stdio connection open karna
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Connection initialize karo
            await session.initialize()
            print("✅ Connected Successfully!\n")
            
            # 3. Server se pucho ki uske paas kon kon se tools hain
            print("🛠️ Available Tools fetched from Server:")
            tools_response = await session.list_tools()
            for tool in tools_response.tools:
                print(f" 👉 {tool.name}")
            
            # 4. As a test, ek tool ko call karke dekhte hain!
            print("\n🤖 Calling tool: 'check_authentication_status'...")
            result = await session.call_tool("check_authentication_status")
            
            # 5. Output print karo
            print(f"🎯 Server Reply: {result.content[0].text}")

if __name__ == "__main__":
    asyncio.run(run_mcp_test())