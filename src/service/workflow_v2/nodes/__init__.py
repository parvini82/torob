"""
Workflow nodes for the v2 system.

This package contains all individual node implementations that can be
composed together to create workflow scenarios.
"""

from .caption_generator import CaptionGeneratorNode
from .tag_extractor import TagExtractorNode
from .image_tag_extractor import ImageTagExtractorNode
from .translator import TranslatorNode
from .merger import MergerNode
from .refiner import RefinerNode
from .conversation_refiner import ConversationRefinerNode

__all__ = [
    "CaptionGeneratorNode",
    "TagExtractorNode",
    "ImageTagExtractorNode",
    "TranslatorNode",
    "MergerNode",
    "RefinerNode",
    "ConversationRefinerNode"
]
