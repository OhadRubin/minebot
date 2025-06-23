
import time
from .bot import create_bot
from .mining import do_floor_mining

if __name__ == "__main__":
    options = {
                'host'    : "7.tcp.eu.ngrok.io",
                'port'    : 14984,
                'username': "pybot",
                'auth'    : "offline",
                'version' : "1.20.4",
                'hideErrors': False,
                }

    print("Creating bot...")
    bot = create_bot(options)
    print("Bot created, setting up events...")
    
    @bot.on_login
    def handle_login():
        print("Bot logged in!")
    
    @bot.on_spawn
    def handle_spawn():
        print("Bot spawned, starting 3x3 floor mining...")
        import asyncio
        import threading
        
        def run_async():
            asyncio.run(do_floor_mining(bot))
        
        thread = threading.Thread(target=run_async)
        thread.start()

    for i in range(1, 31):
        time.sleep(1)
    print("Finished mining")

