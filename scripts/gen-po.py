#!/usr/bin/env python3
"""
Regenerate and validate the LuCI message catalogs for luci-app-airoha-npu.

Source of truth:
  * every _('...') literal in the LuCI view  (with its line number)
  * the menu entry title      (root/usr/share/luci/menu.d/*.json)
  * the ACL description       (root/usr/share/rpcd/acl.d/*.json)

Outputs, all sorted by msgid and all UTF-8 / LF:
  po/templates/luci-app-airoha-npu.pot
  po/es/luci-app-airoha-npu.po
  po/zh_Hans/luci-app-airoha-npu.po

Run with --check to only verify the files on disk (exit code 1 on any problem).
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIEW = ROOT / "htdocs/luci-static/resources/view/airoha_npu/status.js"
MENU = ROOT / "root/usr/share/luci/menu.d/luci-app-airoha-npu.json"
ACL = ROOT / "root/usr/share/rpcd/acl.d/luci-app-airoha-npu.json"
POT = ROOT / "po/templates/luci-app-airoha-npu.pot"
PO_ES = ROOT / "po/es/luci-app-airoha-npu.po"
PO_ZH = ROOT / "po/zh_Hans/luci-app-airoha-npu.po"

PKG = "luci-app-airoha-npu"

# The two strings that do not live in the view.
MENU_TITLE = "SoC Status"
ACL_DESC = "Grant access to Airoha SoC status (NPU + CPU + Overclock)"


# --------------------------------------------------------------------------
# extraction
# --------------------------------------------------------------------------
def view_refs():
    """[(msgid, 'path:line')] in source order, duplicate msgids kept."""
    src = VIEW.read_text(encoding="utf-8")
    rel = VIEW.relative_to(ROOT).as_posix()
    out = []
    for m in re.finditer(r"\b_\(", src):
        i = m.end()
        while i < len(src) and src[i] in " \t\r\n":
            i += 1
        if i >= len(src) or src[i] not in "'\"`":
            continue
        quote = src[i]
        j = i + 1
        buf = []
        while j < len(src):
            ch = src[j]
            if ch == "\\":
                nxt = src[j + 1] if j + 1 < len(src) else ""
                buf.append({"n": "\n", "t": "\t"}.get(nxt, nxt))
                j += 2
                continue
            if ch == quote:
                break
            buf.append(ch)
            j += 1
        line = src.count("\n", 0, i) + 1
        out.append(("".join(buf), f"{PKG}/{rel}:{line}"))
    return out


def json_ref(path, key):
    """Line number of the value of `key` in a small hand-formatted JSON file."""
    rel = path.relative_to(ROOT).as_posix()
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if f'"{key}"' in raw:
            return f"{PKG}/{rel}:{n}"
    raise SystemExit(f"cannot locate {key!r} in {rel}")


def build_corpus():
    """msgid -> list of references, sorted by msgid."""
    refs = {}
    for msgid, ref in view_refs():
        refs.setdefault(msgid, []).append(ref)
    refs.setdefault(MENU_TITLE, []).append(json_ref(MENU, "title"))
    refs.setdefault(ACL_DESC, []).append(json_ref(ACL, "description"))
    return {k: sorted(v) for k, v in sorted(refs.items())}


# --------------------------------------------------------------------------
# po formatting
# --------------------------------------------------------------------------
def quote(text):
    """GNU-style quoted string: one first line plus wrapped continuations."""
    esc = text.replace("\\", "\\\\").replace('"', '\\"').replace("\t", "\\t").replace("\n", "\\n")
    if len(esc) <= 72:
        return f'"{esc}"'
    words = re.findall(r"[^ ]+ |[^ ]+$", esc)
    lines, cur = [], ""
    for w in words:
        if cur and len(cur) + len(w) > 72:
            lines.append(cur)
            cur = ""
        cur += w
    if cur:
        lines.append(cur)
    out = [f'"{lines[0]}"']
    out += [f'"{ln}"' for ln in lines[1:]]
    return "\n".join(out)


def entry(msgid, msgstr, refs):
    block = []
    for r in refs:
        block.append(f"#: {r}")
    body = quote(msgid)
    block.append(f"msgid {body}" if "\n" not in body else f"msgid {body}")
    sbody = quote(msgstr)
    block.append(f"msgstr {sbody}")
    return "\n".join(block) + "\n"


POT_HEADER = 'msgid ""\nmsgstr "Content-Type: text/plain; charset=UTF-8"\n\n'


def po_header(lang, team, plural):
    return (
        f'# {team} translation for {PKG}\n'
        f'# This file is distributed under the same license as the package.\n'
        'msgid ""\n'
        'msgstr ""\n'
        f'"Project-Id-Version: {PKG}\\n"\n'
        '"Report-Msgid-Bugs-To: '
        'https://github.com/rchen14b/luci-app-airoha-npu/issues\\n"\n'
        '"POT-Creation-Date: 2026-11-14 00:47+0800\\n"\n'
        '"PO-Revision-Date: 2026-11-14 00:47+0800\\n"\n'
        '"Last-Translator: Ryan Chen <rchen14b@gmail.com>\\n"\n'
        f'"Language-Team: {team}\\n"\n'
        f'"Language: {lang}\\n"\n'
        '"MIME-Version: 1.0\\n"\n'
        '"Content-Type: text/plain; charset=UTF-8\\n"\n'
        '"Content-Transfer-Encoding: 8bit\\n"\n'
        f'"Plural-Forms: {plural}\\n"\n'
        "\n"
    )


# --------------------------------------------------------------------------
# translations
# --------------------------------------------------------------------------
ES = {
    "%d MHz is above %d MHz, which is as far as this has been tested. The "
    "board may run unstable or stop responding until it is power cycled.":
        "%d MHz supera los %d MHz hasta los que se ha probado este equipo. La "
        "placa puede volverse inestable o dejar de responder hasta que se "
        "reinicie.",
    "%d sta": "%d estaciones",
    "%d used / %d free (%s%%)": "%d en uso / %d libres (%s%%)",
    "%s (%d regions)": "%s (%d regiones)",
    "%s | %s | %d cores": "%s | %s | %d núcleos",
    "8x RISC-V via PCIe RAM": "8x RISC-V vía RAM PCIe",
    "Active": "Activo",
    "Active (%s)": "Activo (%s)",
    "Airoha SoC Status": "Estado del SoC Airoha",
    "Apply": "Aplicar",
    "Applying...": "Aplicando...",
    "Band %d": "Banda %d",
    "Bound": "Vinculadas",
    "CPU Cores": "Núcleos de CPU",
    "CPU DMA 1": "CPU DMA 1",
    "CPU DMA 2": "CPU DMA 2",
    "CPU Frequency": "Frecuencia de la CPU",
    "CPU set to %d MHz": "CPU ajustada a %d MHz",
    "CPU: %s": "CPU: %s",
    "Cancel": "Cancelar",
    "Confirm overclock": "Confirmar overclock",
    "Continue": "Continuar",
    "Could not set the governor: %s": "No se pudo establecer el regulador: %s",
    "Could not set the maximum frequency: %s":
        "No se pudo establecer la frecuencia máxima: %s",
    "Current Frequency": "Frecuencia actual",
    "Direct PLL write, %d-%d MHz. Tested up to %d MHz.":
        "Escritura directa del PLL, %d-%d MHz. Probado hasta %d MHz.",
    "Drop %s": "Descartes %s",
    "Error: %s": "Error: %s",
    "Ethernet": "Ethernet",
    "Failed: %s": "Falló: %s",
    "Fair": "Regular",
    "Firmware / Clock / Cores": "Firmware / Reloj / Núcleos",
    "Frame Engine": "Motor de tramas",
    "Good": "Bueno",
    "Governor": "Regulador",
    "Grant access to Airoha SoC status (NPU + CPU + Overclock)":
        "Conceder acceso al estado del SoC Airoha (NPU + CPU + Overclock)",
    "HW Offload: %s%%": "Descarga por HW: %s%%",
    "HWF: %s": "HWF: %s",
    "Idle": "Inactivo",
    "Index": "Índice",
    "Internal Switch (1G LAN3/4)": "Switch interno (1G LAN3/4)",
    "LAN2 (USXGMII 10G)": "LAN2 (USXGMII 10G)",
    "Manages:": "Gestiona:",
    "Max Frequency": "Frecuencia máxima",
    "N/A": "N/D",
    "NPU & Offload Engine": "NPU y motor de descarga",
    "NPU Status": "Estado de la NPU",
    "New Flow": "Flujo nuevo",
    "No clients": "Sin clientes",
    "Not Active": "No activo",
    "Not available: unrecognised SoC": "No disponible: SoC no reconocido",
    "Off": "Apagado",
    "Original Flow": "Flujo original",
    "Overclock": "Overclock",
    "Overclock request failed: %s": "La solicitud de overclock falló: %s",
    "P7 WiFi DMA": "P7 DMA WiFi",
    "PPE Engines": "Motores PPE",
    "PPE Flow Offload Entries": "Entradas de descarga de flujo PPE",
    "PPE init, WDMA rings, flow stats":
        "Inicialización de PPE, anillos WDMA, estadísticas de flujos",
    "PSE Port Queue Status": "Estado de las colas de los puertos PSE",
    "PSE Shared Buffer": "Búfer compartido PSE",
    "Poor": "Malo",
    "RX": "RX",
    "RX Drop": "Descartes RX",
    "Reserved Memory": "Memoria reservada",
    "SoC": "SoC",
    "SoC Status": "Estado del SoC",
    "State": "Estado",
    "TX": "TX",
    "TX Drop": "Descartes TX",
    "TX: %s": "TX: %s",
    "The frequency must be between %d and %d MHz":
        "La frecuencia debe estar entre %d y %d MHz",
    "Total": "Total",
    "Type": "Tipo",
    "Unknown": "Desconocido",
    "WAN (USXGMII 10G)": "WAN (USXGMII 10G)",
    "devmem is not available on this build":
        "devmem no está disponible en esta compilación",
}

ZH_HANS = {
    "%d MHz is above %d MHz, which is as far as this has been tested. The "
    "board may run unstable or stop responding until it is power cycled.":
        "%d MHz 高于本功能已测试的 %d MHz 上限。主板可能运行不稳定或停止响应，需断电重启才能恢复。",
    "%d sta": "%d 个终端",
    "%d used / %d free (%s%%)": "已用 %d / 空闲 %d (%s%%)",
    "%s (%d regions)": "%s（%d 个区域）",
    "%s | %s | %d cores": "%s | %s | %d 核",
    "8x RISC-V via PCIe RAM": "8 个 RISC-V 核心（经 PCIe 内存）",
    "Active": "活跃",
    "Active (%s)": "活跃 (%s)",
    "Airoha SoC Status": "Airoha SoC 状态",
    "Apply": "应用",
    "Applying...": "正在应用…",
    "Band %d": "频段 %d",
    "Bound": "已绑定",
    "CPU Cores": "CPU 核心",
    "CPU DMA 1": "CPU DMA 1",
    "CPU DMA 2": "CPU DMA 2",
    "CPU Frequency": "CPU 频率",
    "CPU set to %d MHz": "CPU 已设为 %d MHz",
    "CPU: %s": "CPU：%s",
    "Cancel": "取消",
    "Confirm overclock": "确认超频",
    "Continue": "继续",
    "Could not set the governor: %s": "无法设置 CPU 调度器：%s",
    "Could not set the maximum frequency: %s": "无法设置最大频率：%s",
    "Current Frequency": "当前频率",
    "Direct PLL write, %d-%d MHz. Tested up to %d MHz.":
        "直接写入 PLL，%d-%d MHz，最高已测试至 %d MHz。",
    "Drop %s": "丢弃 %s",
    "Error: %s": "错误：%s",
    "Ethernet": "以太网",
    "Failed: %s": "失败：%s",
    "Fair": "一般",
    "Firmware / Clock / Cores": "固件 / 时钟 / 核心",
    "Frame Engine": "帧引擎",
    "Good": "良好",
    "Governor": "调度器",
    "Grant access to Airoha SoC status (NPU + CPU + Overclock)":
        "授予访问 Airoha SoC 状态（NPU + CPU + 超频）的权限",
    "HW Offload: %s%%": "硬件卸载：%s%%",
    "HWF: %s": "HWF：%s",
    "Idle": "空闲",
    "Index": "索引",
    "Internal Switch (1G LAN3/4)": "内部交换机（1G LAN3/4）",
    "LAN2 (USXGMII 10G)": "LAN2（USXGMII 10G）",
    "Manages:": "管理：",
    "Max Frequency": "最大频率",
    "N/A": "无",
    "NPU & Offload Engine": "NPU 与卸载引擎",
    "NPU Status": "NPU 状态",
    "New Flow": "新流",
    "No clients": "无客户端",
    "Not Active": "未运行",
    "Not available: unrecognised SoC": "不可用：无法识别的 SoC",
    "Off": "关闭",
    "Original Flow": "原始流",
    "Overclock": "超频",
    "Overclock request failed: %s": "超频请求失败：%s",
    "P7 WiFi DMA": "P7 WiFi DMA",
    "PPE Engines": "PPE 引擎",
    "PPE Flow Offload Entries": "PPE 流卸载表项",
    "PPE init, WDMA rings, flow stats": "PPE 初始化、WDMA 环、流统计",
    "PSE Port Queue Status": "PSE 端口队列状态",
    "PSE Shared Buffer": "PSE 共享缓冲区",
    "Poor": "较差",
    "RX": "接收",
    "RX Drop": "接收丢弃",
    "Reserved Memory": "保留内存",
    "SoC": "SoC",
    "SoC Status": "SoC 状态",
    "State": "状态",
    "TX": "发送",
    "TX Drop": "发送丢弃",
    "TX: %s": "发送：%s",
    "The frequency must be between %d and %d MHz": "频率必须在 %d 到 %d MHz 之间",
    "Total": "总计",
    "Type": "类型",
    "Unknown": "未知",
    "WAN (USXGMII 10G)": "WAN（USXGMII 10G）",
    "devmem is not available on this build": "此固件未提供 devmem",
}


# --------------------------------------------------------------------------
# validation helpers
# --------------------------------------------------------------------------
SPEC = re.compile(r"%[-+ #0]*[0-9]*(?:\.[0-9]+)?[diouxXeEfgGcs%]")


def specs(text):
    return SPEC.findall(text)


def normalize_specs(seq):
    """%% is a literal percent sign in LuCI, so it never consumes an argument."""
    return [s for s in seq if s != "%%"]


def check_parity(msgid, msgstr, where):
    a = normalize_specs(specs(msgid))
    b = normalize_specs(specs(msgstr))
    if a != b:
        problems.append(f"{where}: format specifiers differ for {msgid!r}: {a} vs {b}")


problems = []


def parse_po(text):
    """Return [(msgid, msgstr, refs, flags)], header entry first."""
    text = text.replace("\r\n", "\n")
    entries, cur = [], None
    field = None
    for line in text.split("\n"):
        if line.startswith("#:"):
            if cur is not None:
                cur["refs"].append(line[2:].strip())
            field = None
            continue
        if line.startswith("#,"):
            if cur is not None:
                cur["flags"].append(line[2:].strip())
            field = None
            continue
        if line.startswith("#"):
            continue
        if line.startswith("msgid "):
            if cur is not None and cur["msgstr"] is not None:
                entries.append(cur)
                cur = None
            if cur is None:
                cur = {"refs": [], "flags": [], "msgid": "", "msgstr": None}
            cur["msgid"] = unquote(line[6:])
            field = "id"
            continue
        if line.startswith("msgstr "):
            cur["msgstr"] = unquote(line[7:])
            field = "str"
            continue
        if line.startswith('"'):
            piece = unquote(line)
            if field == "id":
                cur["msgid"] += piece
            elif field == "str":
                cur["msgstr"] += piece
            continue
        if not line.strip():
            field = None
    if cur is not None and cur["msgstr"] is not None:
        entries.append(cur)
    return entries


def unquote(line):
    s = line.strip()
    if s.startswith('"') and s.endswith('"'):
        s = s[1:-1]
    return (
        s.replace("\\\\", "\\")
        .replace('\\"', '"')
        .replace("\\n", "\n")
        .replace("\\t", "\t")
    )


def check_catalog(path, expected, translation):
    if not path.exists():
        problems.append(f"{path}: missing")
        return
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        problems.append(f"{path}: has a UTF-8 BOM")
    if b"\r\n" in raw:
        problems.append(f"{path}: contains CRLF line endings")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        problems.append(f"{path}: not valid UTF-8 ({exc})")
        return

    entries = parse_po(text)
    if not entries or entries[0]["msgid"] != "":
        problems.append(f"{path}: first entry is not the header")
        return

    body = {e["msgid"]: e for e in entries[1:]}
    for msgid in expected:
        if msgid not in body:
            problems.append(f"{path}: missing msgid {msgid!r}")
            continue
        got = body[msgid]["msgstr"]
        if not got:
            problems.append(f"{path}: empty translation for {msgid!r}")
        if msgid not in translation:
            problems.append(f"{path}: no expected translation for {msgid!r}")
        elif got != translation[msgid]:
            problems.append(f"{path}: translation differs for {msgid!r}")
    for msgid in body:
        if msgid not in expected:
            problems.append(f"{path}: stale msgid {msgid!r}")
        check_parity(msgid, body[msgid]["msgstr"], str(path))

    # header sanity
    header = entries[0]["msgstr"]
    for field in ("Language:", "Content-Type: text/plain; charset=UTF-8", "Plural-Forms:"):
        if field not in header:
            problems.append(f"{path}: header lacks {field!r}")


def check_pot(path, expected):
    if not path.exists():
        problems.append(f"{path}: missing")
        return
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        problems.append(f"{path}: has a UTF-8 BOM")
    if b"\r\n" in raw:
        problems.append(f"{path}: contains CRLF line endings")
    text = raw.decode("utf-8")
    entries = parse_po(text)
    if not entries or entries[0]["msgid"] != "":
        problems.append(f"{path}: first entry is not the header")
        return
    body = {e["msgid"]: e for e in entries[1:]}
    for msgid in expected:
        if msgid not in body:
            problems.append(f"{path}: missing msgid {msgid!r}")
    for msgid, e in body.items():
        if msgid not in expected:
            problems.append(f"{path}: stale msgid {msgid!r}")
        if e["msgstr"]:
            problems.append(f"{path}: template has a non-empty msgstr for {msgid!r}")


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def render_pot(corpus):
    parts = [POT_HEADER]
    for msgid, refs in corpus.items():
        parts.append(entry(msgid, "", refs))
        parts.append("\n")
    return "".join(parts)


def render_po(lang, team, plural, corpus, table):
    missing = [m for m in corpus if m not in table]
    if missing:
        raise SystemExit(f"{lang}: missing translations for {missing!r}")
    parts = [po_header(lang, team, plural)]
    for msgid, refs in corpus.items():
        parts.append(entry(msgid, table[msgid], refs))
        parts.append("\n")
    return "".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify only, do not write")
    args = ap.parse_args()

    corpus = build_corpus()
    print(f"{len(corpus)} messages in the package "
          f"({len(view_refs())} _() calls in the view)")

    if args.check:
        expected = list(corpus)
        check_pot(POT, expected)
        check_catalog(PO_ES, expected, ES)
        check_catalog(PO_ZH, expected, ZH_HANS)
        if problems:
            print(f"\n{len(problems)} problem(s):")
            for p in problems:
                print(f"  - {p}")
            return 1
        print("catalogs OK: no missing, stale or empty entries, "
              "format specifiers match")
        return 0

    POT.parent.mkdir(parents=True, exist_ok=True)
    PO_ES.parent.mkdir(parents=True, exist_ok=True)
    PO_ZH.parent.mkdir(parents=True, exist_ok=True)
    POT.write_text(render_pot(corpus), encoding="utf-8", newline="\n")
    PO_ES.write_text(
        render_po("es", "Spanish", "nplurals=2; plural=(n != 1);", corpus, ES),
        encoding="utf-8", newline="\n",
    )
    PO_ZH.write_text(
        render_po("zh_Hans", "Chinese (Simplified)", "nplurals=1; plural=0;", corpus, ZH_HANS),
        encoding="utf-8", newline="\n",
    )
    for p in (POT, PO_ES, PO_ZH):
        print(f"wrote {p.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
