
"""
Example server for the AG-UI protocol.
"""

import os
import uvicorn
import uuid
import copy
import json
import jsonpatch
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from ag_ui.core import (
    RunAgentInput,
    EventType,
    RunStartedEvent,
    RunFinishedEvent,
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    StateSnapshotEvent,
    StateDeltaEvent
)
from ag_ui.encoder import EventEncoder


from oci.config import from_file
from oci.generative_ai_agent_runtime import GenerativeAiAgentRuntimeClient
from oci.generative_ai_agent_runtime.models import CreateSessionDetails, ChatDetails, FunctionCallingPerformedAction




from tools import AGENT_TOOLS


## Set service information
load_dotenv()

# config
config = from_file(
    os.getenv("CONFIG_PATH"), 
    os.getenv("CONFIG_PROFILE")
    )

# Service endpoint
compartment_id = os.getenv("COMPARTMENT_ID")
agent_id = os.getenv("AGENT_ID")
service_endpoint = os.getenv("SERVICE_ENDPOINT")
agent_endpoint_id = os.getenv("AGENT_ENDPOINT_ID")

  
genai_agent_runtime_client = GenerativeAiAgentRuntimeClient(
    config=config,
    service_endpoint=service_endpoint
    ) 



def create_session(display_name, description):
    # create session
    create_session_response = genai_agent_runtime_client.create_session(
        agent_endpoint_id=agent_endpoint_id,    
        create_session_details=CreateSessionDetails(
            display_name = display_name,
            description = description
        )
    )

    session_id = create_session_response.data.id
    print("Agent create a session: ",session_id)
    return session_id

## Create fastapi app
app = FastAPI(title="AG-UI Endpoint")

@app.post("/")
async def agentic_chat_endpoint(input_data: RunAgentInput, request: Request):
    """Agentic chat endpoint"""
    accept_header = request.headers.get("accept")

    # Create an event encoder to properly format SSE events
    encoder = EventEncoder(accept=accept_header)
    
    for message in input_data.messages:
        if message.role == "user":
            user_message = message.content

    return StreamingResponse(
        reponse_loop(user_message, encoder,input_data),
        media_type=encoder.get_content_type()
    )


async def reponse_loop(user_message, encoder,input_data):
    # send message start
    message_id = str(uuid.uuid4())
    # Send run started event
    event = RunStartedEvent(
        type=EventType.RUN_STARTED,
        thread_id=input_data.thread_id,
        run_id=input_data.run_id
        )
    yield encoder.encode(event)

    if input_data.state.get("session_id"):
        session_id = input_data.state.get("session_id")
    else:
        session_id = create_session("lvp", "experimenting with the rag agent")


    # # Send initial state snapshot
    state = {
        "session_id": session_id,
        "steps": [
            {   
                "key":"",
                "status": "pending",
                "tag": "Planning",
                "traceDetails": [
                    {"key":"input","value": user_message}
                ]
            }
            ]
            }
    event = StateSnapshotEvent(
        type=EventType.STATE_SNAPSHOT,
        snapshot=state
        )
    yield encoder.encode(event)

    previous_state = None
    is_finish = False
    tool_performed_actions = []
    # loop until finish
    while not is_finish:
        print("\n\nCALL API: ",user_message)
        response = await get_response(genai_agent_runtime_client,
                                    user_message,
                                    session_id,
                                    streaming=True,
                                    performed_actions=tool_performed_actions
                                    )
        print(response.request.body)

        async for chunk in event_generator(encoder, response,input_data,message_id,state,previous_state):
            if isinstance(chunk,dict):
                if chunk.get("required_actions"):
                    tool_performed_actions = [chunk.get("required_actions")]
                elif chunk.get("run_finished"):
                    is_finish = True
            else:
                yield chunk

    # Send run finished event
    event = RunFinishedEvent(
        type=EventType.RUN_FINISHED,
        thread_id=input_data.thread_id,
        run_id=input_data.run_id
        )
    yield encoder.encode(event)
        

