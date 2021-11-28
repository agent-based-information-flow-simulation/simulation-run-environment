import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from subprocess import PIPE, STDOUT
import uuid
import asyncio

app = FastAPI()
cors_origins = ["http://localhost:3000"]
cors_methods = ["*"]
app.add_middleware(CORSMiddleware, allow_origins=cors_origins, allow_methods=cors_methods)
simulations = {}


@app.post("/simulations")
async def post_simulations(num_agents: int):
    simulation_id = str(uuid.uuid4())
    simulation = await asyncio.create_subprocess_exec("python", "-u", "main.py", "-n", f"{num_agents}", "-d", f"{simulation_id}", stdout=PIPE, stderr=STDOUT)
    simulations[simulation_id] = simulation
    return {"id": simulation_id}


@app.websocket("/simulations/{simulation_id}")
async def get_simulation(websocket: WebSocket, simulation_id: str):
    await websocket.accept()
    if simulation_id not in simulations:
        websocket.close()
    while True:
        try:
            line = await simulations[simulation_id].stdout.readline()
        except KeyError:
            await websocket.send_json({"id": simulation_id, "error": "Simulation not found"})
            await websocket.close()
        except:
            await websocket.send_json({"id": simulation_id, "error": "Unknown error"})
            del simulations[simulation_id]
            await websocket.close()
        if line:
            await websocket.send_json({"id": simulation_id, "line": line.decode("utf-8").strip('\n')})


@app.websocket("/simulations")
async def get_simulations(websocket: WebSocket):
    await websocket.accept()
    while True:
        await websocket.send_json({"running_simulations": list(simulations.keys())})
        await asyncio.sleep(2)
        

@app.delete("/simulations/{simulation_id}")
async def delete_simulation(simulation_id: str):
    if simulation_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    simulations[simulation_id].kill()
    del simulations[simulation_id]
    return {"success": True}


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
