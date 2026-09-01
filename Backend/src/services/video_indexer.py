import os
import time
import logging
from urllib import response
from langchain_mistralai import data
import requests
import yt_dlp

from azure.identity import DefaultAzureCredential

logger = logging.getLogger("Video_indexer")

class video_indexer:
    def __init__(self):
        self.AZURE_VI_NAME = os.getenv("AZURE_VI_NAME")
        self.AZURE_VI_LOCATION = os.getenv("AZURE_VI_LOCATION")
        self.AZURE_VI_ACCOUNT_ID = os.getenv("AZURE_VI_ACCOUNT_ID")
        self.AZURE_SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
        self.AZURE_RESOURCE_GROUP = os.getenv("AZURE_RESOURCE_GROUP")
        self.credential = DefaultAzureCredential()

    #generate the ARM token for the Azure video indexer
    def get_access_token(self):
        try:
            token_obj = self.credential.get_token("https://management.azure.com/default")
            return token_obj.token
        except Exception as e:
            logger.error(f"Error occurred while fetching the ARM token for Azure Video Indexer due to {e}")
            raise

    #Exchanging the ARM token for the Azure Video Indexer access token
    def get_account_token(self , arm_access_token):
        url = (
            f"https://management.azure.com/subscriptions/{self.AZURE_SUBSCRIPTION_ID}/",
            f"resourceGroups/{self.AZURE_RESOURCE_GROUP}/providers/Microsoft.VideoIndexer/"
            f"provider/Microsoft.VideoIndexer/accounts/{self.AZURE_VI_ACCOUNT_ID}/"
            f"generateAccessToken?api-version=2021-11-10-preview"
        )
        headers = {
            "Authorization" : f"Bearer {arm_access_token}"
        }
        payload ={
            "permissionType" : "Contributor"
        }
        response = requests.get( url , json = payload , headers = headers)
        if response.status_code != 200:
            raise Exception(f"Failed to get the Azure Video Indexer access token. Status code: {response.status_code}, Response: {response.text}")
            
        return response.json().get("accessToken")

    #download the video from yt temporarily using 'yt-dlp'
    def download_video(self , video_url , output_path="temp_video.mp4"):
        ydf_opts = {
            "format" : "best[ext=mp4]",
            "outtmpl" : output_path,
            "quiet" : True,
            "overwrite" : True,
        }

        try:
            with yt_dlp.YoutubeDL(ydf_opts) as ydl:
                ydl.download([video_url])
                logger.info(f"Video download succesful")
                return output_path
        except Exception as e:
            raise Exception(f"Failed to download video from {video_url} due to {e}")

    #Upload the video to Azure Video Indexer and get the video ID
    def upload_video(self , video_id_input , local_path):
        try:
            arm_token = self.get_access_token()
            vi_token = self.get_account_token(arm_token)

            url = f"https://api.videoindexer.ai/{self.AZURE_VI_LOCATION}/Accounts/{self.AZURE_VI_ACCOUNT_ID}/Videos"

            params ={
                "name" : video_id_input,
                "privacy" : "Private",
                "accessToken" : vi_token,
                "indexingPreset" : "Default",
            }
            logger.info(f"Uploading video to Azure Video Indexer...")

            with open(local_path , "rb") as video_file:
                files = {"file" : video_file}
                response = requests.post( url , params = params, files = files)

            if response.status_code !=200:
                raise Exception(f"Failed to upload in Azure Video Indexer. Status code : {response.status_code}, Response : {response.text}")
            
        except Exception as e:
            raise Exception(f"Failed to upload video to Azure Video Indexer due to {e}")

    #wait for the video to upload and get processed and get the transcript and ocr text
    def wait_for_extract(self, video_id_input):
        logger.info(f"Waiting for video processing to complete...")
        while True:
            arm_token = self.get_access_token()
            vi_token = self.get_account_token(arm_token)

            url = f"https://api.videoindexer.ai/{self.AZURE_VI_LOCATION}/Accounts/{self.AZURE_VI_ACCOUNT_ID}/Videos"
            params = { "accessToken" : vi_token}
            response = requests.get(url , params = params)

            state = data.get("state")
            if state == "Processed":
                logger.info(f" Video processing completed successfully.")
            elif state == "Failed":
                raise Exception(f"Video processing failed. State: {state}")
            elif state == "Quanrrentied":
                raise Exception(f"Video quarrentined , copyright Issues/current policy violation")
            logger.info(f"waiting 30s....")
            time.sleep(30)

    #clean the extracted data and return the transcript and ocr text
    def clean_extract(self, raw_context):
        transcript_lines = []
        for v in raw_context.get("videos" , []):
            for insight in v.get("insights" , []).get("transcript" , []):
                transcript_lines.append(insight.get("text"))

        ocr_text = []
        for v in raw_context.get("videos"):
            for insight in v.get("insights",[]).get("ocr",[]):
                ocr_text.append(insight.get("text"))

        return{
            "transcript" : transcript_lines,
            "ocr_text" : ocr_text,
            "video_metadata" : {
                "duration" : raw_context.get("SummarizedInsights").get("durationInSeconds"),
                "platform" : "youtube",
            }
        }