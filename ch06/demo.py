"""Print an unverified review package from the scripted Chapter 6 workflow."""
import json
from workflow import prepare
if __name__=='__main__':print(json.dumps(prepare()[1],indent=2))
