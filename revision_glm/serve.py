"""Serve the published weights with bounded-memory, full-context fusion attention."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from serve_pruner import model,app
from revision_glm.memory_attention import install
import uvicorn
install(model)
if __name__=='__main__':uvicorn.run(app,host='127.0.0.1',port=8000)
