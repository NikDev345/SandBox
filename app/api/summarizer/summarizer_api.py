from SandBox.app.api.summarizer.ai_api import AIAPI


class SummarizerAPI:

    @staticmethod
    def summarize(
        text: str,
        length: str,
        token: str,
    ):

        return AIAPI.post(
            endpoint="/summarizer/generate",
            data={
                "text": text,
                "length": length,
            },
            token=token,
        )