import configparser
import time

import httpx

config = configparser.ConfigParser(allow_no_value=True)

class HeartRate:
    def __init__(self, measured_at: int, heart_rate: int):
        self._measured_at = measured_at
        self._heart_rate = heart_rate

    @property
    def measured_at(self) -> int:
        return self._measured_at

    @property
    def heart_rate(self) -> int:
        return self._heart_rate

class Pulsoid:
    def __init__(self):
        """Initialize the Pulsoid class."""
        self.token = config["Login"]["api_token"]
        self._get_client()
        self._validate_token()
        self._start_time = time.monotonic()
        self._current_ramping_multiplier = 1.0
        self._ramping_max_multiplier = float(config["Settings"]["ramping_max_multiplier"])
        self._seconds_to_max_ramping = float(config["Settings"]["seconds_till_max_ramping"])
        self._ramping_mode = config["Settings"]["ramping_mode"].lower() == "true"
        self._polling_interval = float(config["Settings"]["polling_interval"])
        self._smoothing_interval = float(config["Settings"]["smoothing_interval"])
        self._base_multiplier = float(config["Settings"]["base_multiplier"])

        self._polls_within_interval: list[tuple[float, int]] = []
        """A list of tuples containing the time and heart rate of each poll within the smoothing interval."""

    def _get_smoothed_heartrate(self) -> int:
        """Get the smoothed heartrate."""
        if len(self._polls_within_interval) == 0:
            return 0

        total_heartrate = sum([poll[1] for poll in self._polls_within_interval])
        average_heartrate = total_heartrate // len(self._polls_within_interval)

        # print(f"Smoothed HR: {average_heartrate} (Avg of {len(self._polls_within_interval)}) polls")
        return average_heartrate

    def get_heartrate(self) -> HeartRate:
        """Get the current heart rate."""
        try:
            r = self.client.get("https://dev.pulsoid.net/api/v1/data/heart_rate/latest")
            r.raise_for_status()
        except httpx.HTTPError as e:
            print(e)
            return None

        json_data = r.json()
        return HeartRate(json_data["measured_at"], json_data["data"]["heart_rate"])

    def run(self):
        output_file_is_csv = (self._get_heart_rate_file_extension() == 'csv')
        latest_heart_rate_value = None
        while True:
            time.sleep(self._polling_interval)
            if not (hr := self.get_heartrate()):
                print("Failed to get heart rate.")
                continue
            
            if not output_file_is_csv:
                # update the txt file
                self._set_current_ramping_multiplier()
                self._populate_polls_within_interval(hr.heart_rate)
                smoothed_hr = self._get_smoothed_heartrate()
                final_hr = self._set_multiplied_heartrate(hr.heart_rate, smoothed_hr)
                self._write_heartrate(final_hr)
            else:
                # add entry to the csv file
                # only append if the got value is different than the last one
                if hr.heart_rate != latest_heart_rate_value:
                    self._write_heartrate_csv(hr)

            latest_heart_rate_value = hr.heart_rate

    def _get_heart_rate_file_extension(self) -> str:
        """Gets the extension of the file specified on the config."""
        return config["Settings"]["heart_rate_file"].split(".")[-1]

    def _write_heartrate_csv(self, hr: HeartRate):
        """Write the heart rate to the file."""
        with open(config["Settings"]["heart_rate_file"], "a+") as f:
            new_file = (f.tell() == 0)
            if new_file:
                # header is needed
                f.write(f"UNIX millis timestamp;heartrate\n")
            f.write(f"{hr.measured_at};{hr.heart_rate}\n")

    def _write_heartrate(self, hr):
        """Write the heart rate to the file."""
        with open(config["Settings"]["heart_rate_file"], "w") as f:
            f.write(str(hr))

    def _set_multiplied_heartrate(self, hr, smoothed_hr):
        m_hr = int(smoothed_hr * self._current_ramping_multiplier * self._base_multiplier)
        time_elapsed = time.monotonic() - self._start_time
        print(
            f"HR: {m_hr: 3d} ({hr: 3d} > Smoothed: {smoothed_hr} * Ramp: {self._current_ramping_multiplier: 4.2f} "
            f"* Base: {self._base_multiplier}) at {time_elapsed:.2f} seconds"
        )
        return m_hr

    def _set_current_ramping_multiplier(self):
        """Set the current ramping multiplier."""
        if not self._ramping_mode:
            self._current_ramping_multiplier = 1.0
            return

        time_elapsed = time.monotonic() - self._start_time

        if time_elapsed >= self._seconds_to_max_ramping:
            self._current_ramping_multiplier = self._ramping_max_multiplier
            # print("Ramping multiplier is at max: " + str(self._current_ramping_multiplier))
            return

        portion_of_max_ramping = time_elapsed / self._seconds_to_max_ramping
        self._current_ramping_multiplier = self._ramping_max_multiplier * portion_of_max_ramping + 1
        # print(f"Ramping multiplier: {self._current_ramping_multiplier:.2f} at {time_elapsed:.2f} seconds")

    def _populate_polls_within_interval(self, hr):
        """Populate the polls within the smoothing interval."""
        current_time = time.monotonic()

        # Remove all polls that are older than the smoothing interval
        self._polls_within_interval = [
            poll for poll in self._polls_within_interval if current_time - poll[0] <= self._smoothing_interval
        ]

        # Always add the current poll
        self._polls_within_interval.append((current_time, hr))

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


def ensure_config():
    """Ensure that the config has the correct keys."""
    if "Login" not in config:
        config.add_section("Login")
    if "Settings" not in config:
        config.add_section("Settings")

    if not config.has_option("Login", "api_token"):
        config.set("Login", "api_token", "YOUR_API_TOKEN")
    if not config.has_option("Settings", "heart_rate_file"):
        config.set("Settings", "heart_rate_file", "heart_rate.txt")
    if not config.has_option("Settings", "polling_interval"):
        config.set("Settings", "polling_interval", "0.5")
    if not config.has_option("Settings", "smoothing_interval"):
        config.set("Settings", "smoothing_interval", "10")
    if not config.has_option("Settings", "base_multiplier"):
        config.set("Settings", "base_multiplier", "1.0")
    if not config.has_option("Settings", "ramping_mode"):
        config.set("Settings", "ramping_mode", "True")
    if not config.has_option("Settings", "ramping_max_multiplier"):
        config.set("Settings", "ramping_max_multiplier", "3.0")
    if not config.has_option("Settings", "seconds_till_max_ramping"):
        config.set("Settings", "seconds_till_max_ramping", "360")

    with open("config.ini", "w") as f:
        config.write(f)


def process_ini_file():
    """Make an empty config.ini file."""
    global config

    if config.read("config.ini"):
        print("Config file exists.")
        ensure_config()
        return

    ensure_config()
    print("Config file created. Please edit it and run the program again.")
    exit()


def save_heart_rate(hr):
    """Save the heart rate to a file, catching exceptions since there might be race conditions."""
    try:
        with open(config["Settings"]["heart_rate_file"], "w") as f:
            f.write(str(hr))
    except Exception as e:
        print(e)


def run():
    """Run the program."""
    print("Starting Pulsoid Heartrate Monitor...")
    print("Press Ctrl+C to exit.")
    print("")
    print("Love you bro <3")
    print("")
    process_ini_file()
    pulsoid = Pulsoid()

    pulsoid.run()


if __name__ == "__main__":
    run()
