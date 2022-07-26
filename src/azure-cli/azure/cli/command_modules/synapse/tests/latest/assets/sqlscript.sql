IF NOT EXISTS (SELECT * FROM sys.external_file_formats WHERE name = 'SynapseParquetFormat') 
	CREATE EXTERNAL FILE FORMAT [SynapseParquetFormat] 
	WITH ( FORMAT_TYPE = PARQUET)
GO

IF NOT EXISTS (SELECT * FROM sys.external_data_sources WHERE name = 'public_pandemicdatalake_blob_core_windows_net') 
	CREATE EXTERNAL DATA SOURCE [public_pandemicdatalake_blob_core_windows_net] 
	WITH (
		LOCATION   = 'https://pandemicdatalake.blob.core.windows.net/public', 
	)
Go

CREATE EXTERNAL TABLE [Test0830-1] (
	[id] int,
	[updated] date,
	[confirmed] int,
	[confirmed_change] int,
	[deaths] int,
	[deaths_change] smallint,
	[recovered] int,
	[recovered_change] int,
	[latitude] float,
	[longitude] float,
	[iso2] varchar(8000),
	[iso3] varchar(8000),
	[country_region] varchar(8000),
	[admin_region_1] varchar(8000),
	[iso_subdivision] varchar(8000),
	[admin_region_2] varchar(8000),
	[load_time] datetime2(7)
	)
	WITH (
	LOCATION = 'curated/covid-19/bing_covid-19_data/latest/bing_covid-19_data.parquet',
	DATA_SOURCE = [public_pandemicdatalake_blob_core_windows_net],
	FILE_FORMAT = [SynapseParquetFormat]
	)
GO

SELECT TOP 100 * FROM [Test0830-1]
GO
