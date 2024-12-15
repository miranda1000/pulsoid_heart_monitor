# Pagrax Heart Rate Monitoring Tool
![Banner Image](images/banner2.png)

A simple script that checks Pulsoid for heart rate data and injects the current rate into a text file. 

## Prerequisites
- Python 3.11 or higher, or Docker
- Git
- A Pulsoid API token

## Usage

Clone the repository to your computer, then navigate to that folder

```bash
git clone https://github.com/Wyko/pagrax_heart_mon.git
cd pagrax_heart_mon
```

Check the [configuration](#configuration) section below to get your API token.

### Docker usage (recommended)

Go to the `docker` folder, and run `docker compose up -d`

### Python usage

Install the required packages

```bash
pip install -r requirements.txt
```

Run the script

```bash
python -m pagmon
```

## Configuration
The script comes with a `config.ini` file in the root directory as the script. This file contains the following settings:
```ini
[Login]
API_TOKEN=YOUR_API_TOKEN

[Settings]
HEART_RATE_FILE=my/heart/rate/file.txt
```
| Setting | Description |
| --- | --- |
| `API_TOKEN` | The API token you get from Pulsoid. You can find it by logging into your account and going to the [API page](https://docs.pulsoid.net/access-token-management/manual-token-issuing). |
| `HEART_RATE_FILE` | The path to the file you want to write the heart rate to. |

If HEART_RATE_FILE is a txt file it will output the latest heartrate; if it is a csv it will log all the values.

## License
This project is licensed under the GNU GPLv3 license. See the [LICENSE](LICENSE) file for more information. It's just for my brother anyway :)