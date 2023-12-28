# formal_verification_swarm
Using autogen and multiple agents to create mathematical formalizations for code generations.

This is part of a larger project worked on with various teammates to create a complete pipeline for verifying code generated by AIs.

# auto.py

Model-agnostic version of verification using autogen, connected to mistral, code llama, and a finetuned version of code llama trained for mathematical formal verification.
Finetuned model: https://huggingface.co/jbb/llama_coq 
Dataset: https://huggingface.co/datasets/jbb/coq_code 
