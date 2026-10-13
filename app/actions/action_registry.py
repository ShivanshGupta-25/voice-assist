"""Central registry of applications the assistant may launch."""

from types import MappingProxyType


ALLOWED_APPS = MappingProxyType({
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
    "whatsapp": "whatsapp:",
})