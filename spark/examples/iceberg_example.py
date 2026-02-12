# Example: Working with Iceberg tables from Spark
# Location: spark/examples/iceberg_example.py

"""
Example Spark job demonstrating Iceberg table operations
"""

import sys
sys.path.insert(0, '/workspaces/Nexus-Data-Platform')

from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType
from datetime import datetime
from spark.iceberg_config import create_spark_session_with_iceberg


def create_tourism_iceberg_table(spark):
    """
    Create an Iceberg table from sample tourism data
    """
    print("🗂️  Creating Iceberg table...")
    
    # Create sample data
    schema = StructType([
        StructField("event_id", StringType(), True),
        StructField("event_name", StringType(), True),
        StructField("destination", StringType(), True),
        StructField("visitor_count", IntegerType(), True),
        StructField("revenue", DoubleType(), True),
        StructField("event_date", TimestampType(), True),
    ])
    
    data = [
        ("EVT001", "Beach Festival", "Maldives", 500, 25000.00, datetime.now()),
        ("EVT002", "Mountain Trek", "Nepal", 200, 15000.00, datetime.now()),
        ("EVT003", "Cultural Show", "Vietnam", 300, 18000.00, datetime.now()),
    ]
    
    df = spark.createDataFrame(data, schema=schema)
    
    # Write to Iceberg table (creates if not exists)
    df.writeTo("iceberg.tourism_db.events") \
        .createOrReplace() \
        .append()
    
    print("✅ Iceberg table created: iceberg.tourism_db.events")
    return df


def query_iceberg_table(spark):
    """
    Query Iceberg table
    """
    print("\n📊 Querying Iceberg table...")
    
    df = spark.sql("SELECT * FROM iceberg.tourism_db.events")
    df.show()
    
    return df


def update_iceberg_table(spark):
    """
    Update Iceberg table (ACID transaction)
    """
    print("\n✏️  Updating Iceberg table...")
    
    # Iceberg supports UPDATE operation
    spark.sql("""
        UPDATE iceberg.tourism_db.events 
        SET visitor_count = visitor_count + 100
        WHERE destination = 'Maldives'
    """)
    
    print("✅ Updated records in Iceberg table")


def delete_iceberg_records(spark):
    """
    Delete records from Iceberg table (ACID transaction)
    """
    print("\n🗑️  Deleting from Iceberg table...")
    
    spark.sql("""
        DELETE FROM iceberg.tourism_db.events
        WHERE visitor_count < 300
    """)
    
    print("✅ Deleted records from Iceberg table")


def show_iceberg_history(spark):
    """
    Show Iceberg table history (time-travel capability)
    """
    print("\n⏱️  Iceberg table history...")
    
    history_df = spark.sql("""
        SELECT * FROM iceberg.tourism_db.events.history
    """)
    
    if history_df.count() > 0:
        history_df.show()
    else:
        print("No history available")


def snapshot_iceberg_table(spark):
    """
    Create a snapshot/backup of Iceberg table
    """
    print("\n📸 Creating snapshot...")
    
    # Query specific snapshot
    snapshot_df = spark.sql("""
        SELECT * FROM iceberg.tourism_db.events
        VERSION AS OF 1  -- Query specific version
    """)
    
    print("✅ Snapshot created")
    return snapshot_df


def main():
    """
    Run Iceberg examples
    """
    print("=" * 60)
    print("🧊 Apache Iceberg + Spark Examples")
    print("=" * 60)
    
    # Initialize Spark with Iceberg
    spark = create_spark_session_with_iceberg("IcebergExample")
    
    try:
        # Create Iceberg table
        create_tourism_iceberg_table(spark)
        
        # Query the table
        query_iceberg_table(spark)
        
        # Update (ACID transaction)
        update_iceberg_table(spark)
        
        # Query after update
        print("\n📊 After UPDATE:")
        query_iceberg_table(spark)
        
        # Show table metadata
        print("\n📋 Iceberg table metadata:")
        spark.sql("DESCRIBE DETAIL iceberg.tourism_db.events").show()
        
        print("\n✅ All Iceberg operations completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
