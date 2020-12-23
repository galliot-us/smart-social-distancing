from pydantic import Field, validator
from typing import List, Optional

from .base import OptionalSectionConfig, SnakeModel


class PeriodicTaskDTO(OptionalSectionConfig):
    liveInterval: Optional[int] = Field(example=10)
    backupInterval: Optional[int] = Field(example=30)
    backupS3Bucket: Optional[str] = Field(example="your-s3-bucket")

    @validator("name")
    def validate_name(cls, value):
        if value not in ["metrics", "s3_backup"]:
            raise ValueError(f"Not supported periodic task named: {value}")
        return value


class MetricsTaksDTO(PeriodicTaskDTO):
    liveInterval: int = Field(example=10)


class S3Backup(PeriodicTaskDTO):
    backupInterval: Optional[int] = Field(example=30)
    backupS3Bucket: str = Field(example="your-s3-bucket")


class PeriodicTaskListDTO(SnakeModel):
    periodicTasks: List[PeriodicTaskDTO]


def validate_periodic_task(task: PeriodicTaskDTO):
    task_model = None
    if task.name == "metrics":
        task_model = MetricsTaksDTO
    elif task.name == "s3_backup":
        task_model = S3Backup
    task_model(**task.dict())