async def get_response(generative_ai_agent_runtime_client, user_message, session_id, streaming=True,performed_actions=None):
    chat_details = ChatDetails(
        user_message=user_message,
        session_id=session_id,
        should_stream = streaming
        )

    if performed_actions:
        chat_details.performed_actions = performed_actions
        
    response = generative_ai_agent_runtime_client.chat(
        agent_endpoint_id=agent_endpoint_id,
        chat_details=chat_details
        )
    
    if not streaming:
        #print(str(response.data))
        response = response.data.message.content.text
        return response
    else:
        return response

async def event_generator(encoder, response,input_data,message_id,state,previous_state):
    for event in response.data.events():
        try:
            data = json.loads(event.data)
            print("-"*22,"\n",data)            
        except:
            print(event.data)
            raise
        # process trace
        if data.get("traces"):
            for trace in data.get("traces"):
                timeFinished = trace.get("timeFinished",0)
                timeCreated = trace.get("timeCreated",1000)
                elapsedTime = round((timeFinished - timeCreated)/1000,2)
                trace_step = {
                            "traceType": trace.get("traceType"),
                            "key": trace.get("key",""),
                            "parentKey": trace.get("parentKey",""),
                            "timeCreated": timeCreated,
                            "timeFinished": timeFinished,
                            "elapsedTime": elapsedTime,
                            "status": "completed",
                            "traceDetails":[]
                        }

                if trace.get("usage"):
                    usage = trace.get("usage")[0]
                    trace_step["usage"] = {
                            "modelName": usage.get("modelDetails",{}).get("modelName"),                            
                            "inputTokenCount": usage.get("usageDetails",{}).get("inputTokenCount"),
                            "outputTokenCount": usage.get("usageDetails",{}).get("outputTokenCount"),
                            "inputCharCount": usage.get("usageDetails",{}).get("inputCharCount"),
                            "outputCharCount": usage.get("usageDetails",{}).get("outputCharCount")
                        }

                if trace.get("traceType") == "PLANNING_TRACE":
                    trace_step["tag"] = "Planning"
                    trace_step["traceDetails"] = [
                        {"key":"input","value": trace.get("input","").encode('utf-8').decode('unicode_escape')},
                        {"key":"output","value": trace.get("output","").encode('utf-8').decode('unicode_escape')}
                    ]

                    # update first step
                    if len(state["steps"]) == 1 and state["steps"][0]["status"] == "pending":
                        state["steps"] = []                        
                    
                elif trace.get("traceType") == "TOOL_INVOCATION_TRACE":
                    trace_step["tag"] = "Tool Invocation"
                    trace_step["traceDetails"] = [
                        {"key":"tool_id","value": trace.get("toolId")},
                        {"key":"tool_name","value": trace.get("toolName")},
                        {"key":"invocation_details","value": to_text(trace.get("invocationDetails"))}
                    ]

                elif trace.get("traceType") == "RETRIEVAL_TRACE":
                    trace_step["tag"] = "Retrieval"
                    trace_step["traceDetails"] = [
                        {"key":"retrievalInput","value": trace.get("retrievalInput")},
                        {"key":"citations","value": to_text(trace.get("citations"))}
                    ]
                    
                elif trace.get("traceType") == "GENERATION_TRACE":
                    trace_step["tag"] = "Generation"
                    trace_step["traceDetails"] = [
                        {"key":"input","value": trace.get("input")},
                        {"key":"generation","value": trace.get("generation")}
                    ]
                    
                elif trace.get("traceType") == "EXECUTION_TRACE":
                    trace_step["tag"] = "Execution"
                    trace_step["traceDetails"] = [
                        {"key":"input","value": trace.get("input")},
                        {"key":"output","value": trace.get("output")}
                    ]
                    
                elif trace.get("traceType") == "ERROR_TRACE":
                    trace_step["tag"] = "Error"
                    trace_step["traceDetails"] = [
                        {"key":"error_message","value": trace.get("errorMessage")},
                        {"key":"code","value": trace.get("code")}
                    ]
                else:
                    trace_step["tag"] = trace.get("traceType")
                    trace_step["traceDetails"] = [
                        {"key":"traceType","value": trace.get("traceType")}
                    ]
                # append trace step to state and yield state events
                state["steps"].append(trace_step)
                yield send_state_events(previous_state, state, encoder)
                previous_state = copy.deepcopy(state)

        # Function call 
        elif data.get("requiredActions"):
            requiredActions = data["requiredActions"]
            tool_performed_actions = []
            for each in requiredActions:
                actionId = each["actionId"]
                functionCall = each["functionCall"]
                function_name = functionCall["name"]
                function_arguments = json.loads(functionCall["arguments"])
                print("function call: ",actionId, function_name, function_arguments)
                step = {
                        "key": actionId,
                        "tag": "Function Call",
                        "status": "pending",
                        "traceDetails": [
                            {"key":"function_name","value": to_text(function_name)},
                            {"key":"function_arguments","value": "{}" if not function_arguments else to_text(function_arguments)}
                        ]
                    }
                # append trace step to state and yield state events
                state["steps"].append(step)
                yield send_state_events(previous_state, state, encoder)
                previous_state = copy.deepcopy(state)

                # perform function call
                function_call_output = AGENT_TOOLS[function_name](**function_arguments)
                print("function call output: ",function_call_output)

                # update last step by key
                for step in state["steps"]:
                    if step["key"] == actionId:
                        step["status"] = "completed"
                        step["traceDetails"].append(
                            {"key":"function_result","value": to_text(function_call_output)}
                        )
                        break
                # yield state events
                yield send_state_events(previous_state, state, encoder)
                previous_state = copy.deepcopy(state)

                performed_action = FunctionCallingPerformedAction(
                        action_id = actionId,
                        performed_action_type = "FUNCTION_CALLING_PERFORMED_ACTION",
                        function_call_output = to_text(function_call_output)
                    )
                yield {"required_actions": performed_action}
        
        # Display answer
        elif data.get('message'):
            content = data['message']["content"]
            text = content["text"]

            event = TextMessageStartEvent(
                type=EventType.TEXT_MESSAGE_START,
                message_id=message_id,
                role="assistant"
            )
            yield encoder.encode(event)

            event = TextMessageContentEvent(
                type=EventType.TEXT_MESSAGE_CONTENT,
                message_id=message_id,
                delta=text
            )
            yield encoder.encode(event)

            # send message end
            event = TextMessageEndEvent(
                type=EventType.TEXT_MESSAGE_END,
                message_id=message_id
            )
            yield encoder.encode(event)

            yield {"run_finished": True}



