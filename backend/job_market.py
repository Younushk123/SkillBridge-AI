
import requests
from requests import RequestException

URL = "https://himalayas.app/jobs/api/search"


class JobMarketProviderError(Exception):
    pass


def fetch_current_jobs(target_role, limit=10):
    try:
        response = requests.get(
            URL,
            params={"q": target_role, "sort": "recent", "page": 1},
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
    except (RequestException, ValueError) as error:
        raise JobMarketProviderError("Live job-market data is unavailable") from error

    if isinstance(data, list):
        jobs = data
    elif isinstance(data, dict) and isinstance(data.get("jobs"), list):
        jobs = data["jobs"]
    else:
        raise JobMarketProviderError("Live job-market data is invalid")

    return [job for job in jobs if isinstance(job, dict)][:limit]
