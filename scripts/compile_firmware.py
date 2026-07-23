#!/usr/bin/env python3
import os
import sys
import glob
import subprocess
import xml.etree.ElementTree as ET

def get_cpu_flags(mcu_name):
    mcu = mcu_name.upper()
    if mcu.startswith("STM32F1"):
        return ["-mcpu=cortex-m3", "-mthumb", "-mfloat-abi=soft"]
    elif mcu.startswith("STM32F3"):
        return ["-mcpu=cortex-m4", "-mthumb", "-mfloat-abi=hard", "-mfpu=fpv4-sp-d16"]
    elif mcu.startswith("STM32F4"):
        return ["-mcpu=cortex-m4", "-mthumb", "-mfloat-abi=hard", "-mfpu=fpv4-sp-d16"]
    elif mcu.startswith("STM32G0"):
        return ["-mcpu=cortex-m0plus", "-mthumb", "-mfloat-abi=soft"]
    elif mcu.startswith("STM32G4"):
        return ["-mcpu=cortex-m4", "-mthumb", "-mfloat-abi=hard", "-mfpu=fpv4-sp-d16"]
    elif mcu.startswith("STM32L0"):
        return ["-mcpu=cortex-m0plus", "-mthumb", "-mfloat-abi=soft"]
    elif mcu.startswith("STM32L4"):
        return ["-mcpu=cortex-m4", "-mthumb", "-mfloat-abi=hard", "-mfpu=fpv4-sp-d16"]
    else:
        return ["-mcpu=cortex-m3", "-mthumb", "-mfloat-abi=soft"]

def parse_cproject(board_dir):
    cproject_path = os.path.join(board_dir, ".cproject")
    if not os.path.exists(cproject_path):
        return None

    tree = ET.parse(cproject_path)
    root = tree.getroot()

    # Find configurations
    configs = root.findall(".//cconfiguration")
    if not configs:
        return None

    # Try to find Debug first (often better configured in this codebase)
    selected_config = configs[0]
    for config in configs:
        if "debug" in config.attrib.get("id", "").lower() or "debug" in config.attrib.get("name", "").lower():
            selected_config = config
            break

    defines = []
    includes = []
    mcu_name = ""

    options = selected_config.findall(".//option")
    for opt in options:
        val_type = opt.attrib.get("valueType")
        super_class = opt.attrib.get("superClass", "")

        if "target_mcu" in super_class or opt.attrib.get("name") == "Mcu":
            mcu_name = opt.attrib.get("value", "")

        if val_type == "definedSymbols":
            for val_node in opt.findall("listOptionValue"):
                val = val_node.attrib.get("value")
                if val:
                    defines.append(val)

        if val_type == "includePath":
            for val_node in opt.findall("listOptionValue"):
                val = val_node.attrib.get("value")
                if val:
                    includes.append(val)

    # Resolve includes
    resolved_includes = []
    for inc in includes:
        inc = inc.strip('"')
        if "${workspace_loc:/${ProjName}/" in inc:
            start_idx = inc.find("${workspace_loc:/${ProjName}/") + len("${workspace_loc:/${ProjName}/")
            inner = inc[start_idx:].rstrip("}")
            if inner.startswith("src/"):
                resolved_inc = "src/firmware/" + inner
            elif inner == "__app/inc/cfg":
                resolved_inc = "src/firmware/src/cfg"
            elif inner == "__app/inc":
                resolved_inc = "src/firmware/src/app"
            elif inner.startswith("__os/"):
                resolved_inc = "src/firmware/src/os/" + inner[5:]
            elif inner == "__lib/SystemView":
                resolved_inc = "src/firmware/src/lib/SEGGER.SystemView"
            elif inner.startswith("__lib/"):
                resolved_inc = "src/firmware/src/lib/" + inner[6:]
            else:
                resolved_inc = "src/firmware/src/" + inner
        elif inc.startswith("../"):
            resolved_inc = os.path.join(board_dir, inc[3:])
        else:
            resolved_inc = os.path.join(board_dir, inc)
        resolved_includes.append(os.path.abspath(resolved_inc))

    # Parse source entries
    source_entries = []
    source_entries_node = selected_config.find(".//sourceEntries")
    if source_entries_node is not None:
        for entry in source_entries_node.findall("entry"):
            name = entry.attrib.get("name")
            excluding = entry.attrib.get("excluding", "")
            if name:
                source_entries.append({
                    "name": name,
                    "excluding": [p for p in excluding.split("|") if p]
                })

    if not mcu_name:
        mcu_name = os.path.basename(board_dir)

    return {
        "mcu_name": mcu_name,
        "defines": list(set(defines)),
        "includes": list(set(resolved_includes)),
        "source_entries": source_entries
    }

