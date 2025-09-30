# Databricks notebook source
# MAGIC %md
# MAGIC #Tool-calling Agent
# MAGIC
# MAGIC This is an auto-generated notebook created by an AI playground export. In this notebook, you will:
# MAGIC - Author a tool-calling [MLflow's `ResponsesAgent`](https://mlflow.org/docs/latest/api_reference/python_api/mlflow.pyfunc.html#mlflow.pyfunc.ResponsesAgent) that uses the OpenAI client
# MAGIC - Manually test the agent's output
# MAGIC - Evaluate the agent with Mosaic AI Agent Evaluation
# MAGIC - Log and deploy the agent
# MAGIC
# MAGIC This notebook should be run on serverless or a cluster with DBR<17.
# MAGIC
# MAGIC  **_NOTE:_**  This notebook uses the OpenAI SDK, but AI Agent Framework is compatible with any agent authoring framework, including LlamaIndex or LangGraph. To learn more, see the [Authoring Agents](https://docs.databricks.com/generative-ai/agent-framework/author-agent) Databricks documentation.
# MAGIC
# MAGIC ## Prerequisites
# MAGIC
# MAGIC - Address all `TODO`s in this notebook.

# COMMAND ----------

# MAGIC %pip install -U -qqqq backoff databricks-openai uv databricks-agents mlflow-skinny[databricks]
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md ## Define the agent in code
# MAGIC Below we define our agent code in a single cell, enabling us to easily write it to a local Python file for subsequent logging and deployment using the `%%writefile` magic command.
# MAGIC
# MAGIC For more examples of tools to add to your agent, see [docs](https://docs.databricks.com/generative-ai/agent-framework/agent-tool.html).

# COMMAND ----------

