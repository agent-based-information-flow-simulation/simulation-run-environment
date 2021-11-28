import uvicorn
from fastapi import FastAPI, HTTPException
from subprocess import PIPE, STDOUT
import uuid
import asyncio

app = FastAPI()
simulations = {}


@app.post("/simulations")
async def post_simulations(num_agents: int):
    simulation = await asyncio.create_subprocess_exec("python", "-u", "main.py", "-n", f"{num_agents}", "-d", f"{str(uuid.uuid4())}", stdout=PIPE, stderr=STDOUT)
    simulation_id = str(uuid.uuid4())
    simulations[simulation_id] = simulation
    return {"id": simulation_id}


@app.get("/simulations/{simulation_id}")
async def get_simulation(simulation_id: str):
    if simulation_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    max_lines_to_read = 50
    lines = []
    timeout = 2  # seconds
    while len(lines) < max_lines_to_read:
        try:
            line = await asyncio.wait_for(simulations[simulation_id].stdout.readline(), timeout)
        except:
            break
        if line:
            lines.append(line.decode("utf-8"))
    return {"output": lines}


@app.get("/simulations")
async def get_simulations():
    return {"running_simulations": list(simulations.keys())}


@app.delete("/simulations/{simulation_id}")
async def delete_simulation(simulation_id: str):
    if simulation_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    simulations[simulation_id].kill()
    del simulations[simulation_id]
    return {"success": True}


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
