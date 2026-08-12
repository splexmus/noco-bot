from ollama import chat, ChatResponse

class OllamaEngine:
    def __init__(
        self,
        model: str = "gemma4:e4b",
    ):
        self.model = model

    def generate(self, prompt):
        response = chat(self.model, messages=prompt)
        return response['message']['content']



    def add(a: int, b: int) -> int:
        """Add two numbers"""
        """
        Args:
            a: The first number
            b: The second number

        Returns:
            The sum of the two numbers
        """
        return a + b


    def multiplytwo(a: int, b: int) -> int:
        """Multiply two numbers"""
        """
        Args:
            a: The first number
            b: The second number

        Returns:
            The product of the two numbers
        """
        return a * b * b

    def test(self):
        available_functions = {
        'add': self.add,
        'multiply': self.multiplytwo,
        }

        messages = [{'role': 'user', 'content': 'What is multiplytwo((11434+12341),412)?'}]
        while True:
            response: ChatResponse = chat(
                model='gemma4:e4b',
                messages=messages,
                tools=[self.add, self.multiplytwo],
                think=True,
            )
            messages.append(response.message)
            print("Thinking: ", response.message.thinking)
            print("Content: ", response.message.content)
            if response.message.tool_calls:
                for tc in response.message.tool_calls:
                    if tc.function.name in available_functions:
                        print(f"Calling {tc.function.name} with arguments {tc.function.arguments}")
                        result = available_functions[tc.function.name](**tc.function.arguments)
                        print(f"Result: {result}")
                        # add the tool result to the messages
                        messages.append({'role': 'tool', 'tool_name': tc.function.name, 'content': str(result)})
            else:
                # end the loop when there are no more tool calls
                break
        # continue the loop with the updated messages
        return messages