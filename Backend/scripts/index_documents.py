import os
import logging
import glob
from dotenv import load_dotenv
load_dotenv(override=True)

#pypdf loader and text spilitters
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

#Azure search and Azure embeddings 
from langchain_azure_ai.vectorstores import AzureSearch
from langchain_azure_ai.embeddings import AzureAIOpenAIApiEmbeddingsModel

logging.basicConfig(
    level= logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("indexer")

def index_docs():
    original_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(original_path , "../data")

    logging.info("="*60)
    logging.info(f"AZURE_SEARCH_ENDPOINT = {os.getenv("AZURE_SEARCH_ENDPOINT")}")
    logging.info(f"AZURE_SEARCH_INDEX_NAME = {os.getenv("AZURE_SEARCH_INDEX_NAME")}")
    logging.info(f"AZURE_MISTRAL_ENDPOINT = {os.getenv("AZURE_MISTRAL_ENDPOINT")}")
    logging.info(f"AZURE_MISTRAL_VERSION = {os.getenv("AZURE_MISTRAL_VERSION")}")
    logging.info(f"AZURE_OPENAI_EMBEDDING_DEPLOYMENT = {os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT" , "text-embedding-3-small")}")
    logging.info("="*60)

    required_vars = [
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_INDEX_NAME",
        "AZURE_MISTRAL_ENDPOINT",
        "AZURE_SEARCH_API_KEY",
        "AZURE_MISTRAL_KEY",
    ]

    missing_var = [var for var in required_vars if not os.getenv(var)]
    if missing_var:
        logging.error(f"Missing requirements env variable : {missing_var}")
        logging.error("check your env variables")

    #initialise embedding model and convert into vectors
    try:
        embedding_model = AzureAIOpenAIApiEmbeddingsModel(
            AZURE_MISTRAL_KEY = os.getenv("AZURE_MISTRAL_KEY"),
            AZURE_MISTRAL_ENDPOINT = os.getenv("AZURE_MISTRAL_ENDPOINT"),
            AZURE_MISTRAL_VERSION = os.getenv("AZURE_MISTRAL_VERSION"),
            AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
        )
        logging.info("succesfully integrated the api keys of the embdded model")

    except Exception as e:
        logging.error(f"Error occured when loading the embedding model due to {e} ")
        logging.error("Failed to load the embedding model ")

    #initialise azure search
    try:
        vector_store = AzureSearch(
            AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT"),
            AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY"),
            index_name = index_name,
            embedding_function = embedding_model.embed_query,
        )
        logging.info(f"azure ai search configuration successfully installed with index name : {index_name}")
    except Exception as e:
        logging.error(f"Failed to configure Azure Search due to {e}")
        logging.error("Make sure every api keys or end pints are correct")

    #process the pdf
    pdf_file = glob.glob(os.path.join(file_path , "*.pdf"))
    if not pdf_file:
        logging.warning(f"pdf path is not there fix it : {file_path}")
    logging.info("path_file taken succesfully")

    all_splits=[]
    for pdfs in pdf_file:
        try:
            logging.info(f"taking the pdf one by one : {os.path.basename(pdfs)} ")
            #loading the pdf
            loader = PyPDFLoader(pdfs)
            raw_docs = loader.load()

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size = 1000,
                chunk_overlap = 200,
            )

            try:
                splitted_docs = text_splitter.split_documents(raw_docs)
                for split in splitted_docs:
                    split.metadata["source"] = os.path.basename(pdf_file)

                all_splits.extend(splitted_docs)
                logging.info(f"splitted into {len(splitted_docs)} chunks")

                if splitted_docs:
                    logging.info("documents spllited")

            except Exception as e:
                logging.error(f"spllitting couldnot happen from raw docs due to : {e}")

        except Exception as e:
            logging.error(f"splliting failed due to : {e}")

        #adding the splitted documents in vector database to azure
        if all_splits:
            logging.info(f"storing {len(all_splits)} chunks in database with index name = {index_name} ")
            try:
                vector_store.add_documents(documents=all_splits )
                logging.info("="*60)
                logging.info("stored all the documents in the database in Azure")
                logging.info("="*60)

            except Exception as e:
                logging.error(f"error occured while storing the embedded chunks in the database due to {e}")

        else:
            logging.warning("no documents processed")

if __name__ == "__main__":
    index_docs()
