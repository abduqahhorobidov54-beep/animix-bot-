import asyncio
import asyncpg
import json

# BU YERGA O'ZINGIZNING EXTERNAL DATABASE URL HAVOLANGIZNI QO'YING
DB_URL = "postgresql://animix_db_user:xICwbIPcQHGpSo8EqM2zYyj5KXxBg0xV@dpg-d9ac5567r5hc73cg0ga0-a.frankfurt-postgres.render.com/animix_db"

async def init_db():
    conn = await asyncpg.connect(DB_URL)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS animes (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            genres TEXT,
            description TEXT,
            photo_id TEXT,
            seasons JSONB DEFAULT '[]'::jsonb
        )
    ''')
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            key TEXT PRIMARY KEY,
            value INT DEFAULT 0
        )
    ''')
    # Statistikani boshlang'ich qiymat bilan to'ldirish
    await conn.execute('''
        INSERT INTO stats (key, value) VALUES ('total_users', 0)
        ON CONFLICT (key) DO NOTHING
    ''')
    await conn.close()

async def get_all_anime():
    conn = await asyncpg.connect(DB_URL)
    rows = await conn.fetch('SELECT id, title, genres, description, photo_id, seasons FROM animes')
    await conn.close()
    
    anime_list = {}
    for row in rows:
        anime_list[str(row['id'])] = {
            "title": row['title'],
            "genres": row['genres'],
            "description": row['description'],
            "photo_id": row['photo_id'],
            "seasons": json.loads(row['seasons'])
        }
    return anime_list

async def save_anime_db(anime_id, anime_data):
    conn = await asyncpg.connect(DB_URL)
    seasons_json = json.dumps(anime_data.get("seasons", []))
    
    # Agar anime bazada bo'lsa yangilaydi, yo'q bo'lsa qo'shadi
    await conn.execute('''
        INSERT INTO animes (id, title, genres, description, photo_id, seasons)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (id) DO UPDATE 
        SET title = $2, genres = $3, description = $4, photo_id = $5, seasons = $6
    ''', int(anime_id), anime_data['title'], anime_data['genres'], anime_data['description'], anime_data['photo_id'], seasons_json)
    await conn.close()

async def get_next_anime_id():
    conn = await asyncpg.connect(DB_URL)
    row = await conn.fetchrow('SELECT MAX(id) FROM animes')
    await conn.close()
    return (row['max'] or 0) + 1

async def add_user_to_stats():
    conn = await asyncpg.connect(DB_URL)
    await conn.execute("UPDATE stats SET value = value + 1 WHERE key = 'total_users'")
    await conn.close()

async def get_total_users():
    conn = await asyncpg.connect(DB_URL)
    row = await conn.fetchrow("SELECT value FROM stats WHERE key = 'total_users'")
    await conn.close()
    return row['value'] if row else 0
