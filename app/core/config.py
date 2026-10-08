"""Core configuration for the PDF extraction microservice."""


class Settings:
    """Application settings loaded from environment/config."""

    def __init__(self) -> None:
        self.project_name = "pdf-extraction-service"
        self.version = "1.0.0"
        self.api_v1_prefix = "/api/v1"
        self.pdf_max_pages = 50
        self.pdf_max_file_size_mb = 50
