from pyrogram import Client

api_id = int(input("Enter API ID: "))
api_hash = input("Enter API Hash: ")

with Client("my_account", api_id=api_id, api_hash=api_hash) as app:
    print("Session created successfully!")
