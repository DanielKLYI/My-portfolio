from .parse import ParseStage
from .detect_chapters import DetectChaptersStage
from .split_chapters import SplitChaptersStage
from .extract_entities import ExtractEntitiesStage
from .generate_embeddings import GenerateEmbeddingsStage

STAGES = [
    ParseStage(),
    DetectChaptersStage(),
    SplitChaptersStage(),
    ExtractEntitiesStage(),
    GenerateEmbeddingsStage(),
]
