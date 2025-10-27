from azure.cli.core.azclierror import FileOperationError, InvalidArgumentValueError
from azure.mgmt.cognitiveservices.models import ConnectionCategory
from os import PathLike
from typing import IO, Any, AnyStr, Dict, List, Optional, Union

_ML_CONNECTION_TYPE_TO_COGNITIVE_SERVICES_CONNECTION_TYPE = {
    "PythonFeed": ConnectionCategory.PYTHON_FEED,
    "ContainerRegistry": ConnectionCategory.CONTAINER_REGISTRY,
    "Git": ConnectionCategory.GIT,
    "S3": ConnectionCategory.S3,
    "Snowflake": ConnectionCategory.SNOWFLAKE,
    "AzureSqlDb": ConnectionCategory.AZURE_SQL_DB,
    "AzureSynapseAnalytics": ConnectionCategory.AZURE_SYNAPSE_ANALYTICS,
    "AzureMySqlDb": ConnectionCategory.AZURE_MY_SQL_DB,
    "AzurePostgresDb": ConnectionCategory.AZURE_POSTGRES_DB,
    "ADLSGen2": ConnectionCategory.ADLS_GEN2,
    "Redis": ConnectionCategory.REDIS,
    "ApiKey": ConnectionCategory.API_KEY,
    "AzureOpenAI": ConnectionCategory.AZURE_OPEN_AI,
    "AzureOpenAi": ConnectionCategory.AZURE_OPEN_AI,
    "AIServices": ConnectionCategory.AI_SERVICES,
    "AiServices": ConnectionCategory.AI_SERVICES,
    "CognitiveSearch": ConnectionCategory.COGNITIVE_SEARCH,
    "CognitiveService": ConnectionCategory.COGNITIVE_SERVICE,
    "CustomKeys": ConnectionCategory.CUSTOM_KEYS,
    "AzureBlob": ConnectionCategory.AZURE_BLOB,
    "AzureOneLake": ConnectionCategory.AZURE_ONE_LAKE,
    "CosmosDb": ConnectionCategory.COSMOS_DB,
    "CosmosDbMongoDbApi": ConnectionCategory.COSMOS_DB_MONGO_DB_API,
    "AzureDataExplorer": ConnectionCategory.AZURE_DATA_EXPLORER,
    "AzureMariaDb": ConnectionCategory.AZURE_MARIA_DB,
    "AzureDatabricksDeltaLake": ConnectionCategory.AZURE_DATABRICKS_DELTA_LAKE,
    "AzureSqlMi": ConnectionCategory.AZURE_SQL_MI,
    "AzureTableStorage": ConnectionCategory.AZURE_TABLE_STORAGE,
    "AmazonRdsForOracle": ConnectionCategory.AMAZON_RDS_FOR_ORACLE,
    "AmazonRdsForSqlServer": ConnectionCategory.AMAZON_RDS_FOR_SQL_SERVER,
    "AmazonRedshift": ConnectionCategory.AMAZON_REDSHIFT,
    "Db2": ConnectionCategory.DB2,
    "Drill": ConnectionCategory.DRILL,
    "GoogleBigQuery": ConnectionCategory.GOOGLE_BIG_QUERY,
    "Greenplum": ConnectionCategory.GREENPLUM,
    "Hbase": ConnectionCategory.HBASE,
    "Hive": ConnectionCategory.HIVE,
    "Impala": ConnectionCategory.IMPALA,
    "Informix": ConnectionCategory.INFORMIX,
    "MariaDb": ConnectionCategory.MARIA_DB,
    "MicrosoftAccess": ConnectionCategory.MICROSOFT_ACCESS,
    "MySql": ConnectionCategory.MY_SQL,
    "Netezza": ConnectionCategory.NETEZZA,
    "Oracle": ConnectionCategory.ORACLE,
    "Phoenix": ConnectionCategory.PHOENIX,
    "PostgreSql": ConnectionCategory.POSTGRE_SQL,
    "Presto": ConnectionCategory.PRESTO,
    "SapOpenHub": ConnectionCategory.SAP_OPEN_HUB,
    "SapBw": ConnectionCategory.SAP_BW,
    "SapHana": ConnectionCategory.SAP_HANA,
    "SapTable": ConnectionCategory.SAP_TABLE,
    "Spark": ConnectionCategory.SPARK,
    "SqlServer": ConnectionCategory.SQL_SERVER,
    "Sybase": ConnectionCategory.SYBASE,
    "Teradata": ConnectionCategory.TERADATA,
    "Vertica": ConnectionCategory.VERTICA,
    "Pinecone": ConnectionCategory.PINECONE,
    "Cassandra": ConnectionCategory.CASSANDRA,
    "Couchbase": ConnectionCategory.COUCHBASE,
    "MongoDbV2": ConnectionCategory.MONGO_DB_V2,
    "MongoDbAtlas": ConnectionCategory.MONGO_DB_ATLAS,
    "AmazonS3Compatible": ConnectionCategory.AMAZON_S3_COMPATIBLE,
    "FileServer": ConnectionCategory.FILE_SERVER,
    "FtpServer": ConnectionCategory.FTP_SERVER,
    "GoogleCloudStorage": ConnectionCategory.GOOGLE_CLOUD_STORAGE,
    "Hdfs": ConnectionCategory.HDFS,
    "OracleCloudStorage": ConnectionCategory.ORACLE_CLOUD_STORAGE,
    "Sftp": ConnectionCategory.SFTP,
    "GenericHttp": ConnectionCategory.GENERIC_HTTP,
    "ODataRest": ConnectionCategory.O_DATA_REST,
    "Odbc": ConnectionCategory.ODBC,
    "GenericRest": ConnectionCategory.GENERIC_REST,
    "AmazonMws": ConnectionCategory.AMAZON_MWS,
    "Concur": ConnectionCategory.CONCUR,
    "Dynamics": ConnectionCategory.DYNAMICS,
    "DynamicsAx": ConnectionCategory.DYNAMICS_AX,
    "DynamicsCrm": ConnectionCategory.DYNAMICS_CRM,
    "GoogleAdWords": ConnectionCategory.GOOGLE_AD_WORDS,
    "Hubspot": ConnectionCategory.HUBSPOT,
    "Jira": ConnectionCategory.JIRA,
    "Magento": ConnectionCategory.MAGENTO,
    "Marketo": ConnectionCategory.MARKETO,
    "Office365": ConnectionCategory.OFFICE365,
    "Eloqua": ConnectionCategory.ELOQUA,
    "Responsys": ConnectionCategory.RESPONSYS,
    "OracleServiceCloud": ConnectionCategory.ORACLE_SERVICE_CLOUD,
    "PayPal": ConnectionCategory.PAY_PAL,
    "QuickBooks": ConnectionCategory.QUICK_BOOKS,
    "Salesforce": ConnectionCategory.SALESFORCE,
    "SalesforceServiceCloud": ConnectionCategory.SALESFORCE_SERVICE_CLOUD,
    "SalesforceMarketingCloud": ConnectionCategory.SALESFORCE_MARKETING_CLOUD,
    "SapCloudForCustomer": ConnectionCategory.SAP_CLOUD_FOR_CUSTOMER,
    "SapEcc": ConnectionCategory.SAP_ECC,
    "ServiceNow": ConnectionCategory.SERVICE_NOW,
    "SharePointOnlineList": ConnectionCategory.SHARE_POINT_ONLINE_LIST,
    "Shopify": ConnectionCategory.SHOPIFY,
    "Square": ConnectionCategory.SQUARE,
    "WebTable": ConnectionCategory.WEB_TABLE,
    "Xero": ConnectionCategory.XERO,
    "Zoho": ConnectionCategory.ZOHO,
    "GenericContainerRegistry": ConnectionCategory.GENERIC_CONTAINER_REGISTRY,
    "Elasticsearch": ConnectionCategory.ELASTICSEARCH,
    "OpenAI": ConnectionCategory.OPEN_AI,
    "OpenAi": ConnectionCategory.OPEN_AI,
    "Serp": ConnectionCategory.SERP,
    "BingLLMSearch": ConnectionCategory.BING_LLM_SEARCH,
    "Serverless": ConnectionCategory.SERVERLESS,
    "ManagedOnlineEndpoint": ConnectionCategory.MANAGED_ONLINE_ENDPOINT,
    # The following are from azure.ai.ml.constants._common.ConnectionTypes
    "Custom": ConnectionCategory.CUSTOM_KEYS,
    "AzureDataLakeGen2": ConnectionCategory.ADLS_GEN2,
    "AzureContentSafety": ConnectionCategory.COGNITIVE_SERVICE,
    "AzureSpeechServices": ConnectionCategory.COGNITIVE_SERVICE,
    "AzureAiSearch": ConnectionCategory.COGNITIVE_SEARCH,
    "AzureAiServices": ConnectionCategory.AI_SERVICES,
}


