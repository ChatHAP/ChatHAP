from dataclasses import dataclass
from enum import Enum
import json
import logging
import os
import random
import re
import time
from typing import Literal, Optional, Sequence, Union
import numpy as np
from numpy.typing import NDArray
import tiktoken
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field, ValidationError
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI


from app.genSignal import GAIN, AmplitudeEnvelopeType, GenSignalInput
from app.appmode import CH_DISABLE_OPENAI

from langchain_core.runnables import RunnableSerializable

logger = logging.getLogger("ChatHAP")


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY is None:
    raise ValueError("Please set the `OPENAI_API_KEY` environment variable or create a .env file with the API key.")



# llama_model = ChatOpenAI(
#     # use llama server on localhost
#     base_url="http://127.0.0.1:8080/v1",
#     # base_url="http://localhost:8000/v1",
#     temperature=0,
# )
gpt4_model = ChatOpenAI(
    api_key=OPENAI_API_KEY,  # type: ignore
    model="gpt-4-turbo-2024-04-09",
    temperature=0,
)

claude_model = ChatAnthropic(
    model='claude-3-5-sonnet-20240620', # type: ignore
    temperature=0,
) # type: ignore
# gemini_model = ChatGoogleGenerativeAI(
#     model="gemini-1.5-pro",
#     temperature=0,
# )

default_llm_model = gpt4_model

@dataclass
class LLMChains:
    base_chain: RunnableSerializable
    nav_chain: RunnableSerializable
default_chains: LLMChains = LLMChains(None, None) # type: ignore

class GenChangeDirection(Enum):
    """Directions for changing generation parameters."""
    NONE = "NONE"
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"

class SignalFeature(Enum):
    """Features of a vibration signal."""
    ROUGHNESS = "Roughness"
    VALENCE = "Pleasant or Positive"
    AROUSAL = "Exciting or Urgent"
    A = "Amplitude"
    A_W_option = "Whole Amplitude Envelope"
    A_E_option = "Each Amplitude Envelope"
    freq_c = "Carrier Frequency"
    freq_e = "Envelope Frequency"
    dur = "Duration"
    rhythm = "Rhythm"

class SignalParameter(Enum):
    """Parameters for generating vibration signal."""
    A = "Amplitude"
    A_W_option = "Whole Amplitude Envelope"
    A_E_option = "Each Amplitude Envelope"
    freq_c = "Carrier Frequency"
    freq_e = "Envelope Frequency"
    dur = "Duration"
    rhythm = "Rhythm"

class GenChangeSummary(BaseModel):
    """Change summary of generation parameters for the signal."""
    target_feature: SignalFeature = Field(description="Feature to change in the signal.")
    selected_parameter: SignalParameter = Field(description="Selected parameter to change.")
    changed_parameter_direction: GenChangeDirection = Field(description="Direction of the change in the selected parameter.")

class GenerationApproach(BaseModel):
    """Approach for generating vibrations."""
    approach_type: Literal['GenerationApproach']
    generation_parameters: GenSignalInput = Field(description="Generation parameters for the signal if using generation approach.")
    generation_change: Optional[GenChangeSummary] = Field(description="Summary of change in generation parameters for the feature of the signal if using generation approach.")

class NavigationApproach(BaseModel):
    """Approach for navigating vibrations."""
    approach_type: Literal['NavigationApproach']
    natural_language_search_query: str = Field(description="Natural language search query for navigating vibrations, will be pased to LLM.")

class ModifyApproach(BaseModel):
    """Approach for modifying vibrations."""
    approach_type: Literal['ModifyApproach']
    change_amplitude_factor: Optional[float] = Field(None, description="Change the amplitude of the signal by a factor.")
    time_stretch_factor: Optional[float] = Field(None, description="Time stretch factor for the signal.")
    truncate_or_extend_signal_factor: Optional[float] = Field(None, description="Truncate or extend the signal by a factor.")
    reverse_signal: Optional[bool] = Field(None, description="Reverse the signal.")

