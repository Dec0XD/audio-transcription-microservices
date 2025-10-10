"""Simple utility to convert a video/audio file to WAV using ffmpeg.

Usage:
	python main.py input_video.mp4 -o output.wav --sr 16000 --channels 1

Requirements:
	- ffmpeg must be installed and available on PATH.

The script calls ffmpeg directly (no heavy Python audio libs) which is robust for large files.
"""

from __future__ import annotations

import argparse
import subprocess
import os
import sys


def convert_to_wav(input_path: str, output_path: str | None = None, sample_rate: int = 16000, channels: int = 1, overwrite: bool = True) -> str:
	"""Converts any audio/video file to a WAV file using ffmpeg.

	Returns the path to the created WAV file.
	Raises RuntimeError on failure.
	"""
	if not os.path.exists(input_path):
		raise FileNotFoundError(f"Input file not found: {input_path}")

	if output_path is None:
		base, _ = os.path.splitext(input_path)
		output_path = f"{base}.wav"

	if os.path.exists(output_path):
		if overwrite:
			try:
				os.remove(output_path)
			except OSError:
				raise RuntimeError(f"Cannot remove existing output file: {output_path}")
		else:
			raise RuntimeError(f"Output file already exists: {output_path}")

	cmd = [
		"ffmpeg",
		"-y" if overwrite else "-n",
		"-i",
		input_path,
		"-vn",  # no video
		"-ar",
		str(sample_rate),
		"-ac",
		str(channels),
		"-acodec",
		"pcm_s16le",
		output_path,
	]

	try:
		# Run ffmpeg and capture output for better error messages
		res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
	except subprocess.CalledProcessError as e:
		stderr = e.stderr.decode(errors="ignore") if e.stderr else ""
		raise RuntimeError(f"ffmpeg failed: {stderr}")

	if not os.path.exists(output_path):
		raise RuntimeError("ffmpeg did not produce the expected output file")

	return output_path


def parse_args(argv=None):
	p = argparse.ArgumentParser(description="Convert video/audio file to WAV using ffmpeg")
	p.add_argument("input", help="Path to input video/audio file")
	p.add_argument("-o", "--output", help="Path for output WAV file (optional)")
	p.add_argument("--sr", "--sample-rate", type=int, default=16000, help="Output sample rate (default: 16000)")
	p.add_argument("--channels", type=int, default=1, choices=[1, 2], help="Number of audio channels (1 or 2)")
	p.add_argument("--no-overwrite", dest="overwrite", action="store_false", help="Do not overwrite existing output file")
	p.add_argument("--quiet", dest="quiet", action="store_true", help="Suppress ffmpeg stdout/stderr on success")
	return p.parse_args(argv)


def main(argv=None):
	args = parse_args(argv)

	try:
		out = convert_to_wav(args.input, args.output, sample_rate=args.sr, channels=args.channels, overwrite=args.overwrite)
		if not args.quiet:
			print(f"Converted to WAV: {out}")
		return 0
	except Exception as exc:
		print(f"Error: {exc}", file=sys.stderr)
		return 2


if __name__ == "__main__":
	raise SystemExit(main())
