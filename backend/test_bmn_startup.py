import uvicorn
import sys
import os

sys.path.insert(0, os.path.abspath("."))

if __name__ == "__main__":
    uvicorn.run("bmn_app:app", host="127.0.0.1", port=5004, reload=True)
