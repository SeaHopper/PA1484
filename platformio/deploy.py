"""PlatformIO packaging and deployment for the T4-S3 MicroPython template."""

Import("env")

import shutil
import os
import stat
import subprocess
import sys
from pathlib import Path


ROOT = Path(env.subst("$PROJECT_DIR"))
sys.path.insert(0, str(ROOT / "platformio"))
from firmware_layout import find_vfs_partition


PROJECT_SOURCE = ROOT / "project"
SUPPORT = ROOT / "support"
BUILD = ROOT / "device-build"
VFS_ROOT = BUILD / "vfs-root"
VFS_IMAGE = BUILD / "t4s3-vfs.img"
VFS_DEPLOY_IMAGE = BUILD / "t4s3-vfs-deploy.img"
VFS_DEPLOY_SIZE = 0x20000
FIRMWARE = ROOT / "firmware" / "t4s3-lvgl-micropython.bin"

PIO_PACKAGES = Path(env.subst("$PROJECT_PACKAGES_DIR"))
ESPTOOL = PIO_PACKAGES / "tool-esptoolpy" / "esptool.py"
# mkfatfs ships as a native executable per host platform; only Windows uses .exe.
MKFATFS = PIO_PACKAGES / "tool-mkfatfs" / (
    "mkfatfs.exe" if sys.platform == "win32" else "mkfatfs")

SUPPORT_FILES = [
    (SUPPORT / "boot.py", "boot.py"),
    (SUPPORT / "debug_log.py", "debug_log.py"),
    (SUPPORT / "board_lvgl.py", "board_lvgl.py"),
    (SUPPORT / "drivers" / "rm690b0" / "rm690b0.py", "t4s3_rm690b0.py"),
    (SUPPORT / "drivers" / "rm690b0" / "_rm690b0_init.py", "_rm690b0_init.py"),
]

PROJECT_EXCLUDES = {
    "pio_upload_stub.c",
    "secrets_example.py",
    "__pycache__",
    ".DS_Store",
    "Thumbs.db",
    "Desktop.ini",
}


def remove_readonly(function, path, _error_info):
    """Allow generated OneDrive files/directories to be replaced on Windows."""
    os.chmod(path, stat.S_IWRITE)
    function(path)


def require(path, description):
    if not path.exists():
        raise RuntimeError("Missing %s: %s" % (description, path))


def copy_project_tree():
    """Copy student files recursively while preserving their relative paths."""
    require(PROJECT_SOURCE / "main.py", "project/main.py")
    for source_path in PROJECT_SOURCE.rglob("*"):
        relative = source_path.relative_to(PROJECT_SOURCE)
        if (any(part in PROJECT_EXCLUDES for part in relative.parts) or
                source_path.suffix in (".pyc", ".pyo")):
            continue
        destination = VFS_ROOT / relative
        if source_path.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, destination)


def build_app_fs(source=None, target=None, env=None):
    require(MKFATFS, "PlatformIO mkfatfs tool")
    require(FIRMWARE, "course MicroPython firmware")
    _offset, vfs_size = find_vfs_partition(FIRMWARE)
    BUILD.mkdir(parents=True, exist_ok=True)
    if VFS_ROOT.exists():
        shutil.rmtree(VFS_ROOT, onerror=remove_readonly)
    VFS_ROOT.mkdir(parents=True, exist_ok=True)

    copy_project_tree()
    for source_path, device_name in SUPPORT_FILES:
        require(source_path, "project file")
        shutil.copy2(source_path, VFS_ROOT / device_name)

    if not (VFS_ROOT / "secrets.py").exists():
        secrets = PROJECT_SOURCE / "secrets_example.py"
        print("Using placeholder Wi-Fi credentials from secrets_example.py")
        require(secrets, "Wi-Fi credentials example file")
        shutil.copy2(secrets, VFS_ROOT / "secrets.py")

    if VFS_IMAGE.exists():
        VFS_IMAGE.unlink()
    subprocess.run(
        [str(MKFATFS), "-c", str(VFS_ROOT), "-t", "fatfs",
         "-s", str(vfs_size), str(VFS_IMAGE)],
        check=True,
    )
    with VFS_IMAGE.open("rb") as source_stream, \
            VFS_DEPLOY_IMAGE.open("wb") as target_stream:
        target_stream.write(source_stream.read(VFS_DEPLOY_SIZE))
    print("Python application packaged: %s" % VFS_DEPLOY_IMAGE)


def run_esptool(images):
    require(ESPTOOL, "PlatformIO esptool")
    for _offset, image in images:
        require(image, "flash image")
    env.AutodetectUploadPort()
    port = env.subst("$UPLOAD_PORT")
    command = [
        sys.executable, str(ESPTOOL),
        "--chip", "esp32s3",
        "--port", port,
        "--baud", env.subst("$UPLOAD_SPEED"),
        "--before", "usb_reset",
        "--after", "hard_reset",
        "write_flash",
        "--flash_mode", "keep",
        "--flash_size", "keep",
    ]
    for offset, image in images:
        command.extend([offset, str(image)])
    subprocess.run(command, check=True)


def flash_micropython(source=None, target=None, env=None):
    run_esptool([("0x0", FIRMWARE)])


def flash_app(source=None, target=None, env=None):
    build_app_fs()
    vfs_offset, _vfs_size = find_vfs_partition(FIRMWARE)
    run_esptool([(hex(vfs_offset), VFS_DEPLOY_IMAGE)])


def deploy_all(source=None, target=None, env=None):
    build_app_fs()
    vfs_offset, _vfs_size = find_vfs_partition(FIRMWARE)
    run_esptool([
        ("0x0", FIRMWARE),
        (hex(vfs_offset), VFS_DEPLOY_IMAGE),
    ])


# The ordinary PlatformIO Upload button provisions both a new and used board.
env.Replace(UPLOADCMD=deploy_all)

env.AddCustomTarget(
    "build_app_fs", None, build_app_fs,
    title="Build Python application",
    description="Package project/main.py without flashing",
    always_build=True,
)
env.AddCustomTarget(
    "flash_micropython", None, flash_micropython,
    title="Flash MicroPython firmware",
    description="Flash only the supplied LVGL MicroPython firmware",
    always_build=True,
)
env.AddCustomTarget(
    "flash_app", None, flash_app,
    title="Flash Python application",
    description="Flash only project/main.py and board support",
    always_build=True,
)
env.AddCustomTarget(
    "deploy", None, deploy_all,
    title="Deploy complete project",
    description="Flash firmware and Python application",
    always_build=True,
)
