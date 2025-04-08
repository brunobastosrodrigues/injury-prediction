import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

CLIENT_ID = "144607"
CLIENT_SECRET = "5103b9d299464cde9b0ec9ba1b289dcbe18efb48"
REDIRECT_URI = "http://localhost:8080/exchange_token"

class StravaCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if "code=" in self.path:
            code = self.path.split("code=")[-1].split("&")[0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Authorization code received. You can close this tab.")
            with open("auth_code.txt", "w") as f:
                f.write(code)
            self.server.auth_code = code
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid request.")

def run_local_server():
    print("Starting local server at http://localhost:8080/exchange_token")
    server_address = ("localhost", 8080)
    httpd = HTTPServer(server_address, StravaCallbackHandler)
    httpd.handle_request()
    return httpd.auth_code

def get_authorization_code():
    print("Please authorize the app in your browser...")
    print(f"Open this URL: https://www.strava.com/oauth/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope=activity:read")
    return run_local_server()

def get_access_token():
    authorization_code = get_authorization_code()
    response = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": authorization_code,
            "grant_type": "authorization_code"
        }
    )
    response_json = response.json()
    if "access_token" in response_json:
        return response_json["access_token"]
    else:
        raise Exception(f"Error fetching access token: {response_json}")
