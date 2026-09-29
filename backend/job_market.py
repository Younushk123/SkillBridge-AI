
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

def fetch_jobs_for_roles(roles, limit_per_role=10):
    all_jobs = []

    for role in roles:
        jobs = fetch_current_jobs(role, limit=limit_per_role)

        for job in jobs:
            job_copy = dict(job)
            job_copy["_searched_role"] = role
            all_jobs.append(job_copy)

    return all_jobs

def calculate_role_demand(roles, limit_per_role=10):
    jobs = fetch_jobs_for_roles(
        roles,
        limit_per_role=limit_per_role,
    )

    role_counts = {}

    for job in jobs:
        role = job.get("_searched_role")

        if not role:
            continue

        role_counts[role] = role_counts.get(role, 0) + 1

    total_jobs = sum(role_counts.values())

    if total_jobs == 0:
        return []

    role_demand = [
        {
            "role": role,
            "job_count": count,
            "demand_percentage": round((count / total_jobs) * 100, 1),
        }
        for role, count in role_counts.items()
    ]

    role_demand.sort(
        key=lambda item: (-item["job_count"], item["role"].casefold())
    )

    return role_demand
