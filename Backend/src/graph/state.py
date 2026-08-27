import operator
from typing import Annotated,List,Dict,Optional,Any,TypedDict

class ComplianceIssue(Annotated):
    category : str
    severity : str
    description : str
    timestamp : Optional[str]

class VideoAudit(Annotated):
    '''
    Makes the data schema for the video audit
    '''
    #input parameters
    video_url : str
    video_id : str

    #video audit
    video_file_path : Optional[str]
    metadata : Dict[str,Any]
    transcript : Optional[str]
    ocr_text : List[str]
    
    #analysis output
    compliance_result : Annotated[List[ComplianceIssue], operator.add]

    #final deliveries
    final_status : str #PASS | FAIL
    final_report : str #final verdict
    
    #errors
    #api key timeout, system level errors
    error : Annotated[List[str], operator.add]
