import httpx
import asyncio

async def test():
    app_id = "72d283fb"
    app_key = "bc8fa114baf05df8506b6d60fe998b14"
    country = "in"
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    
    roles = [
        "Backend Developer",
        "Frontend Developer",
        "Full Stack Developer",
        "AI Engineer",
        "Data Scientist",
    ]
    
    async with httpx.AsyncClient() as client:
        for role in roles:
            for emp in ["", " Intern"]:
                for rem in ["", " remote"]:
                    what = f"{role}{emp}{rem}"
                    params = {
                        "app_id": app_id,
                        "app_key": app_key,
                        "results_per_page": 1,
                        "what": what,
                        "content-type": "application/json",
                    }
                    resp = await client.get(url, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        print(f"Query: '{what}' -> {data.get('count', 0)} results")
                    else:
                        print(f"Query: '{what}' -> HTTP {resp.status_code}")

if __name__ == "__main__":
    asyncio.run(test())

