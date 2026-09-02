from pprint import pprint
import logging
import  uuid
import json
from Backend.src.graph.workflow import Workflow

from dotenv import load_dotenv
load_dotenv(override=True)

logging.basicConfig(
    level=logging.INFO,
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    )

logger = logging.getLogger("final_main")

def create_main():
    session_id = str(uuid.uuid4())
    logging.info(f"Starting the session with session_id: {session_id}")

    initial_input = {
        "video_url": "https://www.youtube.com/watch?v=example_video_id",

        "video_id": f"vid_{session_id[:8]}",

        "compliance_results": [],
    }

    print(f"input payload : {json.dumps(initial_input , indent = 4)}")

    try:
        workflow = Workflow.invoke(initial_input)

        print(f"Video Id : {workflow.get('video_id')}")
        print(f"STATUS : {workflow.get('status')}")
        results = workflow.get('compliance_results', [])

        if results:
            for issues in results:
                print(f" = [{issues.get('severity')}] , {issues.get('category')} , {issues.get('description')}")

        else:
            print("No compliance issues found.")

        print(f"Final output \n {workflow.get('final_report')}")

    except Exception as e:
        logging.error(f"An error occurred: {e}")


if __name__ == "__main__":
    create_main()
