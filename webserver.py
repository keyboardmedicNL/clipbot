# loads libraries needed in script
from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import json
import requests

# formats embed for discord webhook and posts to url
def discord_embed(title,color,description):
    if webhooklogurl != "":
        data = {"embeds": [
                {
                    "title": title,
                    "color": color,
                    "description": description
                }
            ]}
        rl = requests.post(webhooklogurl, json=data)

# loads config into variables for use in script
with open("config/config.json") as config: # opens config and stores data in variables
    configJson = json.load(config)
    hostName = configJson["hostname"]
    serverPort = int(configJson["webport"])
    webhooklogurl = configJson["webhooklogurl"]
    config.close()
    configcheck = True # stops loop if succesfull
    print("<WEBSERVER> Succesfully loaded config")
    discord_embed("Clipbot/webserver",14081792,"succesfully loaded config")

# start webserver
class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><head><title>https://pythonbasics.org</title></head>", "utf-8"))
        self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))
        self.wfile.write(bytes("<p>Hello, i am a webserver.</p>", "utf-8"))
        self.wfile.write(bytes("</body></html>", "utf-8"))

if __name__ == "__main__":        
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("<WEBSERVER> Server started http://%s:%s" % (hostName, serverPort))
    discord_embed("Clipbot/webserver",703235,"Server started http://%s:%s" % (hostName, serverPort))


    webServer.serve_forever()