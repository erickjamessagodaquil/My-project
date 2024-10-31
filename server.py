from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from datetime import datetime

server = FastAPI()

####################################
#connection of the database
con = sqlite3.connect("social_media_post.db", check_same_thread=False)
cursor = con.cursor()


####################################
#table of the social media post

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        firstname TEXT NOT NULL,
        lastname TEXT  NOT NULL
    )
"""
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS posts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        caption TEXT NOT NULL,
        likes INTEGER DEFAULT 0,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        deactivated BOOLEAN DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id) 
    )
"""
)

con.commit()

class User(BaseModel):
    username: str
    lastname: str
    firstname: str

class Postnani(BaseModel):
    user_id: int
    caption: str
    likes: int = 0

@server.post("/users/")
def create_users(user: User):
    cursor.execute("INSERT INTO users (username, firstname, lastname) VALUES (?, ?, ?)",
                   (user.username, user.firstname, user.lastname))
    con.commit()
    return {"message": "Successfully Added"}

@server.get("/users/{user_id}")
def get_user(user_id: int):
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    return user

@server.put("/users/{user_id}")
def update_user(user_id: int, user: User):
    cursor.execute("UPDATE users SET username = ?, lastname = ?, firstname = ? WHERE id = ?",
                   (user.username, user.lastname, user.firstname, user_id))
    con.commit()
    return {"message": "User updated successfully"}

@server.delete("/users/{user_id}")
def delete_user(user_id: int):
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    con.commit()
    return {"message": "User deleted successfully"}


@server.get("/users/{user_id}/posts/")
def get_user_posts(user_id: int):
    cursor.execute("SELECT firstname, lastname FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    cursor.execute("SELECT caption, likes, date, time, deactivated FROM posts WHERE user_id = ? AND deactivated = 0", (user_id,))
    posts = cursor.fetchall()

    if not posts:
        raise HTTPException(status_code=404, detail="No posts found for this user")

    return {
        "user": {
            "firstname": user[0],
            "lastname": user[1]
        },
        "posts": [
            {
                "caption": post[0],
                "likes": post[1],
                "date": post[2],
                "time": post[3],
                "deactivated": bool(post[4])
            } for post in posts
        ]
    }


######################################################################################
# Post CRUD
@server.post("/posts/")
def create_post(post: Postnani):
    cursor.execute("SELECT * FROM users WHERE id = ?", (post.user_id,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.now()
    current_date = now.strftime('%Y-%m-%d')
    current_time = now.strftime('%H:%M:%S')

    cursor.execute("INSERT INTO posts (user_id, caption, likes, date, time) VALUES (?, ?, ?, ?, ?)",
                   (post.user_id, post.caption, post.likes, current_date, current_time))
    con.commit()
    return {"message": "Post created successfully"}


@server.put("/posts/{post_id}/deactivate")
def deactivate_post(post_id: int):
    cursor.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    post = cursor.fetchone()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    cursor.execute("UPDATE posts SET deactivated = 1 WHERE id = ?", (post_id,))
    con.commit()
    
    return {"message": "Post deactivated successfully"}


@server.put("/posts/{post_id}")
def update_post(post_id: int, post: Postnani):
    cursor.execute("UPDATE posts SET caption = ?, likes = ? WHERE id = ?",
                   (post.caption, post.likes, post_id))
    con.commit()
    return {"message": "Post updated successfully"}


@server.delete("/posts/{post_id}")
def delete_post(post_id: int):
    cursor.execute("UPDATE posts SET deactivated = 1 WHERE id = ?", (post_id,))
    con.commit()
    return {"message": "Post deactivated successfully"}