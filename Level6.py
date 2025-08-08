#!/usr/bin/env python
# coding: utf-8

from pprint import pprint
from flask import Flask, request, jsonify

from llama_stack_client import LlamaStackClient
from llama_stack_client import Agent
from llama_stack_client.lib.agents.event_logger import EventLogger
from llama_stack_client import RAGDocument
from llama_stack_client.lib.agents.react.agent import ReActAgent
from llama_stack_client.lib.agents.react.tool_parser import ReActOutput

# pretty print of the results returned from the model/agent
from termcolor import cprint
import sys
sys.path.append('..')  
#from src.utils import step_printer
import uuid
import os

from dotenv import load_dotenv


# for communication with Llama Stack
load_dotenv()


base_url = os.getenv("REMOTE_BASE_URL")


provider_data = None

client = LlamaStackClient(
    base_url=base_url,
    provider_data=provider_data
)

print(f"Connected to Llama Stack server")

# model_id will later be used to pass the name of the desired inference model to Llama Stack Agents/Inference APIs
model_id = "llama3.2:3b"

temperature = float(os.getenv("TEMPERATURE", 0.0))
if temperature > 0.0:
    top_p = float(os.getenv("TOP_P", 0.95))
    strategy = {"type": "top_p", "temperature": temperature, "top_p": top_p}
else:
    strategy = {"type": "greedy"}

max_tokens = int(os.getenv("MAX_TOKENS", 512))

# sampling_params will later be used to pass the parameters to Llama Stack Agents/Inference APIs
sampling_params = {
    "strategy": strategy,
    "max_tokens": max_tokens,
}


stream_env = os.getenv("STREAM", "False")
# the Boolean 'stream' parameter will later be passed to Llama Stack Agents/Inference APIs
# any value non equal to 'False' will be considered as 'True'
stream = (stream_env != "False")

print(f"Inference Parameters:\n\tModel: {model_id}\n\tSampling Parameters: {sampling_params}\n\tstream: {stream}")

# Optional: Enter your MCP server URL here
aap_mcp_url = os.getenv("REMOTE_AAP_MCP_URL") # Optional: enter your MCP server url here

tgs = client.toolgroups.list()

print(client.models.list())

print("Registered Tools:")
for tool in tgs:
    print(tool.identifier)

#print(client.tools.list(toolgroup_id="mcp::aapa"))

model_prompt= """You are a helpful assistant. You have access to a number of tools.
Whenever a tool is called, be sure return the Response in a friendly and helpful tone."""

# Create simple agent with tools
#print(client.tools.list(toolgroup_id="mcp::aapa"))
print("Creating agent with tools")

agent = Agent(
    client,
    model=model_id, # replace this with your choice of model
    instructions = model_prompt , # update system prompt based on the model you are using
    tools=["mcp::aap",],
    tool_config={"tool_choice":"auto"},
    sampling_params=sampling_params
)



session_id = agent.create_session(session_name="AAP_demo")

print(session_id)
response = agent.create_turn(
        messages=[
            {
                "role":"user",
                "content": "get me list of projects in AAP"
            }
        ],
        session_id=session_id,
        stream=stream,
    )

pprint(response)

