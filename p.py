from youtube_transcript_api import YouTubeTranscriptApi

client = YouTubeTranscriptApi()

transcript = client.fetch("jNQXAC9IVRw")

print(type(transcript))

print(type(transcript[0]))

print(transcript[0])

print(dir(transcript[0]))