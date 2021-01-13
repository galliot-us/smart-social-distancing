class SourcePostProcessor:

    def __init__(self, config, source: str, post_processor: str):
        self.post_processor_name = config.get_section_dict(post_processor)["Name"]
        self.post_processor = None
        if self.post_processor_name == "objects_filtering":
            from .objects_filtering import ObjectsFilteringPostProcessor
            self.post_processor = ObjectsFilteringPostProcessor(config, source, post_processor)
        elif self.post_processor_name == "social_distance":
            from .social_distance import SocialDistancePostProcessor
            self.post_processor = SocialDistancePostProcessor(config, source, post_processor)
        elif self.post_processor_name == "anonymizer":
            from .anonymizer import AnonymizerPostProcesor
            self.post_processor = AnonymizerPostProcesor(config, source, post_processor)
        else:
            raise ValueError(f"Not supported post processor named: {self.post_processor_name}")

    def process(self, cv_image, objects_list, post_processing_data):
        return self.post_processor.process(cv_image, objects_list, post_processing_data)
