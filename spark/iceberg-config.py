# Spark Configuration for Apache Iceberg
# Location: spark/iceberg-config.py

"""
Iceberg Configuration for Spark
This file contains helper functions to configure Spark with Iceberg support
"""

def get_iceberg_spark_config():
    """
    Returns Spark session configuration for Iceberg support
    
    Returns:
        dict: Configuration dictionary for Spark session builder
    """
    return {
        # Iceberg packages
        "spark.jars.packages": (
            "org.apache.iceberg:iceberg-spark-runtime-3.5_2.13:1.4.0,"
            "org.apache.iceberg:iceberg-aws:1.4.0,"
            "software.amazon.awssdk:s3:2.23.0,"
            "software.amazon.awssdk:sts:2.23.0"
        ),
        
        # Iceberg catalog configuration
        "spark.sql.catalog.iceberg": "org.apache.iceberg.spark.SparkCatalog",
        "spark.sql.catalog.iceberg.type": "rest",
        "spark.sql.catalog.iceberg.uri": "http://iceberg-rest:8080",
        "spark.sql.catalog.iceberg.warehouse": "s3://iceberg-warehouse/",
        
        # S3/MinIO configuration
        "spark.hadoop.fs.s3a.endpoint": "http://minio:9000",
        "spark.hadoop.fs.s3a.access.key": "minioadmin",
        "spark.hadoop.fs.s3a.secret.key": "minioadmin123",
        "spark.hadoop.fs.s3a.path.style.access": "true",
        "spark.hadoop.fs.s3a.impl": "org.apache.hadoop.fs.s3a.S3AFileSystem",
        
        # Enable Iceberg SQL extensions
        "spark.sql.extensions": "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
        
        # Set Iceberg as default catalog
        "spark.sql.defaultCatalog": "iceberg",
        
        # Performance tuning
        "spark.sql.iceberg.merge.preserve-order": "false",
        "spark.sql.iceberg.split-open-file-cost": "4194304",  # 4MB
    }


def initialize_spark_with_iceberg(spark):
    """
    Initialize a Spark session with Iceberg support
    
    Args:
        spark: SparkSession object
        
    Returns:
        SparkSession: Configured Spark session
    """
    # Enable Iceberg SQL extensions
    spark.sparkContext._jsc.hadoopConfiguration().set("fs.s3a.endpoint", "http://minio:9000")
    spark.sparkContext._jsc.hadoopConfiguration().set("fs.s3a.access.key", "minioadmin")
    spark.sparkContext._jsc.hadoopConfiguration().set("fs.s3a.secret.key", "minioadmin123")
    spark.sparkContext._jsc.hadoopConfiguration().set("fs.s3a.path.style.access", "true")
    
    return spark


def create_spark_session_with_iceberg(app_name="IcebergApp"):
    """
    Create a Spark session with Iceberg support
    
    Args:
        app_name (str): Spark application name
        
    Returns:
        SparkSession: Configured Spark session with Iceberg
    """
    from pyspark.sql import SparkSession
    
    config = get_iceberg_spark_config()
    
    builder = SparkSession.builder.appName(app_name)
    
    for key, value in config.items():
        builder = builder.config(key, value)
    
    spark = builder.getOrCreate()
    
    return initialize_spark_with_iceberg(spark)


# Example usage:
# spark = create_spark_session_with_iceberg()
# df = spark.sql("SELECT * FROM iceberg.tourism_db.events")
