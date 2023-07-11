import configparser

import httpx
import time

config = configparser.ConfigParser()
config.read("config.ini")


class Pulsoid:
    def __init__(self):
        """Initialize the Pulsoid class."""
        self.token = config["Login"]["API_TOKEN"]
        self._get_client()
        self._validate_token()

    def get_heartrate(self):
        """Get the current heart rate."""
        try:
            r = self.client.get("https://dev.pulsoid.net/api/v1/user")
            r.raise_for_status()
        except httpx.HTTPError as e:
            print(e)
            return None
        return r.json()["heartrate"]

    def _validate_token(self):
        """Validate token against the API."""
        r = self.client.get("https://dev.pulsoid.net/api/v1/token/validate")
        r.raise_for_status()

    def _get_client(self) -> httpx.Client:
        """Get a client with the token set in the header."""
        self.client = httpx.Client(
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
        )


def save_heart_rate(hr):
    """Save the heart rate to a file, catching exceptions since there might be race conditions."""
    try:
        with open(config["Settings"]["HEART_RATE_FILE"], "w") as f:
            f.write(hr)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    pulsoid = Pulsoid()

    while True:
        if hr := pulsoid.get_heartrate():
            save_heart_rate(hr)
            print(hr)
