import os
from promptflow.rag.config import LocalSource, AzureAISearchConfig, EmbeddingsModelConfig
from promptflow.rag import build_index
from promptflow.rag import get_langchain_retriever_from_index

# Azure Search parameters
search_service_name = "ai-search-wiski"
admin_key = "Zu8iq9PKbNIuSpiroRCrmwWZK7hoE1hMNIrGB6ATinAzSeBBG0KC"
index_name = "wiski-index"

# Azure OpenAI parameters
openai_api_key = "2hkRYN8YdY0FDaETo7DTDqjQcXDGoCltTpZHjczVqz6hsI9YnZZwJQQJ99AKACfhMk5XJ3w3AAABACOG2IL9"
openai_endpoint = "https://user-upload.openai.azure.com/"
openai_model = "text-embedding-ada-002"

# Set environment variables for Azure Search and OpenAI
os.environ["AZURE_AI_SEARCH_KEY"] = admin_key
os.environ["AZURE_AI_SEARCH_ENDPOINT"] = f"https://{search_service_name}.search.windows.net"
os.environ["OPENAI_API_VERSION"] = "2024-09-01"
os.environ["AZURE_OPENAI_API_KEY"] = openai_api_key
os.environ["AZURE_OPENAI_ENDPOINT"] = openai_endpoint

def create_index():
    """
    Creates an index in Azure AI Search using promptflow.rag.
    """
    try:
        # Define the index
        local_index = build_index(
            name=index_name,
            vector_store="azure_ai_search",
            embeddings_model_config=EmbeddingsModelConfig(
                model_name=openai_model,
                deployment_name=openai_model,  # Ensure deployment name matches the model
            ),
            input_source=LocalSource(input_data="./data"),  # Path to your data folder
            index_config=AzureAISearchConfig(
                ai_search_index_name=index_name  # Name for the index in Azure AI Search
            ),
            tokens_per_chunk=800,  # Optional: maximum tokens per chunk
            token_overlap_across_chunks=0  # Optional: token overlap
        )
        print(f"Index '{index_name}' created successfully.")
        return local_index
    except Exception as e:
        print(f"Error creating index: {e}")

def query_index(index, query):
    """
    Queries the created index using langchain retriever.
    """
    try:
        # Use the LangChain retriever
        retriever = get_langchain_retriever_from_index(index)
        results = retriever.get_relevant_documents(query)
        print("Query Results:")
        for result in results:
            print(result)
    except Exception as e:
        print(f"Error querying index: {e}")

if __name__ == "__main__":
    # Ensure you have a data folder with text files to index
    data_folder = "./data"

    # Create the index
    index = create_index()
