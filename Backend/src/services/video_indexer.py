import os
import time
import logging
from urllib import response
import requests
import yt_dlp

from azure.identity import DefaultAzureCredential

logger = logging.getLogger("Video_indexer")

class VideoIndexer:
    def __init__(self):
        self.AZURE_VI_NAME = os.getenv("AZURE_VI_NAME")
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
    def yt_download(self , video_url , output_path="temp_video.mp4"):
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
    