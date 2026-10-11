# MTGTable uses HTTP with client-initiated long-poll for IPC

The central game process is an HTTP server (FastAPI) and every player process is a pure client. Clients learn of game events by long-polling `GET /events`, with Server-Sent Events as a planned upgrade, instead of the server calling back into player processes or using gRPC. This avoids each player process running a server, port registration, and unreachable-callback handling, while keeping every interaction plain request/response.
