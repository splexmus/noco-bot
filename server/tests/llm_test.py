from server.llm.ollama_engine import OllamaEngine

llm = OllamaEngine()

mesg = "Hi, what are you?"
print(llm.generate(mesg))
