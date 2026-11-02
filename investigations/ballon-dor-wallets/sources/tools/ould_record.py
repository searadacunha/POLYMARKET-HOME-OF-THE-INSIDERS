import json,sys
sys.path.insert(0,'tools')
import case_chain as C
r=C.relay_record('0x909d9602d5ad975b2f30c66d4a058592306e2468a002dd0a691170b61677a6f1')
print(json.dumps(r,indent=0)[:1200])