# might be better to use tool api (see around https://python.langchain.com/v0.2/docs/how_to/tool_calling/#passing-tool-outputs-to-the-model)
class LLMResponse(BaseModel):
    """ChatHAP assistant response to messages."""
    response_msg: Optional[str] = Field(None, description="This message is used to show information to the user before any approaches are taken.")
    approach: Optional[Union[GenerationApproach, NavigationApproach, ModifyApproach]] = Field(None, description="Approach for generating vibrations.", discriminator='approach_type')


base_prompt = ChatPromptTemplate.from_messages(
    [
        (
			"system",
            """
            You are a helpful assistant who helps users create custom vibrations. Use one of three primary approaches based on user input: NavigationApproach, GenerationApproach, or ModifyApproach.

            1. **Navigating Descriptions (NavigationApproach)**:
            - Use this approach if users describe vibrations using physical, sensory, emotional, or metaphoric words, or usage examples.
            - Select NavigationApproach and provide the `natural_language_search_query` to navigate the vibrations using an LLM search.
            - Provide the user with a message showing and explaining your search query.

            2. **Designing Vibrations Systematically (GenerationApproach)**:
            - Use this approach if users mention specific vibration parameters such as frequency or envelope frequency, number of pulses, or duration.
            - Provide `generation_parameters` and ensure `generation_change` is None initially.
            - For further changes, provide the adjusted `generation_parameters`, and fill `generation_change` appropriately to explain the adjustments.
                - Tips for adjusting `generation_parameters` to change features:
                    - For pleasant or positive feelings (opposite side of unpleasant or negative feelings), decrease "Amplitude" or "Rhythm".
                    - For exciting or urgent feelings (opposite side of calm feelings), increase "Amplitude" or "Duration".
                    - For rough sensations (opposite side of smooth sensations), increase "Amplitude" or "Duration".
            - Provide the user with a message explaining the generation parameters and changes made if any.

            3. **Modifying Vibrations (ModifyApproach)**:
            - Use this approach after navigating or generating vibrations to modify the last vibration. For example:
                - Change the intensity/amplitude of the signal by a factor (greater than 1.0 to increase, less than 1.0 to decrease).
                - Change speed/tempo the signal by a factor with time stretch (greater than 1.0 to slow down, less than 1.0 to speed up).
                - Truncate or extend (by looping) the duration of the signal by a factor (greater than 1.0 to extend, less than 1.0 to shorten).
                - Flip or Reverse the signal (set reverse_signal to True).
                Examples:
                    User: "Can you make the vibration stronger?"
                    Response: change_amplitude_factor = 1.5

                    User: "This vibration is too weak."
                    Response: change_amplitude_factor = 1.8

                    User: "Can you reduce the vibration a bit?"
                    Response: change_amplitude_factor = 0.6

                    User: "The vibration is too intense."
                    Response: change_amplitude_factor = 0.4

                    User: "Can you make the vibration slower?"
                    Response: time_stretch_factor = 1.3

                    User: "This vibration's tempo is too fast."
                    Response: time_stretch_factor = 1.5

                    User: "Can you extend the duration of the vibration two times?"
                    Response: time_stretch_factor = 2.0

                    User: "Can you speed up the vibration?"
                    Response: time_stretch_factor = 0.7

                    User: "Can you reduce the duration of the vibration a bit?"
                    Response: time_stretch_factor = 0.8

                    User: "Can you just use the first half of the vibration?"
                    Response: truncate_or_extend_signal_factor = 0.5

                    User: "Can you cut off the last quarter of the vibration?"
                    Response: truncate_or_extend_signal_factor = 0.75

                    User: "Can you loop the vibration?"
                    Response: truncate_or_extend_signal_factor = 2.0

                    User: "Can you loop the vibration 4 times?"
                    Response: truncate_or_extend_signal_factor = 4.0

            Choose the appropriate approach based on the user's input and provide a response message explaining your choice and any changes made.
            Please make sure to always output the approach.approach_type discriminator.
            """
        ),
		# ("human", "{input}")
        ("placeholder", "{conversation}")
	]
)

def chat_chatgpt(conversation: Sequence[BaseMessage], llmchains: LLMChains = default_chains) -> LLMResponse:
    try:
        response = llmchains.base_chain.invoke({
            "conversation": conversation
        })
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise
    return response  # type: ignore

    # # Count tokens
    # encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    # tags_token_count = len(encoding.encode(msg))
    # logger.debug(f"Number of tokens in msg: {tags_token_count}")



