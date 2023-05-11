#!/usr/bin/env python3
import argparse
import asyncio
import logging
from functools import partial

from TTS.api import TTS
from wyoming.info import Attribution, Info, TtsProgram, TtsVoice
from wyoming.server import AsyncServer

from handler import PiperEventHandler

_LOGGER = logging.getLogger(__name__)

async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--voice",
        default=None,
        help="The Voice to use for TTS",
    )
    parser.add_argument(
        "--speaker",
        help="Set the target speaker",
    )
    parser.add_argument(
        "--language",
        help="Set the target language",
    )
    parser.add_argument("--samples-per-chunk", type=int, default=1024)
    parser.add_argument("--uri", required=True, help="unix:// or tcp://")
    parser.add_argument("--debug", action="store_true", help="Log DEBUG messages")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    if (args.voice == None): 
        _LOGGER.info("The following voices are available (specify with --voice [model_name]): ")
        _LOGGER.info("\n".join(TTS.list_models()))
        exit()

    tts = TTS(args.voice)

    if (tts.is_multi_lingual and args.language is None): 
        _LOGGER.error("The following languages are available (specify with --language [lang]): ")
        _LOGGER.info("\n".join(tts.languages))
        exit()
    if (tts.is_multi_speaker and args.speaker is None):
        _LOGGER.error("The following speakers are available (specify with --speakers [speaker]): ")
        _LOGGER.info("\n".join(tts.speakers))
        exit()

    language = None
    if (tts.is_multi_lingual is False):
        language = args.voice.split("/")[1]
        _LOGGER.info("Using language: %s", language)

    _LOGGER.info("TTS ready")

    wyoming_info = Info(
        tts=[
            TtsProgram(
                name="coqui-ai TTS",
                attribution=Attribution(
                    name="coqui-ai", url="https://github.com/coqui-ai/TTS"
                ),
                installed=True,
                voices=[
                    TtsVoice(
                        name=speaker,
                        attribution=Attribution(
                            name="coqui-ai", url="https://github.com/coqui-ai/TTS"
                        ),
                        installed=True,
                        languages=tts.languages if tts.is_multi_lingual else [language],
                    ) for speaker in ([args.speaker] if tts.is_multi_speaker else ["Default"]) # Preparation for multi speaker support in wyoming event
                ],
            )
        ],
    )
    
    server = AsyncServer.from_uri(args.uri)
    _LOGGER.info("Ready")
    await server.run(
        partial(
                PiperEventHandler,
                wyoming_info,
                args,
                tts
            )
    )



# -----------------------------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(main())
