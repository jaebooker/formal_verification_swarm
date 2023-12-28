import autogen
import pexpect

config_list_mistral = [
    {
        'base_url': "http://0.0.0.0:8000", #will need to setup using ollama
        'api_key': "NULL"
    }
]

config_list_codellama = [
    {
        'base_url': "http://0.0.0.0:35614", #setup with ollama
        'api_key': "NULL"
    }
]

config_list_llamacoq = [
    {
        'base_url': "http://0.0.0.0:3000", #setup using llm studio and running https://huggingface.co/jbb/llama_coq 
        'api_key': "NULL"
    }
]

llm_config_mistral={
    "config_list": config_list_mistral,
    "seed": 42, "request_timeout": 120,
    "temperature": 0,
    "functions": [
          {
              "name": "Coq",
              "description": "run cell in Coq and return the execution result.",
              "parameters": {
                  "type": "object",
                  "properties": {
                      "cell": {
                          "type": "string",
                          "description": "Valid coq cell to execute.",
                      }
                  },
                  "required": ["cell"],
              },
          },
      ],
}

llm_config_codellama={
    "config_list": config_list_codellama,
    "seed": 42, "request_timeout": 120,
    "temperature": 0,
}

llm_config_llamacoq={
    "config_list": config_list_llamacoq,
    "seed": 42, "request_timeout": 120,
    "temperature": 0,
}

class CoqTop:
    coq_regex = r"\r\n[^< ]+ < "

    def __init__(self, timeout=5):
        self.timeout = timeout
        self.process = pexpect.spawn("coqtop -color off")
        self.process.expect(self.coq_regex)

    def send_line(self, line):
        self.process.sendline(' '.join(line.split('\n')))
        self.process.expect(self.coq_regex, timeout=self.timeout)
        return self.process.before.decode('utf-8')

    def send_text(self, text):
        lines = text.split(".")
        output = []

        for line in lines[:-1]:
            answer = self.send_line(line + ".")
            if answer is not None:
                output.append(answer)
                if "Error" in answer:
                    break

        return "".join(output)

# The User Input Agent initiates the conversation by collecting the user’s input.
# The Formalization Agent and Coq Writing Agent receives this input and begins the formalization process, collaborating with the Coq Writing Agent to translate this into Coq code.
# The Coq Verification Agent then takes over to verify the Coq code. If issues are found, it communicates them back to the Coq Writing Agent for revisions.
# The Coordinator Agent (Product Manager) monitors this flow and ensures that the process stays aligned with the user’s original input.

user_proxy_agent = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={"work_dir": "web"},
    llm_config=llm_config_mistral,
    system_message="""Reply TERMINATE if the task has been solved at full satisfaction.
Otherwise, reply CONTINUE, or the reason why the task is not solved yet."""
)


# Formalization Agent
formalization_agent = autogen.AssistantAgent(
    name="Formalization_Agent",
    system_message="I translate coding problems into formal specifications. I receive the input from the User Input Agent, and begin the formalization process, collaborating with the Coq Writing Agent to translate this into Coq code.",
    llm_config=llm_config_codellama,
)

# Coq Writing Agent
coq_writing_agent = autogen.AssistantAgent(
    name="Coq_Writing_Agent",
    system_message="I write Coq code based on formal specifications.",
    llm_config=llm_config_llamacoq,
)

# Coq Verification Agent
coq_verification_agent = autogen.AssistantAgent(
    name="Coq_Verification_Agent",
    system_message="I verify the correctness of Coq code from the Coq Writing Agent. If issues are found, I communicate them back to the Coq Writing Agent for revisions. I will run exec_coq(cell) on the code Coq_Writing_Agent creates",
    llm_config=llm_config_mistral,
    code_execution_config={
    "work_dir": "coding",
    "use_docker": False,
    }
)

# Define the Product Manager Agent
product_manager = autogen.AssistantAgent(
    name="Product_Manager",
    system_message="I oversee the process, coordinate between different agents, and ensure that the process stays aligned with the user’s original input",
    llm_config=llm_config_mistral,
)

groupchat = autogen.GroupChat(agents=[user_input_agent, formalization_agent, coq_writing_agent, coq_verification_agent, product_manager], messages=[], max_round=50)
manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

def exec_coq(cell):
    cell = """Require Import List.
    Import ListNotations.
    Require Import Arith.""" +cell
    coqtop = CoqTop()
    result = coqtop.send_text(cell)
    return result


# register the functions
coq_verification_agent.register_function(
    function_map={
        "Coq": exec_coq,
    }
)

user_input_agent.initiate_chat(manager, message="Here's a coding problem that needs formalization: [insert specifications]")
