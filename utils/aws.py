import boto3
from io import BytesIO
from utils.embedding import get_text_chunks, get_vector_store

session = boto3.Session(
    profile_name='Developer-Access-070677990097'
)

s3 = session.client('s3')

bucket_name = 'hrdatamart'
resource_path = 'polices/'

response = s3.list_objects_v2(
    Bucket=bucket_name,
    Prefix=resource_path
)

def fetch_resources():
    if 'Contents' in response:
        for obj in response['Contents']:
            file_name = obj['Key'].split('/')[1]
            file_obj = BytesIO()
            s3.download_fileobj(bucket_name, obj['Key'], file_obj)
            file_obj.seek(0)
            data_text = file_obj.read().decode('utf-8')
            
            chunks = get_text_chunks(data_text)
            get_vector_store(chunks, "llama-3", obj["ETag"], file_name)
            
            print(f"File Name: {file_name}, Size: {len(data_text)} bytes")