import configparser

import httpx
import time

config = configparser.ConfigParser()


class Pulsoid:
    def __init__(self):
        """Initialize the Pulsoid class."""
        self.token = config["Login"]["API_TOKEN"]
        self._get_client()
        self._validate_token()

    def get_heartrate(self):
        """Get the current heart rate."""
        try:
            r = self.client.get("https://dev.pulsoid.net/api/v1/data/heart_rate/latest")
            r.raise_for_status()
        except httpx.HTTPError as e:
            print(e)
            return None

        return r.json()["data"]["heart_rate"]

    def _validate_token(self):
        """Validate token against the API."""
        r = self.client.get("https://dev.pulsoid.net/api/v1/token/validate")

        try:
            r.raise_for_status()
        except httpx.HTTPError as e:
            if r.status_code == 403:
                print("Pulsoid declined the token. Please check the ini file and update it.")
            else:
                print(e)
            exit()

    def _get_client(self) -> httpx.Client:
        """Get a client with the token set in the header."""
        self.client = httpx.Client(
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
        )


def process_ini_file():
    """Make an empty config.ini file."""
    global config

    if config.read("config.ini"):
        print("Config file exists.")
        return

    config["Login"] = {"API_TOKEN": "YOUR_API_TOKEN"}
    config["Settings"] = {"HEART_RATE_FILE": "heartrate.txt"}
    with open("config.ini", "w") as f:
        config.write(f)

    print("Config file created. Please edit it and run the program again.")
    exit()


def save_heart_rate(hr):
    """Save the heart rate to a file, catching exceptions since there might be race conditions."""
    try:
        with open(config["Settings"]["HEART_RATE_FILE"], "w") as f:
            f.write(str(hr))
    except Exception as e:
        print(e)


def run():
    """Run the program."""
    process_ini_file()
    pulsoid = Pulsoid()

    while True:
        time.sleep(0.5)
        if hr := pulsoid.get_heartrate():
            save_heart_rate(hr)
            print(hr)


if __name__ == "__main__":
    run()
