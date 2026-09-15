from agenttrust_client import AgentTrustClient

client = AgentTrustClient(api_key="demo-key-123")
result = client.verify_and_submit(
    agent_url="http://127.0.0.1:9001/",
    prompt="Summarize the latest task",
)
print(result)
