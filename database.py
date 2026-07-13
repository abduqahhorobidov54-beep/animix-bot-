import json
import aiofiles
import os

FILES = {"anime": "anime.json", "admins": "admins.json", "users": "users.json"}

async def init_db():
    for key, filename in FILES.items():
        if not os.path.exists(filename):
            async with aiofiles.open(filename, "w", encoding="utf-8") as f:
                await f.write(json.dumps([] if key != "anime" else {}, indent=4))

async def read_data(file_key):
    async with aiofiles.open(FILES[file_key], "r", encoding="utf-8") as f:
        content = await f.read()
        return json.loads(content)

async def write_data(file_key, data):
    async with aiofiles.open(FILES[file_key], "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, indent=4, ensure_ascii=False))
