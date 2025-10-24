import base64
from typing import Dict, Union
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
from agent_graph import AGENT_APP
from config import GraphState, NEW_CATALOG_ITEM_TEMPLATE

# FastAPI Implementation

app = FastAPI(title="Supplier Catalog Agent API", version="1.0")

@app.post("/process_catalog_image/", 
          summary="Upload a catalog image to trigger the LangGraph agent",
          response_model=Dict[str, Union[str, list, dict]])
async def process_catalog_image(file: UploadFile = File(..., description="Image file (PNG or JPEG) of the supplier catalog.")):
    """
    Accepts an image file, base64 encodes it, and triggers the LangGraph workflow 
    to extract data, validate it, update the database, and send an email.
    """
    
    # 1. Read and Base64 Encode the uploaded image
    try:
        if file.content_type not in ["image/jpeg", "image/png"]:
             raise HTTPException(status_code=400, detail="Only JPEG and PNG images are accepted.")

        image_bytes = await file.read()
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read or encode file: {e}")

    # 2. Prepare the Initial State for LangGraph
    initial_state = GraphState(
        encoded_image=encoded_image,
        extraction_template=NEW_CATALOG_ITEM_TEMPLATE.copy(),
        extracted_item={},
        historical_df=pd.DataFrame(),
        factors=[],
        suggested_status="",
        final_result={},
        row_data_for_db={},
        email_subject="",
        email_body_html=""
    )

    # 3. Invoke the LangGraph Agent
    print(f"\n--- ⚡️ API Triggered: Processing {file.filename} ---")
    try:
        final_state = AGENT_APP.invoke(initial_state)
    except Exception as e:
        print(f"FATAL LANGGRAPH ERROR: {e}")
        # Return a 500 if the agent workflow fails
        raise HTTPException(status_code=500, detail=f"LangGraph agent failed to complete the process: {e}")

    # 4. Return the Final Result
    return JSONResponse(content={
        "status": "Success",
        "suggested_status": final_state['suggested_status'],
        "flags": final_state['factors'],
        "extracted_data": final_state['final_result'],
        "database_entry": final_state['row_data_for_db'],
        "summary": f"Catalog item processed. Status: {final_state['suggested_status']}. Email generation attempted."
    })