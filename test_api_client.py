import asyncio
from api_client import APIClient, APIClientError

async def main():
    client = APIClient(api_key="your_api_key_here")  # Replace with your actual API key
    try:
        models = await client.list_models()
        print("Available models:")
        for model in models:
            print(f"- {model['id']}")
    except APIClientError as e:
        print(f"Error: {str(e)}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())