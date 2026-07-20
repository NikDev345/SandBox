"""
Paddle Table Client

Singleton wrapper around PaddleOCR Table Structure Recognition.
"""

from __future__ import annotations

from paddleocr import TableStructureRecognition


class PaddleTableClient:
    """
    Singleton Table Recognition model.
    """

    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    @property
    def model(self):
        """
        Lazily initialize the model.
        """

        if self._model is None:

            self._model = TableStructureRecognition(
                model_name="SLANet"
            )

        return self._model