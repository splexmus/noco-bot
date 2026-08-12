from server.llm.ollama_engine import OllamaEngine

llm = OllamaEngine()

mesg = [{'role': 'user', 'content': 'what is ai raising?'}]
# print(llm.generate(mesg))
print(llm.test())