# MAGIC %%writefile agent.py
# MAGIC import json
# MAGIC from typing import Any, Callable, Generator, Optional
# MAGIC from uuid import uuid4
# MAGIC import warnings
# MAGIC
# MAGIC import backoff
# MAGIC import mlflow
# MAGIC import openai
# MAGIC from databricks.sdk import WorkspaceClient
# MAGIC from databricks_openai import UCFunctionToolkit, VectorSearchRetrieverTool
# MAGIC from mlflow.entities import SpanType
# MAGIC from mlflow.pyfunc import ResponsesAgent
# MAGIC from mlflow.types.responses import (
# MAGIC     ResponsesAgentRequest,
# MAGIC     ResponsesAgentResponse,
# MAGIC     ResponsesAgentStreamEvent,
# MAGIC )
# MAGIC from openai import OpenAI
# MAGIC from pydantic import BaseModel
# MAGIC from unitycatalog.ai.core.base import get_uc_function_client
# MAGIC
# MAGIC ############################################
# MAGIC # Define your LLM endpoint and system prompt
# MAGIC ############################################
# MAGIC LLM_ENDPOINT_NAME = "databricks-claude-sonnet-4"
# MAGIC
# MAGIC SYSTEM_PROMPT = """You are an expert Relationship Manager at an Indian bank, and know your customers well. Provide them with the right guidance
# MAGIC """
# MAGIC
# MAGIC
# MAGIC ###############################################################################
# MAGIC ## Define tools for your agent, enabling it to retrieve data or take actions
# MAGIC ## beyond text generation
# MAGIC ## To create and see usage examples of more tools, see
# MAGIC ## https://docs.databricks.com/generative-ai/agent-framework/agent-tool.html
# MAGIC ###############################################################################
# MAGIC class ToolInfo(BaseModel):
# MAGIC     """
# MAGIC     Class representing a tool for the agent.
# MAGIC     - "name" (str): The name of the tool.
# MAGIC     - "spec" (dict): JSON description of the tool (matches OpenAI Responses format)
# MAGIC     - "exec_fn" (Callable): Function that implements the tool logic
# MAGIC     """
# MAGIC
# MAGIC     name: str
# MAGIC     spec: dict
# MAGIC     exec_fn: Callable
# MAGIC
# MAGIC
# MAGIC def create_tool_info(tool_spec, exec_fn_param: Optional[Callable] = None):
# MAGIC     tool_spec["function"].pop("strict", None)
# MAGIC     tool_name = tool_spec["function"]["name"]
# MAGIC     udf_name = tool_name.replace("__", ".")
# MAGIC
# MAGIC     # Define a wrapper that accepts kwargs for the UC tool call,
# MAGIC     # then passes them to the UC tool execution client
# MAGIC     def exec_fn(**kwargs):
# MAGIC         function_result = uc_function_client.execute_function(udf_name, kwargs)
# MAGIC         if function_result.error is not None:
# MAGIC             return function_result.error
# MAGIC         else:
# MAGIC             return function_result.value
# MAGIC     return ToolInfo(name=tool_name, spec=tool_spec, exec_fn=exec_fn_param or exec_fn)
# MAGIC
# MAGIC
# MAGIC TOOL_INFOS = []
# MAGIC
# MAGIC # You can use UDFs in Unity Catalog as agent tools
# MAGIC # TODO: Add additional tools
# MAGIC UC_TOOL_NAMES = ["demo_soumyashree_patra.test_genie_integration._genie_query", "demo_soumyashree_patra.bharat_bank_rm._lookup_customer_info", "demo_soumyashree_patra.bharat_bank_rm._genie_wrapper"]
# MAGIC
# MAGIC uc_toolkit = UCFunctionToolkit(function_names=UC_TOOL_NAMES)
# MAGIC uc_function_client = get_uc_function_client()
# MAGIC for tool_spec in uc_toolkit.tools:
# MAGIC     TOOL_INFOS.append(create_tool_info(tool_spec))
# MAGIC
# MAGIC
# MAGIC # Use Databricks vector search indexes as tools
# MAGIC # See [docs](https://docs.databricks.com/generative-ai/agent-framework/unstructured-retrieval-tools.html) for details
# MAGIC
# MAGIC # # (Optional) Use Databricks vector search indexes as tools
# MAGIC # # See https://docs.databricks.com/generative-ai/agent-framework/unstructured-retrieval-tools.html
# MAGIC # # for details
# MAGIC VECTOR_SEARCH_TOOLS = []
# MAGIC # # TODO: Add vector search indexes as tools or delete this block
# MAGIC # VECTOR_SEARCH_TOOLS.append(
# MAGIC #         VectorSearchRetrieverTool(
# MAGIC #         index_name="",
# MAGIC #         # filters="..."
# MAGIC #     )
# MAGIC # )
# MAGIC for vs_tool in VECTOR_SEARCH_TOOLS:
# MAGIC     TOOL_INFOS.append(create_tool_info(vs_tool.tool, vs_tool.execute))
# MAGIC
# MAGIC
# MAGIC
# MAGIC class ToolCallingAgent(ResponsesAgent):
# MAGIC     """
# MAGIC     Class representing a tool-calling Agent
# MAGIC     """
# MAGIC
# MAGIC     def __init__(self, llm_endpoint: str, tools: list[ToolInfo]):
# MAGIC         """Initializes the ToolCallingAgent with tools."""
# MAGIC         self.llm_endpoint = llm_endpoint
# MAGIC         self.workspace_client = WorkspaceClient()
# MAGIC         self.model_serving_client: OpenAI = (
# MAGIC             self.workspace_client.serving_endpoints.get_open_ai_client()
# MAGIC         )
# MAGIC         self._tools_dict = {tool.name: tool for tool in tools}
# MAGIC
# MAGIC     def get_tool_specs(self) -> list[dict]:
# MAGIC         """Returns tool specifications in the format OpenAI expects."""
# MAGIC         return [tool_info.spec for tool_info in self._tools_dict.values()]
# MAGIC
# MAGIC     @mlflow.trace(span_type=SpanType.TOOL)
# MAGIC     def execute_tool(self, tool_name: str, args: dict) -> Any:
# MAGIC         """Executes the specified tool with the given arguments."""
# MAGIC         return self._tools_dict[tool_name].exec_fn(**args)
# MAGIC
# MAGIC     def call_llm(self, messages: list[dict[str, Any]]) -> Generator[dict[str, Any], None, None]:
# MAGIC         with warnings.catch_warnings():
# MAGIC             warnings.filterwarnings("ignore", message="PydanticSerializationUnexpectedValue")
# MAGIC             for chunk in self.model_serving_client.chat.completions.create(
# MAGIC                 model=self.llm_endpoint,
# MAGIC                 messages=self.prep_msgs_for_cc_llm(messages),
# MAGIC                 tools=self.get_tool_specs(),
# MAGIC                 stream=True,
# MAGIC             ):
# MAGIC                 yield chunk.to_dict()
# MAGIC
# MAGIC     def handle_tool_call(
# MAGIC         self,
# MAGIC         tool_call: dict[str, Any],
# MAGIC         messages: list[dict[str, Any]],
# MAGIC     ) -> ResponsesAgentStreamEvent:
# MAGIC         """
# MAGIC         Execute tool calls, add them to the running message history, and return a ResponsesStreamEvent w/ tool output
# MAGIC         """
# MAGIC         args = json.loads(tool_call["arguments"])
# MAGIC         result = str(self.execute_tool(tool_name=tool_call["name"], args=args))
# MAGIC
# MAGIC         tool_call_output = self.create_function_call_output_item(tool_call["call_id"], result)
# MAGIC         messages.append(tool_call_output)
# MAGIC         return ResponsesAgentStreamEvent(type="response.output_item.done", item=tool_call_output)
# MAGIC
# MAGIC     def call_and_run_tools(
# MAGIC         self,
# MAGIC         messages: list[dict[str, Any]],
# MAGIC         max_iter: int = 10,
# MAGIC     ) -> Generator[ResponsesAgentStreamEvent, None, None]:
# MAGIC         for _ in range(max_iter):
# MAGIC             last_msg = messages[-1]
# MAGIC             if last_msg.get("role", None) == "assistant":
# MAGIC                 return
# MAGIC             elif last_msg.get("type", None) == "function_call":
# MAGIC                 yield self.handle_tool_call(last_msg, messages)
# MAGIC             else:
# MAGIC                 yield from self.output_to_responses_items_stream(
# MAGIC                     chunks=self.call_llm(messages), aggregator=messages
# MAGIC                 )
# MAGIC
# MAGIC         yield ResponsesAgentStreamEvent(
# MAGIC             type="response.output_item.done",
# MAGIC             item=self.create_text_output_item("Max iterations reached. Stopping.", str(uuid4())),
# MAGIC         )
# MAGIC
# MAGIC     def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
# MAGIC         outputs = [
# MAGIC             event.item
# MAGIC             for event in self.predict_stream(request)
# MAGIC             if event.type == "response.output_item.done"
# MAGIC         ]
# MAGIC         return ResponsesAgentResponse(output=outputs, custom_outputs=request.custom_inputs)
# MAGIC
# MAGIC     def predict_stream(
# MAGIC         self, request: ResponsesAgentRequest
# MAGIC     ) -> Generator[ResponsesAgentStreamEvent, None, None]:
# MAGIC         messages = self.prep_msgs_for_cc_llm([i.model_dump() for i in request.input])
# MAGIC         if SYSTEM_PROMPT:
# MAGIC             messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
# MAGIC         yield from self.call_and_run_tools(messages=messages)
# MAGIC
# MAGIC
# MAGIC # Log the model using MLflow
# MAGIC mlflow.openai.autolog()
# MAGIC AGENT = ToolCallingAgent(llm_endpoint=LLM_ENDPOINT_NAME, tools=TOOL_INFOS)
# MAGIC mlflow.models.set_model(AGENT)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test the agent
# MAGIC
# MAGIC Interact with the agent to test its output. Since we manually traced methods within `ResponsesAgent`, you can view the trace for each step the agent takes, with any LLM calls made via the OpenAI SDK automatically traced by autologging.
# MAGIC
# MAGIC Replace this placeholder input with an appropriate domain-specific example for your agent.

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

