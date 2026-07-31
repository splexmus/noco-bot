from server.memory.memory_engine import MemoryEngine

memory = MemoryEngine(
    n_result = 1
)

memory.add(
    "My name is Alex.",
    "Nice to meet you, Alex."
)

memory.add(
    "I have a dog named Max.",
    "That's nice. Max sounds like a good name."
)

print("What is the user's name? : \n", memory.search("What is the user's name?"))
print("Does the user have a pet? : \n", memory.search("Does the user have a pet?"))

memory.clear_memory()