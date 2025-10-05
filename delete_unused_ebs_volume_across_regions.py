#!/usr/bin/env python3
import boto3
import logging
from botocore.exceptions import ClientError

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def delete_unattached_volumes():
    """Delete unattached (available) EBS volumes across all AWS regions."""
    ec2 = boto3.client("ec2")
    regions = [r["RegionName"] for r in ec2.describe_regions()["Regions"]]

    for region in regions:
        logger.info(f"Checking region: {region}")
        ec2_reg = boto3.client("ec2", region_name=region)

        paginator = ec2_reg.get_paginator("describe_volumes")
        for page in paginator.paginate(Filters=[{"Name": "status", "Values": ["available"]}]):
            for volume in page.get("Volumes", []):
                volume_id = volume["VolumeId"]
                attachments = volume.get("Attachments", [])

                if not attachments:  # Unattached
                    try:
                        logger.info(f"Deleting unattached volume {volume_id} in {region}")
                        ec2_reg.delete_volume(VolumeId=volume_id)
                        logger.info(f"Deleted {volume_id} in {region}")
                    except ClientError as e:
                        logger.error(f"Could not delete {volume_id} in {region}: {e}")
                else:
                    logger.info(f"Volume {volume_id} in {region} is attached, skipping")

def lambda_handler(event, context):
    """AWS Lambda entry point."""
    delete_unattached_volumes()
    return {
        "statusCode": 200,
        "body": "Completed volume deletion process"
    }

if __name__ == "__main__":
    delete_unattached_volumes()
