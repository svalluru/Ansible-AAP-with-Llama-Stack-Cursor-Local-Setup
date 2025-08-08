from llama_stack_client import LlamaStackClient

client = LlamaStackClient(base_url="http://localhost:8321")

client.toolgroups.register(
    toolgroup_id="mcp::aap",
    provider_id="model-context-protocol",
    mcp_endpoint={"uri": "http://host.docker.internal:8000/sse"},
)

tgs = client.toolgroups.list()


print("Registered Tools:")
for tool in tgs:
    print(tool.identifier)