def send_state_events(previous_state, state, encoder):
    """Send state events with snapshots and deltas"""
    # print("="*20,"state:\n",state)
    # Generate JSON patch from previous state to current state
    patch = jsonpatch.make_patch(previous_state, state)
    print("patch ","*"*20,"\n",patch.patch,"\npatch ","*"*20)
    event = StateDeltaEvent(
        type=EventType.STATE_DELTA,
        delta=patch.patch
    )
    # print("event:::::::::",event)
    return encoder.encode(event)

async def send_tool_result_message_events():
    """Send message for tool result"""
    message_id = str(uuid.uuid4())

    # Start of message
    yield TextMessageStartEvent(
        type=EventType.TEXT_MESSAGE_START, message_id=message_id, role="assistant"
    )

    # Content
    yield TextMessageContentEvent(
        type=EventType.TEXT_MESSAGE_CONTENT,
        message_id=message_id,
        delta="Retrieved weather information!",
    )

    # End of message
    yield TextMessageEndEvent(type=EventType.TEXT_MESSAGE_END, message_id=message_id)

def to_text(data: dict | str | list | int | float | bool) -> str:
    if isinstance(data, (dict, list)):
        try:
            return json.dumps(data,ensure_ascii=False)
        except:
            return str(data)
    elif isinstance(data, (int, float, bool)):
        return str(data)
    elif isinstance(data, str) and data.strip().startswith("{"):
        try:
            return json.dumps(json.loads(data),ensure_ascii=False)
        except:
            return data
    else:
        return str(data)

    
if __name__ == "__main__":
    # run the app
    import uvicorn
    port = int(os.getenv("PORT", "8008"))
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=True
        )