def get_valid_mlconn_types():
    return list(_ML_CONNECTION_TYPE_TO_COGNITIVE_SERVICES_CONNECTION_TYPE.keys())


def get_mapped_mlconn_type(ml_connection_type: str):
    from azure.ai.ml._utils.utils import _snake_to_camel as snake_to_camel
    normalized_name = snake_to_camel(ml_connection_type)
    return _ML_CONNECTION_TYPE_TO_COGNITIVE_SERVICES_CONNECTION_TYPE.get(normalized_name)


def from_ml_connection(mlconn):
    from azure.mgmt.cognitiveservices import models
    import azure.ai.ml.entities as ml_entities
    conn = None
    connection_category = get_mapped_mlconn_type(mlconn.type)
    if connection_category is None:
        raise InvalidArgumentValueError(
            f"Invalid connection type '{mlconn.type}'. ",
            recommendation=[
                "Verify that the connection type property is set to one of the following values:",
                ', '.join(get_valid_mlconn_types())])
    match type(mlconn.credentials):
        case ml_entities.PatTokenConfiguration:
            conn = models.PATAuthTypeConnectionProperties(
                credentials=models.ConnectionPersonalAccessToken(pat=mlconn.credentials.pat))
        case ml_entities.SasTokenConfiguration:
            conn = models.SASAuthTypeConnectionProperties(
                credentials=models.ConnectionSharedAccessSignature(sas=mlconn.credentials.sas_token))
        case ml_entities.UsernamePasswordConfiguration:
            conn = models.UsernamePasswordAuthTypeConnectionProperties(
                credentials=models.ConnectionUsernamePassword(
                    username=mlconn.credentials.username,
                    password=mlconn.credentials.password))
        case ml_entities.ManagedIdentityConfiguration:
            conn = models.ManagedIdentityAuthTypeConnectionProperties(
                credentials=models.ConnectionManagedIdentity(
                    client_id=mlconn.credentials.client_id,
                    resource_id=mlconn.credentials.resource_id,
                ))
        case ml_entities.ServicePrincipalConfiguration:
            conn = models.ServicePrincipalAuthTypeConnectionProperties(
                credentials=models.ConnectionServicePrincipal(
                    client_id=mlconn.credentials.client_id,
                    client_secret=mlconn.credentials.client_secret,
                    tenant_id=mlconn.credentials.tenant_id
                ))
        case ml_entities.AccessKeyConfiguration:
            conn = models.AccessKeyAuthTypeConnectionProperties(
                credentials=models.ConnectionAccessKey(
                    access_key_id=mlconn.credentials.access_key_id,
                    secret_access_key=mlconn.credentials.secret_access_key
                )
            )
        case ml_entities.ApiKeyConfiguration:
            conn = models.ApiKeyAuthConnectionProperties(
                credentials=models.ConnectionApiKey(key=mlconn.credentials.key)
            )
        case ml_entities.NoneCredentialConfiguration:
            conn = models.NoneAuthTypeConnectionProperties()
        case ml_entities.AccountKeyConfiguration:
            conn = models.AccountKeyAuthTypeConnectionProperties(
                credentials=models.ConnectionAccountKey(
                    key=mlconn.credentials.account_key
                )
            )
        case ml_entities.AadCredentialConfiguration:
            conn = models.AADAuthTypeConnectionProperties()
        case _:
            conn = models.AADAuthTypeConnectionProperties()
    conn.category = connection_category
    conn.target = mlconn.target
    conn.metadata = mlconn.metadata
    return conn


def load_connection_from_file(source: Union[str, PathLike, IO[AnyStr]],
                              params_override: Optional[List[Dict[str, Any]]] = None):
    """
    Load a connection from a JSON file or string.
    """
    from azure.ai.ml.entities._load_functions import load_connection
    cogsvc_connection = None
    ml_connection = None
    try:
        ml_connection = load_connection(
            source=source,
            params_override=params_override,
        )
        # The azure.ai.ml._workspace._ai_workspaces.connection.Connection type maps to the
        # azure.mgmt.cognitiveservices.models.ConnectionPropertiesV2 credentialed subclass type.
        # We need to convert it to the latter type before sending it to the API.
    except Exception as e:
        raise FileOperationError(f"Failed to load connection from {source}: {e}",
                                 recommendation="Check the file path and format.")
    cogsvc_connection = from_ml_connection(ml_connection)
    return cogsvc_connection