from agent import AGENT

AGENT.predict({"input": [{"role": "user", "content": "what is 4*3 in python"}]})

# COMMAND ----------

for chunk in AGENT.predict_stream(
    {"input": [{"role": "user", "content": "What is 4*3 in Python?"}]}
):
    print(chunk.model_dump(exclude_none=True))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Log the `agent` as an MLflow model
# MAGIC Determine Databricks resources to specify for automatic auth passthrough at deployment time
# MAGIC - **TODO**: If your Unity Catalog Function queries a [vector search index](https://docs.databricks.com/generative-ai/agent-framework/unstructured-retrieval-tools.html) or leverages [external functions](https://docs.databricks.com/generative-ai/agent-framework/external-connection-tools.html), you need to include the dependent vector search index and UC connection objects, respectively, as resources. See [docs](https://docs.databricks.com/generative-ai/agent-framework/log-agent.html#specify-resources-for-automatic-authentication-passthrough) for more details.
# MAGIC
# MAGIC Log the agent as code from the `agent.py` file. See [MLflow - Models from Code](https://mlflow.org/docs/latest/models.html#models-from-code).

# COMMAND ----------

# Determine Databricks resources to specify for automatic auth passthrough at deployment time
import mlflow
from agent import UC_TOOL_NAMES, VECTOR_SEARCH_TOOLS, LLM_ENDPOINT_NAME
from mlflow.models.resources import DatabricksFunction, DatabricksServingEndpoint
from pkg_resources import get_distribution

