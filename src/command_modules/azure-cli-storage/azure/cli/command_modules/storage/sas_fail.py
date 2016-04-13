from azure.storage.blob import BlockBlobService
from azure.storage import CloudStorageAccount

def this_fails():
    ACCOUNT_KEY = "lrrU4ZtdQiglpqAgDwVofHSD5mYGstSCyQolQh+Q/q1+PENdWLrN7G4SVmLGxPYGg+3hF9QF/THgXcK3sXPTA=="
    ACCOUNT_NAME = "travistestresourcegr3014"

    csa = CloudStorageAccount(account_name=ACCOUNT_NAME, account_key=ACCOUNT_KEY)
    sas_token = csa.generate_shared_access_signature()
    print('\n===Generated SAS Token ===')
    print(sas_token)

    bbs = BlockBlobService(account_name=ACCOUNT_NAME,sas_token=sas_token)
    results = bbs.list_containers()
    print('\n=== RESULTS ===')
    print(results)