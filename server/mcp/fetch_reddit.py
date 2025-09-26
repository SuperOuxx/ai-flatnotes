from llama_index.tools.mcp import (
    BasicMCPClient, McpToolSpec,
)
from llama_index.core.agent.workflow import FunctionAgent, ToolCallResult, ToolCall
from llama_index.core.workflow import Context
from llama_index.core.base.llms.base import BaseLLM

# "reddit": {
#         "command": "uvx",
#         "args": ["--from", "git+https://github.com/adhikasp/mcp-reddit.git", "mcp-reddit"],
#         "env": {
#           "REDDIT_CLIENT_ID": "IPu1dYXYQdlz-204dlXUWw",
#           "REDDIT_CLIENT_SECRET": "UP--5zLOSiAsb4DrW1IRnsnh6NDKSQ"
#         }
#       }
# or 下面这个tool更多
# "reddit": {
#     "command": "python",
#     "args": ["-m", "mcp_server_reddit"]
#   }

class BaseMcp:

    async def get_agent(self):
        if not self.agent:
            tools = await self.tool_spec.to_tool_list_async()
            self.agent = FunctionAgent(
                name=self.AGENT_NAME,
                description=self.AGENT_DESC,
                llm=self.llm,
                tools=tools,
                system_prompt=self.SYSTEM_PROMPT,
            )
        return self.agent

    async def handle_query(self, 
        query: str,
        verbose: bool = True,
    ):
        agent = await self.get_agent()

        # create the agent context
        agent_context = Context(agent)
        handler = agent.run(query, ctx=agent_context)
        async for event in handler.stream_events():
            if verbose and type(event) == ToolCall:
                print(f"Calling tool {event.tool_name} with kwargs {event.tool_kwargs}")
            elif verbose and type(event) == ToolCallResult:
                print(f"Tool {event.tool_name} returned {event.tool_output}")

        return await handler


class RedditMcp(BaseMcp):
    SYSTEM_PROMPT = """\
    You are an AI assistant for Tool Calling.

    Before you help a user, you need to work with tools to interact with Our Database
    """

    AGENT_NAME = "RedditMCPServer"
    AGENT_DESC = "Reddit MCP Server"

    def __init__(self, llm: BaseLLM):
        super().__init__()


        self.mcp_client = BasicMCPClient(command_or_url="python", 
                                args=["-m", "mcp_server_reddit"],
                                env={
                                    "REDDIT_CLIENT_ID": os.environ.get("REDDIT_CLIENT_ID"),
                                    "REDDIT_CLIENT_SECRET": os.environ.get("REDDIT_CLIENT_SECRET")
                                    }
                                )

        self.tool_spec = McpToolSpec(
            client=self.mcp_client,
            # Optional: Filter the tools by name
            # allowed_tools=["tool1", "tool2"],
            # Optional: Include resources in the tool list
            # include_resources=True,
        )

        self.llm: BaseLLM = llm

        self.agent = None

from llama_index.llms.openai_like import OpenAILike
import os

async def main():
    API_KEY = os.environ.get("OPENAI_API_KEY")
    
    API_BASE = os.environ.get("OPENAI_API_BASE")

    llm = OpenAILike(
        model="llamaCpp",
        api_base="http://localhost:18080/v1",
        api_key=API_KEY,
        # context_window=128000,
        is_chat_model=True,
        is_function_calling_model=True,
    )
    user_input = """
        用我的 Reddit 权限，从 r/education 抓热点与吐槽；
        按“谁、在什么场景、要什么结果”做聚类。
    """
    mcp = RedditMcp(llm)
    response = await mcp.handle_query(user_input)
    print("Agent: ", str(response))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
    
