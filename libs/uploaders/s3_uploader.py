#!/usr/bin/python3

import uuid
import boto3
from botocore.exceptions import ClientError
import logging
import cv2 as cv
import os


class S3Uploader:

    def __init__(self):
        session = boto3.session.Session(
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            region_name=os.environ.get("AWS_BUCKET_REGION")
        )
        self.s3_resource = session.resource('s3')
        self.logger = logging.getLogger(__name__)

    def upload_file(self, bucket_name, file_path, file_name, bucket_prefix):
        """Upload a file to an S3 bucket

        :param bucket_name: Name of the bucket
        :param file_path: Path to for the local file
        :param file_name: File name to upload
        :param bucket_path: Prefix where to upload the file in S3
        :return: True if file was uploaded, else False
        """
        bucket = self.s3_resource.Bucket(bucket_name)
        # List objects inside the prefix to check
        # A random hash is concatenated to the file name to improve performance on S3
        # https://realpython.com/python-boto3-aws-s3/#naming-your-files
        object_name = '-'.join([str(uuid.uuid4().hex[:6]), file_name])
        for s3_file in bucket.objects.filter(Prefix=bucket_prefix):
            uploaded_name = s3_file.key.split("/")[-1]
            if file_name in uploaded_name:
                # The file was previously uploaded, overwrite it
                object_name = uploaded_name

        # Upload the file
        self.logger.info(f'Uploading {file_path} as {bucket_prefix}/{object_name}')
        try:
            self.s3_resource.Bucket(bucket_name).upload_file(Filename=file_path, Key=f"{bucket_prefix}/{object_name}")
        except ClientError as e:
            self.logger.error(f'Error when uploading: {e}')
            return False
        return True

    def upload_cv_image(self, bucket, cv_image, file_name, bucket_path):
        """Upload an opencv image to a S3 bucket

        :param cv_image: Image to upload
        :param file_name: Base name for the image to be uploaded with
        :param bucket_path: Path where to upload the image in S3
        :return: True if file was uploaded, else False
        """

        # A random hash is concatenated to the file name to improve performance on S3
        # https://realpython.com/python-boto3-aws-s3/#naming-your-files
        object_name = ''.join([str(uuid.uuid4().hex[:6]), file_name])

        img = cv.imencode('.jpg', cv_image)[1].tobytes()

        # Upload the file
        self.logger.info(f'Uploading image as {bucket_path}/{object_name}')
        try:
            self.s3_resource.Bucket(bucket).put_object(Body=img, Key=f"{bucket_path}/{object_name}")
        except ClientError as e:
            self.logger.error(f'Error when uploading: {e}')
            return False
        return True