resources = [DatabricksServingEndpoint(endpoint_name=LLM_ENDPOINT_NAME)]
for tool in VECTOR_SEARCH_TOOLS:
    resources.extend(tool.resources)
for tool_name in UC_TOOL_NAMES:
    # TODO: If the UC function includes dependencies like external connection or vector search, please include them manually.
    # See the TODO in the markdown above for more information.    
    resources.append(DatabricksFunction(function_name=tool_name))

input_example = {
    "input": [
        {
            "role": "user",
            "content": "What is the profile of Tiya Sood?"
        }
    ]
}

with mlflow.start_run():
    logged_agent_info = mlflow.pyfunc.log_model(
        name="agent",
        python_model="agent.py",
        input_example=input_example,
        pip_requirements=[
            "databricks-openai",
            "backoff",
            f"databricks-connect=={get_distribution('databricks-connect').version}",
        ],
        resources=resources,
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Evaluate the agent with [Agent Evaluation](https://docs.databricks.com/mlflow3/genai/eval-monitor)
# MAGIC
# MAGIC You can edit the requests or expected responses in your evaluation dataset and run evaluation as you iterate your agent, leveraging mlflow to track the computed quality metrics.
# MAGIC
# MAGIC Evaluate your agent with one of our [predefined LLM scorers](https://docs.databricks.com/mlflow3/genai/eval-monitor/predefined-judge-scorers), or try adding [custom metrics](https://docs.databricks.com/mlflow3/genai/eval-monitor/custom-scorers).

# COMMAND ----------

import mlflow
from mlflow.genai.scorers import RelevanceToQuery, Safety, RetrievalRelevance, RetrievalGroundedness

eval_dataset = [
    {
        "inputs": {
            "input": [
                {
                    "role": "system",
                    "content": "You are an expert Relationship Manager at an Indian bank, and know your customers well. Provide them with the right guidance\n"
                },
                {
                    "role": "user",
                    "content": "What is the profile of Tiya Sood?"
                }
            ]
        },
        "expected_response": None
    },
    {
        "inputs": {
            "input": [
                {
                    "role": "system",
                    "content": "You are an expert Relationship Manager at an Indian bank, and know your customers well. Provide them with the right guidance\n"
                },
                {
                    "role": "user",
                    "content": "What is the profile of Tiya Sood?"
                },
                {
                    "role": "assistant",
                    "content": "The user is asking for the profile of a specific customer named Tiya Sood. I need to use the customer lookup tool to retrieve her information from the bank's customer database.\n\n<uc_function_call>{\"id\":\"yOhTiCpQY5rDNObyn3gd\",\"name\":\"demo_soumyashree_patra.bharat_bank_rm._lookup_customer_info\",\"arguments\":\"{\\\"customer_name\\\":\\\"Tiya Sood\\\"}\"}</uc_function_call>\n\n<uc_function_result>{\"id\":\"yOhTiCpQY5rDNObyn3gd\",\"content\":\"{\\\"is_truncated\\\":false,\\\"columns\\\":[\\\"output\\\"],\\\"rows\\\":[[\\\"Customer ID: 84, Customer Name: Tiya Sood, Product Type:Mutual Fund, Product Sub Type: Distinctio\\\"]]}\"}</uc_function_result>\n\nI need to get comprehensive profile information for Tiya Sood. The lookup function only provided basic product information, so I'll use the Genie wrapper to get detailed customer profile including account balances, KYC status, digital usage, and risk profile.\n\n<uc_function_call>{\"id\":\"bAxo7QNZPyLcDmFQJXuj\",\"name\":\"demo_soumyashree_patra.bharat_bank_rm._genie_wrapper\",\"arguments\":\"{\\\"question\\\":\\\"Can you provide detailed profile information for Tiya Sood including her account balances, KYC details, digital app usage, and risk profile?\\\",\\\"contextual_history\\\":\\\"Customer ID: 84, Customer Name: Tiya Sood, Product Type: Mutual Fund, Product Sub Type: Distinctio\\\"}\"}</uc_function_call>\n\n<uc_function_result>{\"id\":\"bAxo7QNZPyLcDmFQJXuj\",\"content\":\"{\\\"is_truncated\\\":false,\\\"columns\\\":[\\\"output\\\"],\\\"rows\\\":[[\\\"Genie Results are: \\\\nSpace ID: 01f07f96a2711ec2a3d678153974f002\\\\nConversation ID: 01f09e29919b1b4f9bc085ce9fd79ee4\\\\nQuestion That Was Asked: Use the contextual history to answer the question. The history may or may not help you. Use it if you find it relevant.\\\\n        \\\\n        Contextual History: Customer ID: 84, Customer Name: Tiya Sood, Product Type: Mutual Fund, Product Sub Type: Distinctio\\\\n        \\\\n        Question to answer: Can you provide detailed profile information for Tiya Sood including her account balances, KYC details, digital app usage, and risk profile?\\\\n        \\\\nContent: None\\\\nSQL Query: SELECT `customer_master`.`CustomerID` AS `Customer ID`, `customer_master`.`Name` AS `Customer Name`, `customer_master`.`DOB` AS `Date of Birth`, `customer_master`.`PAN` AS `PAN Number`, `customer_master`.`Aadhaar` AS `Aadhaar Number`, `customer_master`.`Segment` AS `Customer Segment`, `customer_master`.`Branch` AS `Branch`, `customer_master`.`RelationshipStartDate` AS `Relationship Start Date`, `portfolio`.`ProductType` AS `Product Type`, `portfolio`.`Value` AS `Account Balance`, `risk_compliance`.`RiskScore` AS `Risk Score`, `risk_compliance`.`KYCExpiry` AS `KYC Expiry Date`, `risk_compliance`.`Alert` AS `Alert`, `digital_engagement`.`MonthlyLogins` AS `Monthly Logins`, `digital_engagement`.`LastLoginDate` AS `Last Login Date`, `digital_engagement`.`Device` AS `Device Used`, `digital_engagement`.`PreferredChannel` AS `Preferred Channel`, `digital_engagement`.`EngagementScore` AS `Engagement Score` FROM `demo_soumyashree_patra`.`bharat_bank_rm`.`customer_master` JOIN `demo_soumyashree_patra`.`bharat_bank_rm`.`portfolio` ON `customer_master`.`CustomerID` = `portfolio`.`CustomerID` JOIN `demo_soumyashree_patra`.`bharat_bank_rm`.`risk_compliance` ON `customer_master`.`CustomerID` = `risk_compliance`.`CustomerID` JOIN `demo_soumyashree_patra`.`bharat_bank_rm`.`digital_engagement` ON `customer_master`.`CustomerID` = `digital_engagement`.`CustomerID` WHERE `customer_master`.`Name` = 'Tiya Sood'\\\\nSQL Query Description: You want to see a detailed profile for Tiya Sood, including her personal information, account balances, KYC details, digital app usage, and risk profile.\\\\nSQL Query Result: [{'Customer ID': 84, 'Customer Name': 'Tiya Sood', 'Date of Birth': datetime.date(1990, 2, 13), 'PAN Number': 'ABCDE0083F', 'Aadhaar Number': '5616-4450-6617', 'Customer Segment': 'Mass', 'Branch': 'Mathura', 'Relationship Start Date': datetime.date(2020, 4, 26), 'Product Type': 'Mutual Fund', 'Account Balance': 3083402.65, 'Risk Score': 45, 'KYC Expiry Date': datetime.date(2027, 8, 11), 'Alert': 'None', 'Monthly Logins': 153, 'Last Login Date': datetime.date(2025, 7, 31), 'Device Used': 'Mobile', 'Preferred Channel': 'NetBanking', 'Engagement Score': 42}]\\\\nError: None\\\"]]}\"}</uc_function_result>\n\nBased on the information retrieved, here is the detailed profile of **Tiya Sood**:\n\n## Customer Profile Summary\n\n**Personal Information:**\n- **Customer ID:** 84\n- **Name:** Tiya Sood\n- **Date of Birth:** February 13, 1990 (Age: 34 years)\n- **PAN Number:** ABCDE0083F\n- **Aadhaar Number:** 5616-4450-6617\n\n**Banking Relationship:**\n- **Customer Segment:** Mass\n- **Branch:** Mathura\n- **Relationship Start Date:** April 26, 2020 (Customer for ~4.5 years)\n\n**Portfolio & Account Details:**\n- **Primary Product Type:** Mutual Fund\n- **Account Balance:** ₹30,83,402.65 (approximately ₹30.8 lakhs)\n\n**Risk & Compliance:**\n- **Risk Score:** 45 (Moderate risk profile)\n- **KYC Status:** Valid until August 11, 2027\n- **Alerts:** None (Clean compliance record)\n\n**Digital Engagement:**\n- **Monthly Logins:** 153 (Very active user)\n- **Last Login Date:** July 31, 2025\n- **Primary Device:** Mobile\n- **Preferred Channel:** NetBanking\n- **Engagement Score:** 42\n\n## Key Insights:\nTiya Sood is a highly engaged customer with significant mutual fund investments. She's digitally savvy with frequent app usage and prefers NetBanking for transactions. Her moderate risk profile and substantial portfolio value make her an excellent candidate for wealth management services and additional investment products.\n\n_tool_reasoning: I used the lookup_customer_info function first to get basic customer information, then used the genie_wrapper to get comprehensive profile details including account balances, KYC status, digital engagement metrics, and risk profile information for Tiya Sood."
                },
                {
                    "role": "user",
                    "content": "What should I sell to her based on her profile?"
                }
            ]
        },
        "expected_response": None
    }
]

eval_results = mlflow.genai.evaluate(
    data=eval_dataset,
    predict_fn=lambda input: AGENT.predict({"input": input}),
    scorers=[RelevanceToQuery(), Safety()], # add more scorers here if they're applicable
)

# Review the evaluation results in the MLfLow UI (see console output)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Perform pre-deployment validation of the agent
# MAGIC Before registering and deploying the agent, we perform pre-deployment checks via the [mlflow.models.predict()](https://mlflow.org/docs/latest/python_api/mlflow.models.html#mlflow.models.predict) API. See [documentation](https://docs.databricks.com/machine-learning/model-serving/model-serving-debug.html#validate-inputs) for details

# COMMAND ----------

mlflow.models.predict(
    model_uri=f"runs:/{logged_agent_info.run_id}/agent",
    input_data={"input": [{"role": "user", "content": "Hello!"}]},
    env_manager="uv",
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Register the model to Unity Catalog
# MAGIC
# MAGIC Update the `catalog`, `schema`, and `model_name` below to register the MLflow model to Unity Catalog.

# COMMAND ----------

mlflow.set_registry_uri("databricks-uc")

# TODO: define the catalog, schema, and model name for your UC model
catalog = "demo_soumyashree_patra"
schema = "bharat_bank_rm"
model_name = "bharat_bank_rm_assistant"
UC_MODEL_NAME = f"{catalog}.{schema}.{model_name}"

# register the model to UC
uc_registered_model_info = mlflow.register_model(
    model_uri=logged_agent_info.model_uri, name=UC_MODEL_NAME
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Deploy the agent

# COMMAND ----------

from databricks import agents
agents.deploy(UC_MODEL_NAME, uc_registered_model_info.version, tags = {"endpointSource": "playground"})

# COMMAND ----------

# MAGIC %md
# MAGIC ## Next steps
# MAGIC
# MAGIC After your agent is deployed, you can chat with it in AI playground to perform additional checks, share it with SMEs in your organization for feedback, or embed it in a production application. See [docs](https://docs.databricks.com/generative-ai/deploy-agent.html) for details
