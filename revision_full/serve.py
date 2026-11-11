"""Published checkpoint, published padding and bounded-memory attention."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from serve_pruner import model,app
from revision_glm.memory_attention import install as install_attention
from revision_full.paper_padding import install as install_padding
import uvicorn
install_attention(model)
install_padding()
if __name__=='__main__':uvicorn.run(app,host='127.0.0.1',port=8000)