class NavResponseResource(BaseModel):
    """Resource selected from the TAG_LIST with reasons."""
    resource: str = Field(..., description="The selected resource from the TAG_LIST.")
    reason: str = Field(..., description="Reason for selecting the resource.")

class NavResponseFeature(BaseModel):
    """Feature for selecting the resource."""
    feature: str = Field(..., description="Feature for selecting the resource.")
    importance: float = Field(..., description="Importance rate of the feature.")

class LLMNavResponse(BaseModel):
    """Navigation response containing the selected resource, features, and reasons."""
    resources: list[NavResponseResource] = Field(..., description="Selected resources from the TAG_LIST and reasons for selection.")
    features: list[NavResponseFeature] = Field(..., description="Features for selecting the resources and their importance rates.")

nav_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are a helpful assistant who navigates users through descriptions for vibrations in a library.
            You must provide selections in the specified format.
            If you can extract physical, sensory, emotional, metaphoric words, or usage examples that describe a vibration that users want to find, provide the corresponding vibrations ("resources") from the following \'TAG_LIST\'.
            You are recommended to provide multiple "resources" (at least two "resources" if possible).
            You must also provide "features" (from words or tags in the TAG_LIST; e.g., "tapping", "regular", or "slow") explaining why you selected the "resources".
            You must also provide "importance", which is the importance rate (between 0 and 1) of each feature in "features".
            For each resource, you must provide the corresponding reason why you selected it.
            If there is no appropriate resource, provide empty lists.
            """
        ),
        ("system", "TAG_LIST: {tag_list}"),
        ("human", "{input_query}"),
        # ("placeholder", "{conversation}")
    ]
)

def nav_chatgpt(input_query: str, tag_list: str, llmchains: LLMChains = default_chains) -> LLMNavResponse:
    response = llmchains.nav_chain.invoke({
        "input_query": input_query,
        "tag_list": tag_list
    })

    return response # type: ignore


default_chains = LLMChains(
    base_chain = base_prompt | default_llm_model.with_structured_output(LLMResponse),
    nav_chain = nav_prompt | default_llm_model.with_structured_output(LLMNavResponse),
)


def llmtests(llmchains: LLMChains = default_chains):
    start_time = time.time()
    test_conversation: list[BaseMessage] = [ HumanMessage(content="Please generate a signal with 3 pulses and a duration of 2 seconds."), ]
    response = chat_chatgpt(test_conversation, llmchains=llmchains)
    assert response.approach is not None and response.approach.approach_type == "GenerationApproach" and response.approach.generation_parameters.rhythm == 3 and response.approach.generation_parameters.dur == 2, response


    # Create tests based on warmup tasks
    # (3) Warm-up tasks (15 minutes)
    #     • Create a vibration appropriate for these requirements:
    #     (I-a) A 4-second vibration with continuous amplitude. The whole amplitude is increasing and then decreasing.
    #     (I-b) Set a frequency is at 100Hz.
    #     (I-c) Change the frequency to 200Hz.
    test_conversation = [ HumanMessage(content="Please generate A 4-second vibration with continuous amplitude. The whole amplitude is increasing and then decreasing."), ]
    response = chat_chatgpt(test_conversation, llmchains=llmchains)
    assert response.approach is not None and response.approach.approach_type == "GenerationApproach" and response.approach.generation_parameters.dur == 4 and response.approach.generation_parameters.A_E_option == AmplitudeEnvelopeType.CONTINUOUS and response.approach.generation_parameters.A_W_option == AmplitudeEnvelopeType.INCREASE_DECREASE, response

    if response.response_msg:
        test_conversation.append(AIMessage(content=response.response_msg))
    test_conversation.append(HumanMessage(content="Please set the frequency to 100Hz."))
    response = chat_chatgpt(test_conversation, llmchains=llmchains)
    assert response.approach is not None and response.approach.approach_type == "GenerationApproach" and response.approach.generation_parameters.freq_c == 100 and response.approach.generation_parameters.dur == 4 and response.approach.generation_parameters.A_E_option == AmplitudeEnvelopeType.CONTINUOUS and response.approach.generation_parameters.A_W_option == AmplitudeEnvelopeType.INCREASE_DECREASE, response

    if response.response_msg:
        test_conversation.append(AIMessage(content=response.response_msg))
    test_conversation.append(HumanMessage(content="Please change the frequency to 200Hz."))
    response = chat_chatgpt(test_conversation, llmchains=llmchains)
    assert response.approach is not None and response.approach.approach_type == "GenerationApproach" and response.approach.generation_parameters.freq_c == 200 and response.approach.generation_parameters.dur == 4 and response.approach.generation_parameters.A_E_option == AmplitudeEnvelopeType.CONTINUOUS and response.approach.generation_parameters.A_W_option == AmplitudeEnvelopeType.INCREASE_DECREASE, response


    # (2-a) A 2-second vibration with 4 pulses. The pulses' envelope should be ramp-up.
    # (2-b) Make the vibration feel stronger.
    # (2-c) Make the vibration's tempo faster.
    test_conversation = [ HumanMessage(content="Please generate a 2-second vibration with 4 pulses. The pulses' envelope should be ramp-up."), ]
    response = chat_chatgpt(test_conversation, llmchains=llmchains)
    assert response.approach is not None and response.approach.approach_type == "GenerationApproach" and response.approach.generation_parameters.dur == 2 and response.approach.generation_parameters.rhythm == 4 and response.approach.generation_parameters.A_E_option == AmplitudeEnvelopeType.INCREASE, response

    if response.response_msg:
        test_conversation.append(AIMessage(content=response.response_msg))
    test_conversation.append(HumanMessage(content="Please make the vibration feel stronger."))
    response = chat_chatgpt(test_conversation, llmchains=llmchains)
    assert response.approach is not None and response.approach.approach_type == "ModifyApproach" and response.approach.change_amplitude_factor is not None and response.approach.change_amplitude_factor > 1, response

    if response.response_msg:
        test_conversation.append(AIMessage(content=response.response_msg))
    test_conversation.append(HumanMessage(content="Please make the vibration's tempo faster."))
    response = chat_chatgpt(test_conversation, llmchains=llmchains)
    assert response.approach is not None and response.approach.approach_type == "ModifyApproach" and response.approach.time_stretch_factor is not None and response.approach.time_stretch_factor < 1, response

    # (3-a) Create a vibration that mimics the sensation of walking.
    # (3-b) Loop the vibration 2 times.
    # (3-c) Truncate the last third of the vibration.
    test_conversation = [ HumanMessage(content="Please create a vibration that mimics the sensation of walking."), ]
    response = chat_chatgpt(test_conversation, llmchains=llmchains)
    assert response.approach is not None and response.approach.approach_type == "NavigationApproach" and len(response.approach.natural_language_search_query) > 6, response

    if response.response_msg:
        test_conversation.append(AIMessage(content=response.response_msg))
    test_conversation.append(HumanMessage(content="Loop the vibration 2 times."))
    response = chat_chatgpt(test_conversation, llmchains=llmchains)
    assert response.approach is not None and response.approach.approach_type == "ModifyApproach" and response.approach.truncate_or_extend_signal_factor == 2, response

    if response.response_msg:
        test_conversation.append(AIMessage(content=response.response_msg))
    test_conversation.append(HumanMessage(content="Truncate the last third of the vibration."))
    response = chat_chatgpt(test_conversation, llmchains=llmchains)
    assert response.approach is not None and response.approach.approach_type == "ModifyApproach" and response.approach.truncate_or_extend_signal_factor is not None and abs(response.approach.truncate_or_extend_signal_factor - 0.66) < 0.015, response

    end_time = time.time()

    bm = llmchains.base_chain.middle[0].bound # type: ignore
    print(f"Tests passed for {bm.model_name if isinstance(bm, ChatOpenAI) else bm.model} in {end_time - start_time:.2f} seconds.")


if __name__ == "__main__":
    # Test LLM output for GenerationApproach style prompt
    claude_chains = LLMChains(
        base_chain = base_prompt | claude_model.with_structured_output(LLMResponse),
        nav_chain = nav_prompt | claude_model.with_structured_output(LLMNavResponse),
    )
    print("Starting tests...")
    for i in range(5):
        llmtests(default_chains) # gpt4_model
        llmtests(claude_chains)


