#!/usr/bin/env python3
"""Read-only local inventory of an Apple .app, .xcarchive or .ipa; no execution."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import plistlib
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from xml.parsers.expat import ExpatError

MAX_PLIST = 8 * 1024 * 1024
MAX_BINARY = 512 * 1024 * 1024
KEYS = {"CFBundleIdentifier", "CFBundleDisplayName", "CFBundleName", "CFBundleExecutable",
        "CFBundleShortVersionString", "CFBundleVersion", "CFBundleSupportedPlatforms",
        "MinimumOSVersion", "LSMinimumSystemVersion", "UIDeviceFamily", "UIRequiredDeviceCapabilities",
        "DTPlatformName", "DTSDKName", "UIBackgroundModes", "NSAppTransportSecurity", "CFBundleURLTypes",
        "LSApplicationQueriesSchemes", "ITSAppUsesNonExemptEncryption", "CFBundleIcons", "CFBundleIcons~ipad",
        "CFBundleIconName", "UISupportedInterfaceOrientations", "UISupportedInterfaceOrientations~ipad",
        "NSExtension", "LSRequiresIPhoneOS"}


def selected_metadata(info):
    if not isinstance(info, dict):
        raise ValueError("Expected a plist dictionary")
    return {k: v for k, v in info.items() if k in KEYS or "UsageDescription" in k}


def run(argv):
    try:
        p = subprocess.run(argv, capture_output=True, text=True, errors="replace", timeout=30)
        return dict(command=argv, returncode=p.returncode, stdout=p.stdout[:100000], stderr=p.stderr[:10000])
    except (OSError, subprocess.TimeoutExpired) as exc:
        return dict(command=argv, error=str(exc))


def digest(stream):
    h = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        h.update(chunk)
    return h.hexdigest()


class Bundle:
    def __init__(self, path):
        self.path, self.archive, self.warnings = path, None, []
        if path.suffix.lower() == ".ipa":
            self.archive = zipfile.ZipFile(path)
            entries = self.archive.infolist()
            if len(entries) > 100000:
                raise ValueError("Archive has too many entries for this inspector")
            names = [x.filename for x in entries]
            if len(names) != len(set(names)):
                raise ValueError("Archive has duplicate member names")
            if any(PurePosixPath(n).is_absolute() or ".." in PurePosixPath(n).parts or "\\" in n for n in names):
                raise ValueError("Unsafe archive member path")
            mains = [n for n in names if re.fullmatch(r"Payload/[^/]+\.app/Info\.plist", n)]
            if len(mains) != 1:
                raise ValueError("Expected exactly one Payload/*.app/Info.plist")
            self.prefix = mains[0][:-len("Info.plist")]
            self.names = sorted(n[len(self.prefix):] for n in names if n.startswith(self.prefix) and not n.endswith("/"))
            self.root = None
        else:
            if path.suffix.lower() == ".xcarchive":
                apps = sorted((path / "Products/Applications").glob("*.app"))
                if len(apps) != 1:
                    raise ValueError("Archive must contain one app; otherwise supply a specific .app path")
                path = apps[0].resolve()
            if path.suffix.lower() != ".app" or not path.is_dir():
                raise ValueError("Input must be an existing .app directory, .xcarchive, or .ipa")
            self.root = path
            self.names = []
            for directory, dirs, files in os.walk(path, followlinks=False):
                dirs[:] = [d for d in dirs if not (Path(directory) / d).is_symlink()]
                for name in files:
                    p = Path(directory) / name
                    if not p.resolve().is_relative_to(path):
                        self.warnings.append("Skipped external symlink: " + str(p.relative_to(path)))
                    else:
                        self.names.append(p.relative_to(path).as_posix())
            self.names.sort()

    def close(self):
        if self.archive:
            self.archive.close()

    @contextmanager
    def open(self, name, limit):
        if name not in self.names:
            raise ValueError("Bundle member missing: " + name)
        if self.archive:
            entry = self.archive.getinfo(self.prefix + name)
            if stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError("Archive symlink not read: " + name)
            if entry.file_size > limit:
                raise ValueError("Member exceeds inspection limit: " + name)
            with self.archive.open(entry) as f:
                yield f
        else:
            p = self.root / name
            if not p.resolve().is_relative_to(self.root) or p.stat().st_size > limit:
                raise ValueError("Member outside bundle or exceeds inspection limit: " + name)
            with p.open("rb") as f:
                yield f

    def read(self, name):
        with self.open(name, MAX_PLIST) as f:
            raw = f.read(MAX_PLIST + 1)
        if len(raw) > MAX_PLIST:
            raise ValueError("Oversized plist: " + name)
        return raw


def decode_plist(raw, allow_openstep=False):
    try:
        return plistlib.loads(raw)
    except (plistlib.InvalidFileException, ExpatError) as exc:
        if not allow_openstep:
            raise ValueError("Unreadable or malformed plist: " + str(exc)) from exc
        # InfoPlist.strings may use OpenStep syntax. plutil reads stdin, never changes the input.
        p = subprocess.run(["plutil", "-convert", "xml1", "-o", "-", "-"], input=raw,
                           capture_output=True, timeout=15)
        if p.returncode:
            raise ValueError("Could not parse localized plist strings")
        return plistlib.loads(p.stdout)


def inspect(path):
    bundle = Bundle(path)
    result = dict(input_path=str(path), inspected_at_utc=datetime.now(timezone.utc).isoformat(),
                  inspection="Static inventory only; no app code executed", errors=[], notes=bundle.warnings)
    try:
        if bundle.archive:
            with path.open("rb") as f:
                result["ipa_sha256"] = digest(f)
            result["notes"].append("IPA signature not verified; only selected members read")
        else:
            result["app_path"] = str(bundle.root)
        info_name = "Info.plist" if "Info.plist" in bundle.names else "Contents/Info.plist"
        raw = bundle.read(info_name)
        info = decode_plist(raw)
        result["info"] = selected_metadata(info)
        result["info_plist_sha256"] = hashlib.sha256(raw).hexdigest()
        result["privacy_manifests"], result["nested_bundles"], result["localized_permissions"] = [], [], []
        relevant = [n for n in bundle.names if n.endswith(("PrivacyInfo.xcprivacy", "Info.plist", "InfoPlist.strings")) and n != info_name]
        if len(relevant) > 2000:
            result["errors"].append("Metadata inventory truncated at 2000 files; remaining files not inspected")
        for name in relevant[:2000]:
            try:
                raw = bundle.read(name)
                data = decode_plist(raw, allow_openstep=name.endswith(".strings"))
                if not isinstance(data, dict):
                    raise ValueError("Expected dictionary")
                if name.endswith("PrivacyInfo.xcprivacy"):
                    result["privacy_manifests"].append(dict(path=name, sha256=hashlib.sha256(raw).hexdigest(), values=data))
                elif name.endswith("InfoPlist.strings"):
                    result["localized_permissions"].append(dict(path=name, values=selected_metadata(data)))
                else:
                    result["nested_bundles"].append(dict(path=name, values=selected_metadata(data)))
            except (OSError, ValueError, plistlib.InvalidFileException, subprocess.TimeoutExpired) as exc:
                result["errors"].append(name + ": " + str(exc))
        executable = info.get("CFBundleExecutable", "")
        if not isinstance(executable, str) or not executable or "/" in executable or "\\" in executable or executable in {".", ".."}:
            raise ValueError("Missing or unsafe CFBundleExecutable")
        executable_name = ("Contents/MacOS/" if info_name.startswith("Contents/") else "") + executable
        with tempfile.TemporaryDirectory(prefix="app-store-inspect-") as tmp:
            if bundle.archive:
                binary = Path(tmp) / "executable"
                with bundle.open(executable_name, MAX_BINARY) as src, binary.open("wb") as dest:
                    shutil.copyfileobj(src, dest)
            else:
                binary = bundle.root / executable_name
            with bundle.open(executable_name, MAX_BINARY) as f:
                result["executable_sha256"] = digest(f)
            result["binary_tools"] = {
                "file": run(["file", str(binary)]),
                "architectures": run(["xcrun", "lipo", "-archs", str(binary)]),
                "build_platform": run(["xcrun", "vtool", "-show-build", str(binary)]),
            }
            vtool = result["binary_tools"]["build_platform"].get("stdout", "")
            result["macho_platforms"] = sorted(set(re.findall(r"\bplatform\s+([A-Za-z0-9_]+)", vtool)))
            if not result["macho_platforms"]:
                result["notes"].append("No Mach-O platform extracted; examine legacy load commands and metadata manually")
            if not bundle.archive:
                result["entitlements_tool"] = run(["codesign", "-d", "--entitlements", ":-", str(bundle.root)])
        for name, tool in result.get("binary_tools", {}).items():
            if tool.get("returncode") != 0:
                result["errors"].append("Binary tool unavailable/failed: " + name)
        result["notes"].append("Hashes identify the IPA or selected files, not a complete directory digest. No runtime compliance conclusion is implied.")
    except (OSError, ValueError, plistlib.InvalidFileException, zipfile.BadZipFile) as exc:
        result["errors"].append(str(exc))
    finally:
        bundle.close()
    result["complete_static_inventory"] = not result["errors"]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    path, out = args.app.expanduser().resolve(), args.out.expanduser().resolve()
    if not path.exists():
        parser.error("Input does not exist")
    if out == path or (path.is_dir() and out.is_relative_to(path)):
        parser.error("Output must be outside the input artifact")
    if out.exists():
        parser.error("Output already exists; choose a new evidence file")
    try:
        result = inspect(path)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        result = dict(input_path=str(path), complete_static_inventory=False, errors=[str(exc)])
    out.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with out.open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        f.write("\n")
    print(json.dumps(dict(output=str(out), complete_static_inventory=result["complete_static_inventory"],
                          platforms=result.get("macho_platforms", []), errors=result["errors"]), indent=2))
    return 0 if result["complete_static_inventory"] else 1


if __name__ == "__main__":
    sys.exit(main())
