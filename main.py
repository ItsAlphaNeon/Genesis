import json
import os
import logging as Logging
from fastapi import FastAPI, HTTPException, Request, Response, status
from pydantic import BaseModel
from gpt import ai_combine_terms, get_openai_key, ai_combine_terms_mix
from datetime import datetime, timedelta
from collections import deque
import asyncio

app = FastAPI(title="Genesis", debug=True)

request_queue = deque(maxlen=1)
queue_lock = asyncio.Lock()

class CombineTerms(BaseModel):
    terms: list


@app.get("/Online")
async def trigger_function():
    print("Sent Online")
    return "Online"

@app.post("/Combine", response_model=dict)
async def combine_terms(request_body: CombineTerms):
    # Retrieve the 'terms' field from the request body which is a pydantic model
    terms = request_body.terms
    print(terms)  # debug

    # Ensure that two terms have been provided
    if not terms or len(terms) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two terms must be provided.",
        )

    # Sort terms for consistent ordering
    terms_sorted = sorted(terms)
    # Check the database for existing terms combination
    existing_combination = check_database(terms_sorted[0], terms_sorted[1])
    if existing_combination:
        # Return the combination if it exists, no need to queue since no AI call is needed
        return existing_combination

    # The AI call is needed, thus queueing is necessary
    async with queue_lock:
        current_time = datetime.now()
        # If the queue is full, check to see if we should allow a new AI request.
        if len(request_queue) == 2:
            time_diff = current_time - request_queue[0]
            if time_diff.total_seconds() < 5:
                print("AI request queued. Waiting for available slot.")
                await asyncio.sleep(5 - time_diff.total_seconds())
        # Enqueue current request timestamp as we are now going to use the AI.
        request_queue.append(current_time)

    try:
        # Call the AI function since the terms are not in the database
        result = await ai_combine_terms(terms_sorted[0], terms_sorted[1])  # This can be switched with ai_combine_terms_mix
        print(result)  # debug
        
        # Parse the AI result to a dictionary, if it's not already
        if isinstance(result, str):
            result_dict = json.loads(result)
        else:  # if the result is already a dict
            result_dict = result
        
        # Check the database for any entries with a matching result, to get the emoji and color
        matching_entry = find_matching_database_entry(result_dict["result"])
        if matching_entry:
            result_dict["emoji"] = matching_entry["emoji"]
            result_dict["color"] = matching_entry["color"]
            print("Found a matching result in the database: ", matching_entry)
        else:
            # If no entry is found, use the emoji and color from the AI result
            print("No matching result found in the database")
        
        print(result_dict)  # debug
        
        # Add the 'rarity' field to the result dictionary
        result_dict["rarity"] = "0.0"
        # Write the new combination to the database
        write_to_database(
            terms=terms_sorted,
            result=result_dict["result"],
            explanation=result_dict["explanation"],
            emoji=result_dict["emoji"],
            color=result_dict["color"],
            rarity=result_dict["rarity"]
        )
        # Return the new combination
        return result_dict
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

def find_matching_database_entry(result):
    with open("database.txt", "r") as file:
        data = json.load(file)
    for key, value in data.items():
        if value["result"] == result:
            return value
    return None


@app.exception_handler(400)
async def bad_request_exception_handler(request: Request, exc: HTTPException):
    return Response(
        content=exc.detail, status_code=exc.status_code, media_type="application/json"
    )

uvicorn_access = Logging.getLogger("uvicorn.access")
uvicorn_access.disabled = True
Logger = Logging.getLogger("uvicorn")
Logger.setLevel(Logging.getLevelName(Logging.DEBUG))


def check_if_database_exists():
    if not os.path.isfile("database.txt"):
        print("Creating database")
        with open("database.txt", "w") as file:
            json.dump({}, file)
        print("Database created")
    elif os.path.isfile("database.txt"):
        with open("database.txt", "r+") as file:
            if file.read() == "":
                file.seek(0)
                json.dump({}, file)
                print("Database Empty JSON created")
    else:
        print("Database exists")


def update_rarity(rarity: float) -> float:
    # Assuming that rarity cannot be more than 1.0 (completely common)
    if rarity >= 1.0:
        return rarity
    else:
        return rarity + 0.1

def check_database(term1: str, term2: str) -> dict:
    with open("database.txt", "r") as file:
        data = json.load(file)
    
    combination_key = ":".join(sorted([term1, term2]))
    combination_data = data.get(combination_key)
    
    # If combination exists, update its rarity
    if combination_data:
        current_rarity = float(combination_data["rarity"])
        # Update rarity before returning the combination
        new_rarity = update_rarity(current_rarity)
        combination_data["rarity"] = str(new_rarity)
        
        # Write updated rarity back to the database
        write_to_database(
            terms=[term1, term2], 
            result=combination_data["result"],
            explanation=combination_data["explanation"],
            emoji=combination_data["emoji"],
            color=combination_data["color"],
            rarity=str(new_rarity)
        )
        
    return combination_data

def write_to_database(
    terms: list, result: str, explanation: str, emoji: str, color: str, rarity: str
):
    with open("database.txt", "r+") as file:
        data = json.load(file)
        combination_key = ":".join(terms)
        # Update the entry if the combination exists
        data[combination_key] = {
            "result": result,
            "explanation": explanation,
            "emoji": emoji,
            "rarity": rarity,
            "color": color,
        }
        file.seek(0)
        file.truncate()
        json.dump(data, file, indent=4)

if __name__ == "__main__":
    check_if_database_exists()
    get_openai_key()
    print("Ready")
    import uvicorn

    uvicorn.run(app, host="localhost", port=5000, log_level="debug")
