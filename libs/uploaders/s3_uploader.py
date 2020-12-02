#!/usr/bin/python3

import uuid
import boto3
from botocore.exceptions import ClientError
import logging
import cv2 as cv


class S3Uploader:

    def __init__(self):
        session = boto3.session.Session()
        self.s3_resource = session.resource('s3')
        self.logger = logging.getLogger(__name__)

    def upload_file(self, bucket, file_path, file_name, bucket_path):
        """Upload a file to an S3 bucket

        :param file_path: Path to where the local image is stored
        :param file_name: File to upload
        :param bucket_path: Path where to upload the image in S3
        :return: True if file was uploaded, else False
        """

        # A random hash is concatenated to the file name to improve performance on S3
        # https://realpython.com/python-boto3-aws-s3/#naming-your-files
        object_name = ''.join([str(uuid.uuid4().hex[:6]), file_name])

        # Upload the file
        self.logger.info(f'Uploading {file_path}/{file_name} as {bucket_path}/{object_name}')
        try:
            self.s3_resource.Bucket(bucket).upload_file(Filename=f"{file_path}/{file_name}", Key=f"{bucket_path}/{object_name}")
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