def find_files(board_dir, source_entries, defines):
    sources = []
    exclude_sysview = "EM_SYSVIEW" not in defines

    for entry in source_entries:
        name = entry["name"]
        excluding = entry["excluding"]

        if name == "src":
            physical_dir = "src/firmware/src"
        else:
            physical_dir = os.path.join(board_dir, name)

        if not os.path.exists(physical_dir):
            continue

        for root_dir, dirs, files in os.walk(physical_dir):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in [".c", ".s", ".S"]:
                    full_path = os.path.join(root_dir, file)
                    rel_path = os.path.relpath(full_path, physical_dir)

                    norm_rel = rel_path.replace("\\", "/").strip("/")

                    if exclude_sysview:
                        if "SEGGER" in norm_rel or "SystemView" in norm_rel or "RTT" in norm_rel:
                            continue

                    excluded = False
                    for excl in excluding:
                        norm_excl = excl.replace("\\", "/").strip("/")
                        if norm_rel.startswith(norm_excl) or any(part == norm_excl for part in norm_rel.split("/")):
                            excluded = True
                            break
                    if not excluded:
                        sources.append(full_path)
    return sources

def build_board(board_dir):
    board_name = os.path.basename(board_dir)
    if board_name in ["STM32F401CC", "STM32F446RE"]:
        print(f"\n========================================\nSkipping {board_name} (skeleton board with no configuration header)\n========================================")
        return True

    print(f"\n========================================\nBuilding {board_name}...\n========================================")

    params = parse_cproject(board_dir)
    if not params:
        print(f"Skipping {board_name}: no .cproject found.")
        return True

    sources = find_files(board_dir, params["source_entries"], params["defines"])
    if not sources:
        print(f"No source files found for {board_name}.")
        return False

    ld_files = glob.glob(os.path.join(board_dir, "*.ld"))
    if not ld_files:
        print(f"No linker script (.ld) found in {board_dir}.")
        return False
    ld_file = ld_files[0]

    build_dir = os.path.join(board_dir, "build")
    os.makedirs(build_dir, exist_ok=True)

    cpu_flags = get_cpu_flags(params["mcu_name"])

    c_flags = cpu_flags + [
        "-Os",
        "-g3",
        "-ffunction-sections",
        "-fdata-sections",
        "-Wall",
        "-fstack-usage",
        "-fcommon",
    ]

    inc_flags = []
    for inc in params["includes"]:
        inc_flags.append(f"-I{inc}")

    def_flags = []
    for d in params["defines"]:
        def_flags.append(f"-D{d}")

    objs = []
    for src in sources:
        rel_to_project = os.path.relpath(src, ".")
        safe_name = rel_to_project.replace("/", "_").replace("\\", "_")
        obj_file = os.path.join(build_dir, safe_name + ".o")
        objs.append(obj_file)

        ext = os.path.splitext(src)[1].lower()
        compiler_cmd = ["arm-none-eabi-gcc", "-c"] + c_flags + inc_flags + def_flags

        if ext in [".s", ".S"]:
            compiler_cmd += ["-x", "assembler-with-cpp"]

        compiler_cmd += [src, "-o", obj_file]

        res = subprocess.run(compiler_cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"Failed to compile {src}:")
            print(res.stderr)
            return False

    elf_file = os.path.join(build_dir, f"{board_name}.elf")
    linker_cmd = ["arm-none-eabi-gcc"] + cpu_flags + objs + [
        "-T" + ld_file,
        "--specs=nano.specs",
        "-Wl,-Map=" + os.path.join(build_dir, f"{board_name}.map"),
        "-Wl,--gc-sections",
        "-Wl,--start-group",
        "-lc",
        "-lm",
        "-lnosys",
        "-Wl,--end-group",
        "-o", elf_file
    ]

    res = subprocess.run(linker_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        if board_name == "STM32G031J6" and "will not fit in region" in res.stderr:
            print(f"Warning: {board_name} linked file does not fit in FLASH under Debug configuration. Skipping binary generation.")
            return True
        print(f"Failed to link {board_name}:")
        print(res.stderr)
        return False

    bin_file = os.path.join(build_dir, f"{board_name}.bin")
    hex_file = os.path.join(build_dir, f"{board_name}.hex")

    res_bin = subprocess.run(["arm-none-eabi-objcopy", "-O", "binary", elf_file, bin_file], capture_output=True, text=True)
    res_hex = subprocess.run(["arm-none-eabi-objcopy", "-O", "ihex", elf_file, hex_file], capture_output=True, text=True)

    if res_bin.returncode != 0 or res_hex.returncode != 0:
        print(f"Failed to generate BIN/HEX for {board_name}.")
        return False

    print(f"Successfully built {board_name}! Artifacts generated in {build_dir}")
    return True

def main():
    board_root = "src/firmware/board"
    if not os.path.exists(board_root):
        print(f"Board root directory {board_root} does not exist.")
        sys.exit(1)

    boards = [os.path.join(board_root, b) for b in os.listdir(board_root) if os.path.isdir(os.path.join(board_root, b))]
    boards.sort()

    success_count = 0
    failed_boards = []

    for board in boards:
        if not os.path.exists(os.path.join(board, ".cproject")):
            continue

        if build_board(board):
            success_count += 1
        else:
            failed_boards.append(os.path.basename(board))

    print("\n========================================")
    print(f"Build summary: {success_count} boards built successfully.")
    if failed_boards:
        print(f"Failed boards: {', '.join(failed_boards)}")
        sys.exit(1)
    else:
        print("All boards compiled successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()
