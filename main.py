from dotenv import load_dotenv
import os
import openai
import pprint
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

load_dotenv()
pp = pprint.PrettyPrinter(indent=4)


def generate_response(messages):

    openai.api_key = os.getenv("OPENAI_API_KEY")
    model_name = os.getenv("MODEL_NAME")

    response = openai.ChatCompletion.create(
        model=model_name,
        messages=messages,
        temperature=0.5,
        max_tokens=250
    )

    print("Request:")
    pp.pprint(messages)

    print(
        f"Completion tokens: {response['usage']['completion_tokens']},"
        f" Prompt tokens: {response['usage']['prompt_tokens']},"
        f" Total tokens: {response['usage']['total_tokens']}"
    )

    return response['choices'][0]['message']


def main():
    chroma_client = chromadb.Client()
    embedding_function = OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name=os.getenv("EMBEDDING_MODEL")
    )
    collection = chroma_client.create_collection(
        name="conversations",
        embedding_function=embedding_function
    )

    current_id = 0

    while True:

        chat_history = []
        chat_metadata = []
        history_ids = []

        messages = [
            {"role": "system", "content": "You are an assistant"}
        ]

        input_text = input("You: ")
        if input_text.lower() == "quit":
            break

        results = collection.query(
            query_texts=[input_text],
            where={"role": "assistant"},
            n_results=2
        )

        for res in results['documents'][0]:
            messages.append({"role": "user", "content": f"previous chat: {res}"})

        messages.append({"role": "user", "content": input_text})
        response = generate_response(messages)

        chat_metadata.append({"role": "user"})
        chat_history.append(input_text)
        chat_metadata.append({"role": "assistant"})
        chat_history.append(response['content'])
        current_id += 1
        history_ids.append(f"id_{current_id}")
        current_id += 1
        history_ids.append(f"id_{current_id}")
        collection.add(
            documents=chat_history,
            metadatas=chat_metadata,
            ids=history_ids
        )
        print(f"Assistant: {response['content']}")


if __name__ == "__main__":
    main()
