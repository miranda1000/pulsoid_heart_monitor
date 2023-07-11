import httpx
import configparser

config = configparser.ConfigParser()
config.read("config.ini")


class Pulsoid:
    def validate_token(self):
        r = self.client.get("https://dev.pulsoid.net/api/v1/token/validate")
        r.raise_for_status()

    def get_client(self):
        self.client = httpx.Client(
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
        )

    def __init__(self):
        self.token = config["Login"]["API_TOKEN"]
        self.get_client()
        self.validate_token()


if __name__ == "__main__":
    pulsoid = Pulsoid()
