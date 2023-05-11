"""Event handler for clients of the server."""
import argparse
import logging
import math
import wave

from TTS.api import TTS
from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.event import Event
from wyoming.info import Describe, Info
from wyoming.server import AsyncEventHandler
from wyoming.tts import Synthesize

_LOGGER = logging.getLogger(__name__)

class PiperEventHandler(AsyncEventHandler):
    def __init__(
        self,
        wyoming_info: Info,
        cli_args: argparse.Namespace,
        tts: TTS,
        *args,
    ) -> None:
        super().__init__(*args)
        self.cli_args = cli_args
        self.wyoming_info_event = wyoming_info.event()
        self.tts = tts

    async def handle_event(self, event: Event) -> bool:
        if Describe.is_type(event.type):
            await self.write_event(self.wyoming_info_event)
            _LOGGER.debug("Sent info")
            return True

        if not Synthesize.is_type(event.type):
            _LOGGER.warning("Unexpected event: %s", event)
            return True
        synthesize = Synthesize.from_event(event)
        raw_text = synthesize.text
        text = raw_text.strip()

        output_path = "/tmp/output.wav"
        _LOGGER.debug(event)
        tts_args = dict()
        if (self.tts.is_multi_lingual):
            tts_args["language"] = self.cli_args.language

        if (self.tts.is_multi_speaker):
            tts_args["speaker"] = self.cli_args.speaker
        self.tts.tts_to_file(text, **tts_args, file_path=output_path)
        wav_file: wave.Wave_read = wave.open(output_path, "rb")
        with wav_file:
            rate = wav_file.getframerate()
            width = wav_file.getsampwidth()
            channels = wav_file.getnchannels()

            await self.write_event(
                AudioStart(
                    rate=rate,
                    width=width,
                    channels=channels,
                ).event(),
            )

            # Audio
            audio_bytes = wav_file.readframes(wav_file.getnframes())
            bytes_per_sample = width * channels
            bytes_per_chunk = bytes_per_sample * self.cli_args.samples_per_chunk
            num_chunks = int(math.ceil(len(audio_bytes) / bytes_per_chunk))

            # Split into chunks
            for i in range(num_chunks):
                offset = i * bytes_per_chunk
                chunk = audio_bytes[offset : offset + bytes_per_chunk]
                await self.write_event(
                    AudioChunk(
                        audio=chunk,
                        rate=rate,
                        width=width,
                        channels=channels,
                    ).event(),
                )

        await self.write_event(AudioStop().event())
        _LOGGER.debug("Completed request")


        return True