from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse
import pandas as pd
import io
from classify import classify
import tempfile
import os

app = FastAPI()

REQUIRED_COLUMNS = ['sources', 'log_message']  # Replace with your actual required columns

@app.post("/classify")
async def classify_logs(file: UploadFile):
    # Check if the file is CSV
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    # Read the uploaded file
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV file: {str(e)}")
    
    # Validate columns
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(missing_columns)}"
        )
    
    # Process the data using classify function
    try:
        df["Lable"] = classify(list(zip(df['sources'], df['log_message'])))   
        
        # Create temporary file to store results
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
            df.to_csv(temp_file.name, index=False)
            temp_path = temp_file.name
        
        # Return the file as response
        return FileResponse(
            path=temp_path,
            filename="classification_results.csv",
            media_type="text/csv",
            background=lambda: os.unlink(temp_path)  # Delete temp file after sending
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification error: {str(e)}")

@app.get("/Test")
async def root():
    return {"message": "Log Classification API"}