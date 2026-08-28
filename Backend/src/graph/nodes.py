import re
import os
import json
import logging
from typing import Any,List,Dict

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage,HumanMessage
from langchain_azure_ai.vectorstores import AzureSearch
from langchain_azure_ai.chat_models import AzureAIOpenAIApiChatModel
from langchain_azure_ai.embeddings import AzureAIOpenAIApiEmbeddingsModel

#importing the nodes
from state import VideoAudit,ComplianceIssue

#importing the video indexer to extract the data
from services import video_indexer

#configuring the logger
logger = logging.getLogger("brand-video")
logging.basicConfig(level=logging.INFO)


def Video_indexer_node(state : VideoAudit) -> Dict[str , Any]:
    #input parameters
    video_url_input = state.get("video_url")
    video_id_input =  state.get("video_id")

    logging.INFO("Fetched Input parameters of the video")
    local_path = "temporary_video.mp4"
    vi_service = video_indexer()

    try:
        #video downloader and storing into a temporary path
        if "youtube.com" in video_url_input or "youtube.be" in video_url_input:
            logging.INFO{"video downloading ....."}
            video_download = vi_service.download_video(video_url_input , output_path = local_path)
        else:
            raise Exception("pls provide a correct url")

        #uploading in azure video indexer
        video_indexer_upload = vi_service.upload_video(video_id_input = video_id_input , local_path = local_path)
        logging.INFO("uploading success") 

        if os.path.exists(local_path):
            os.remove(local_path)

        raw_context = vi_service.wait_for_extract(video_id_input = video_id_input)

        clean_context = vi_service.clean_extract(raw_context)

    except Exception as e:
        logging.error(f"Video Context Extraction Failed due to : {e}")
        return{
            "error" : str(e),
            "final_status" : "FAIL",
            "ocr_text" : [],
            "transcript" : "",
        }

def audit_content_node(state : VideoAudit)-> Dict[str , Any]:
    '''
        take the relevant info from the documents
        basically the node function
    '''
    logging.INFO("fetching the transcript for furthur details")
    transcript = state.get("transcript")
    if not transcript:
        logging.warning("transcript not found skipping audit...")
        return{
            "final_status" : "FAIL",
            "final_report" : "Audit Failed",
        }

    llm = AzureAIOpenAIApiChatModel(
        AZURE_MISTRAL_DEPLOYMENT = os.getenv("AZURE_MISTRAL_DEPLOYMENT"),
        AZURE_MISTRAL_VERSION = os.getenv("AZURE_MISTRAL_VERSION"),
        temperature=0.0,
    )

    embedding_model = AzureAIOpenAIApiEmbeddingsModel(
        AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-3-small",
        AZURE_MISTRAL_KEY= os.getenv("AZURE_MISTRAL_KEY"),
    )

    AI_Search = AzureSearch(
        AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT"),
        AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME"),
        AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY"),
    )

    