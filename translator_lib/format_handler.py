#!/usr/bin/env python3
"""
Format Handler Base Classes

Defines the interface for translation file format handlers.
Each format (PO, JSON, etc.) implements this interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple

from deep_translator import GoogleTranslator


class FormatHandler(ABC):
    """
    Abstract base class for translation file format handlers.
    
    Each format handler knows how to:
    - Load a file in its format
    - Translate the content
    - Save the translated content
    """
    
    def __init__(
        self,
        source_lang: str = "en",
        target_lang: str = "fr",
        skip_translated: bool = True,
        verbose: bool = False,
        checkpoint_every: int = 50,
        cache: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the format handler.
        
        Args:
            source_lang: Source language code (default: "en")
            target_lang: Target language code (default: "fr")
            skip_translated: Whether to skip already translated entries
            verbose: Whether to print verbose progress information
            checkpoint_every: Save checkpoint every N entries
            cache: Optional translation cache dictionary
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.skip_translated = skip_translated
        self.verbose = verbose
        self.checkpoint_every = checkpoint_every
        self.cache = cache if cache is not None else {}
        self.translator = GoogleTranslator(source=source_lang, target=target_lang)
    
    @abstractmethod
    def load(self, input_path: str) -> None:
        """
        Load the input file.
        
        Args:
            input_path: Path to the input file
        """
        pass
    
    @abstractmethod
    def translate(self) -> Tuple[int, int]:
        """
        Translate the loaded content.
        
        Returns:
            Tuple of (total_entries, translated_entries)
        """
        pass
    
    @abstractmethod
    def save(self, output_path: str, dry_run: bool = False) -> None:
        """
        Save the translated content to a file.
        
        Args:
            output_path: Path to the output file
            dry_run: If True, don't actually write the file
        """
        pass
    
    def process_file(
        self,
        input_path: str,
        output_path: str,
        dry_run: bool = False,
        resume: bool = False
    ) -> Tuple[int, int]:
        """
        Complete workflow: load, translate, and save.
        
        Args:
            input_path: Path to the input file
            output_path: Path to the output file
            dry_run: If True, don't write the output file
            resume: If True, resume from existing output file
            
        Returns:
            Tuple of (total_entries, translated_entries)
        """
        self.load(input_path)
        
        # If resuming, try to load existing output
        if resume:
            self._load_existing_output(output_path)
        
        total, translated = self.translate()
        self.save(output_path, dry_run=dry_run)
        
        return total, translated
    
    def _load_existing_output(self, output_path: str) -> None:
        """
        Load existing output file for resume functionality.
        Subclasses can override this if they support resume.
        
        Args:
            output_path: Path to the existing output file
        """
        pass
