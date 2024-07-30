import httpx


class BaseFetcher:
    def __init__(self, api_key):
        self.api_key = api_key

    async def fetch_data(self, url):
        """Fetch data asynchronously from the given URL."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()  # Raise an error for bad responses
                return response.json()  # Assuming API returns JSON data
            except httpx.HTTPStatusError as e:
                print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                print(f"An error occurred: {e}")

        return None  # Return None if there was an error

    def parse_data(self, data):
        """Parse the fetched data. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses should implement this method!")
