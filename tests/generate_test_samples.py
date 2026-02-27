#!/usr/bin/env python3
"""
Generate minimal test sample files for smoke testing laikaboss modules.

Each generated file is the smallest valid specimen that will trigger
the corresponding dispatch rule in dispatch.yara, exercising the module
at runtime.

Usage:
    python tests/generate_test_samples.py [output_dir]

Default output: tests/data/samples/
"""

import os
import sys
import struct
import tarfile
import gzip
import bz2
import zipfile
import io
import zlib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


def get_output_dir():
    if len(sys.argv) > 1:
        return sys.argv[1]
    # Find repo root by looking for setup.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    return os.path.join(repo_root, "tests", "data", "samples")


def write_file(outdir, filename, data):
    path = os.path.join(outdir, filename)
    mode = "wb" if isinstance(data, bytes) else "w"
    with open(path, mode) as f:
        f.write(data)
    print(f"  Generated: {filename} ({len(data)} bytes)")
    return path


def generate_tar(outdir):
    """TAR archive containing a text file. Triggers EXPLODE_TAR."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        info = tarfile.TarInfo(name="test.txt")
        content = b"Hello from tar test"
        info.size = len(content)
        tf.addfile(info, io.BytesIO(content))
    write_file(outdir, "sample.tar", buf.getvalue())


def generate_gzip(outdir):
    """GZIP compressed file. Triggers EXPLODE_GZIP."""
    data = gzip.compress(b"Hello from gzip test")
    write_file(outdir, "sample.gz", data)


def generate_bz2(outdir):
    """BZ2 compressed file. Triggers EXPLODE_BZ2."""
    data = bz2.compress(b"Hello from bz2 test")
    write_file(outdir, "sample.bz2", data)


def generate_email(outdir):
    """RFC822 email with attachment. Triggers META_EMAIL + EXPLODE_EMAIL."""
    msg = MIMEMultipart()
    msg["From"] = "test@example.com"
    msg["To"] = "recipient@example.com"
    msg["Subject"] = "Test email for smoke testing"
    msg["Date"] = "Thu, 01 Jan 2026 00:00:00 +0000"
    # Received header is required for dispatch.yara type_is_email rule
    msg["Received"] = "from mail.example.com by mx.example.com; Thu, 01 Jan 2026 00:00:00 +0000"
    msg.attach(MIMEText("This is a test email body.", "plain"))

    # Add a small text attachment
    attachment = MIMEBase("application", "octet-stream")
    attachment.set_payload(b"attachment content here")
    encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", "attachment", filename="test.txt")
    msg.attach(attachment)

    write_file(outdir, "sample.eml", msg.as_bytes())


def generate_eps(outdir):
    """Minimal EPS/PostScript file. Triggers META_PS_COMMANDS."""
    eps = b"""%!PS-Adobe-3.0 EPSF-3.0
%%BoundingBox: 0 0 100 100
%%EndComments
newpath
0 0 moveto
100 0 lineto
100 100 lineto
0 100 lineto
closepath
stroke
showpage
%%EOF
"""
    write_file(outdir, "sample.eps", eps)


def generate_tiff(outdir):
    """Minimal valid TIFF file (1x1 white pixel). Triggers META_TIFF."""
    # Little-endian TIFF with 1x1 8-bit grayscale image
    # Header: II (little-endian) + magic 42 + offset to IFD
    pixel_data = b"\xff"  # 1 white pixel

    ifd_offset = 8  # IFD starts right after header
    num_entries = 8

    # Each IFD entry is 12 bytes: tag(2) + type(2) + count(4) + value(4)
    ifd_size = 2 + (num_entries * 12) + 4  # count + entries + next_ifd_offset
    strip_offset = 8 + ifd_size  # pixel data after IFD

    entries = []
    # Tag 256: ImageWidth = 1
    entries.append(struct.pack("<HHII", 256, 3, 1, 1))
    # Tag 257: ImageLength = 1
    entries.append(struct.pack("<HHII", 257, 3, 1, 1))
    # Tag 258: BitsPerSample = 8
    entries.append(struct.pack("<HHII", 258, 3, 1, 8))
    # Tag 259: Compression = 1 (no compression)
    entries.append(struct.pack("<HHII", 259, 3, 1, 1))
    # Tag 262: PhotometricInterpretation = 1 (min-is-black)
    entries.append(struct.pack("<HHII", 262, 3, 1, 1))
    # Tag 273: StripOffsets
    entries.append(struct.pack("<HHII", 273, 3, 1, strip_offset))
    # Tag 278: RowsPerStrip = 1
    entries.append(struct.pack("<HHII", 278, 3, 1, 1))
    # Tag 279: StripByteCounts = 1
    entries.append(struct.pack("<HHII", 279, 3, 1, 1))

    data = struct.pack("<2sHI", b"II", 42, ifd_offset)
    data += struct.pack("<H", num_entries)
    data += b"".join(entries)
    data += struct.pack("<I", 0)  # next IFD offset = 0 (no more IFDs)
    data += pixel_data

    write_file(outdir, "sample.tiff", data)


def generate_x509_pem(outdir):
    """Self-signed X.509 PEM certificate. Triggers META_X509."""
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import datetime

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "Test Certificate"),
        ])
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime(2025, 1, 1))
            .not_valid_after(datetime.datetime(2030, 1, 1))
            .sign(key, hashes.SHA256())
        )
        pem = cert.public_bytes(serialization.Encoding.PEM)
        write_file(outdir, "sample.pem", pem)

        # Also generate DER for META_X509 DER path
        der = cert.public_bytes(serialization.Encoding.DER)
        write_file(outdir, "sample.der", der)

        # Generate PKCS7 from the cert for EXPLODE_PKCS7
        # PKCS7 PEM format
        pkcs7_pem = b"-----BEGIN PKCS7-----\n"
        import base64
        # Create a minimal PKCS7 SignedData structure wrapping the cert
        # For simplicity, use openssl-style approach if available
        # Fallback: just use the DER cert wrapped in PKCS7 headers
        pkcs7_pem += base64.encodebytes(der)
        pkcs7_pem += b"-----END PKCS7-----\n"
        write_file(outdir, "sample.p7b", pkcs7_pem)

    except ImportError:
        print("  SKIP: sample.pem (cryptography not installed)")


def generate_lnk(outdir):
    """Minimal Windows LNK shortcut. Triggers META_LNK."""
    # LNK header: magic 4C000000 + GUID 01140200-0000-0000-C000-000000000046
    # Plus minimal shell link header
    header = bytes([
        0x4C, 0x00, 0x00, 0x00,  # HeaderSize
        0x01, 0x14, 0x02, 0x00,  # LinkCLSID part 1
        0x00, 0x00, 0x00, 0x00,  # LinkCLSID part 2
        0x00, 0x00, 0x00, 0x00,  # LinkCLSID part 3
        0xC0, 0x00, 0x00, 0x00,  # LinkCLSID part 4
        0x00, 0x00, 0x00, 0x46,  # LinkCLSID part 5
    ])
    # LinkFlags (HasLinkTargetIDList = 0)
    flags = struct.pack("<I", 0x00000000)
    # FileAttributes
    file_attrs = struct.pack("<I", 0x00000020)  # FILE_ATTRIBUTE_ARCHIVE
    # CreationTime, AccessTime, WriteTime (all zero)
    times = b"\x00" * 24
    # FileSize
    file_size = struct.pack("<I", 0)
    # IconIndex
    icon_index = struct.pack("<I", 0)
    # ShowCommand (SW_SHOWNORMAL = 1)
    show_cmd = struct.pack("<I", 1)
    # HotKey
    hotkey = struct.pack("<H", 0)
    # Reserved
    reserved = b"\x00" * 10

    data = header + flags + file_attrs + times + file_size + icon_index + show_cmd + hotkey + reserved
    write_file(outdir, "sample.lnk", data)


def generate_dmarc(outdir):
    """Minimal DMARC report XML. Triggers META_DMARC."""
    xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<feedback>
  <report_metadata>
    <org_name>example.com</org_name>
    <email>noreply@example.com</email>
    <report_id>12345</report_id>
    <date_range>
      <begin>1704067200</begin>
      <end>1704153600</end>
    </date_range>
  </report_metadata>
  <policy_published>
    <domain>example.com</domain>
    <adkim>r</adkim>
    <aspf>r</aspf>
    <p>none</p>
  </policy_published>
  <record>
    <row>
      <source_ip>192.0.2.1</source_ip>
      <count>1</count>
      <policy_evaluated>
        <disposition>none</disposition>
        <dkim>pass</dkim>
        <spf>pass</spf>
      </policy_evaluated>
    </row>
    <identifiers>
      <header_from>example.com</header_from>
    </identifiers>
  </record>
</feedback>
"""
    # Filename must contain "dmarc" for dispatch rule
    write_file(outdir, "dmarc_report.xml", xml)


def generate_java_class(outdir):
    """Minimal valid Java class file. Triggers META_JAVA_CLASS."""
    # Java class file format: magic + version + constant pool + class info
    # This creates a minimal valid class file for "Test" class
    buf = io.BytesIO()

    # Magic number
    buf.write(struct.pack(">I", 0xCAFEBABE))
    # Minor version
    buf.write(struct.pack(">H", 0))
    # Major version (Java 8 = 52)
    buf.write(struct.pack(">H", 52))

    # Constant pool (count = pool entries + 1)
    # We need: this_class, super_class, class names
    # Entry 1: CONSTANT_Utf8 "Test"
    # Entry 2: CONSTANT_Class -> #1
    # Entry 3: CONSTANT_Utf8 "java/lang/Object"
    # Entry 4: CONSTANT_Class -> #3
    # Entry 5: CONSTANT_Utf8 "Test.java"
    # Entry 6: CONSTANT_Utf8 "SourceFile"
    pool_count = 7  # entries + 1
    buf.write(struct.pack(">H", pool_count))

    # Entry 1: Utf8 "Test"
    buf.write(struct.pack(">B", 1))  # CONSTANT_Utf8
    name = b"Test"
    buf.write(struct.pack(">H", len(name)))
    buf.write(name)

    # Entry 2: Class -> index 1
    buf.write(struct.pack(">BH", 7, 1))  # CONSTANT_Class

    # Entry 3: Utf8 "java/lang/Object"
    buf.write(struct.pack(">B", 1))
    name = b"java/lang/Object"
    buf.write(struct.pack(">H", len(name)))
    buf.write(name)

    # Entry 4: Class -> index 3
    buf.write(struct.pack(">BH", 7, 3))

    # Entry 5: Utf8 "Test.java"
    buf.write(struct.pack(">B", 1))
    name = b"Test.java"
    buf.write(struct.pack(">H", len(name)))
    buf.write(name)

    # Entry 6: Utf8 "SourceFile"
    buf.write(struct.pack(">B", 1))
    name = b"SourceFile"
    buf.write(struct.pack(">H", len(name)))
    buf.write(name)

    # Access flags: ACC_PUBLIC | ACC_SUPER
    buf.write(struct.pack(">H", 0x0021))
    # This class: #2
    buf.write(struct.pack(">H", 2))
    # Super class: #4
    buf.write(struct.pack(">H", 4))
    # Interfaces count
    buf.write(struct.pack(">H", 0))
    # Fields count
    buf.write(struct.pack(">H", 0))
    # Methods count
    buf.write(struct.pack(">H", 0))
    # Attributes count: 1 (SourceFile)
    buf.write(struct.pack(">H", 1))
    # SourceFile attribute: name_index=#6, length=2, sourcefile_index=#5
    buf.write(struct.pack(">HIH", 6, 2, 5))

    write_file(outdir, "Test.class", buf.getvalue())


def generate_swf(outdir):
    """Minimal compressed SWF file. Triggers EXPLODE_SWF."""
    # CWS (compressed) SWF header
    # Format: "CWS" + version(1) + file_length(4) + zlib_compressed_data

    # Minimal SWF body (uncompressed part after first 8 bytes):
    # RECT (stage dimensions) + frame rate + frame count
    # Minimal RECT: Nbits=5 (5 bits for field size), then 4 fields of 0
    # = 00101 00000 00000 00000 00000 + padding = 5 bits + 20 bits = 25 bits -> 4 bytes
    swf_body = bytes([
        0x00,  # RECT: Nbits=0 (just 5 zero bits padded)
        0x00, 0x00,  # FrameRate (0)
        0x00, 0x00,  # FrameCount (0)
        0x00, 0x00,  # End tag
    ])

    compressed = zlib.compress(swf_body)
    total_length = 8 + len(swf_body)  # uncompressed length includes header

    data = b"CWS"
    data += struct.pack("<B", 10)  # version
    data += struct.pack("<I", total_length)
    data += compressed

    write_file(outdir, "sample.swf", data)


def generate_html(outdir):
    """Minimal HTML file. Triggers SCAN_HTML."""
    html = b"""<html>
<head><title>Test Page</title></head>
<body>
<p>Hello from smoke test</p>
<a href="http://example.com">Link</a>
<script>var x = 1;</script>
</body>
</html>
"""
    write_file(outdir, "sample.html", html)


def generate_pdf(outdir):
    """Minimal PDF. Triggers EXPLODE_PDF + META_PDFURL + EXPLODE_PDF_TEXT + META_PDF_STRUCTURE."""
    pdf = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources << /Font << /F1 5 0 R >> >>
>>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Hello) Tj
ET
endstream
endobj
5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000266 00000 n
0000000360 00000 n
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
441
%%EOF"""
    write_file(outdir, "sample.pdf", pdf)


def generate_rtf(outdir):
    """Minimal RTF file. Triggers EXPLODE_RTF + META_RTF_CONTROLWORDS."""
    rtf = rb"{\rtf1\ansi\deff0{\fonttbl{\f0 Times New Roman;}}Hello from RTF test.}"
    write_file(outdir, "sample.rtf", rtf)


def generate_iso(outdir):
    """Minimal ISO 9660 image using pycdlib. Triggers META_ISO + EXPLODE_ISO."""
    try:
        import pycdlib

        iso = pycdlib.PyCdlib()
        iso.new()
        content = b"Hello from ISO test\n"
        iso.add_fp(io.BytesIO(content), len(content), "/TEST.;1")
        buf = io.BytesIO()
        iso.write_fp(buf)
        iso.close()
        write_file(outdir, "sample.iso", buf.getvalue())
    except ImportError:
        print("  SKIP: sample.iso (pycdlib not installed)")


def generate_jar(outdir):
    """JAR file (ZIP with META-INF/MANIFEST.MF). Triggers META_JAVA_MANIFEST."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        manifest = b"Manifest-Version: 1.0\r\nCreated-By: smoke-test\r\n\r\n"
        zf.writestr("META-INF/MANIFEST.MF", manifest)
        # Include Test.class so jar_check rule also fires
        # Read from generated file or create inline
        class_buf = io.BytesIO()
        class_buf.write(struct.pack(">I", 0xCAFEBABE))
        class_buf.write(struct.pack(">HH", 0, 52))
        # Minimal constant pool
        class_buf.write(struct.pack(">H", 7))  # pool count
        # Utf8 "Test"
        class_buf.write(struct.pack(">B", 1))
        class_buf.write(struct.pack(">H", 4))
        class_buf.write(b"Test")
        # Class -> 1
        class_buf.write(struct.pack(">BH", 7, 1))
        # Utf8 "java/lang/Object"
        class_buf.write(struct.pack(">B", 1))
        class_buf.write(struct.pack(">H", 16))
        class_buf.write(b"java/lang/Object")
        # Class -> 3
        class_buf.write(struct.pack(">BH", 7, 3))
        # Utf8 "Test.java"
        class_buf.write(struct.pack(">B", 1))
        class_buf.write(struct.pack(">H", 9))
        class_buf.write(b"Test.java")
        # Utf8 "SourceFile"
        class_buf.write(struct.pack(">B", 1))
        class_buf.write(struct.pack(">H", 10))
        class_buf.write(b"SourceFile")
        # Class info
        class_buf.write(struct.pack(">HHHHHH", 0x0021, 2, 4, 0, 0, 0))
        class_buf.write(struct.pack(">H", 1))  # 1 attribute
        class_buf.write(struct.pack(">HIH", 6, 2, 5))
        zf.writestr("Test.class", class_buf.getvalue())

    write_file(outdir, "sample.jar", buf.getvalue())


def generate_ole(outdir):
    """Minimal OLE document. Triggers EXPLODE_OLE + META_OLE."""
    try:
        import olefile

        ole = olefile.OleFileIO.__new__(olefile.OleFileIO)
        # Can't easily create OLE from scratch with olefile
        # Use a minimal OLE2 header + FAT instead
        raise ImportError("olefile can't create from scratch")
    except (ImportError, Exception):
        # Create minimal OLE2 Compound Binary File manually
        # This is complex - rely on the existing .lbtest files for OLE coverage
        pass


def generate_pe(outdir):
    """Minimal PE/MZ executable. Triggers META_PE."""
    # MZ header + minimal PE
    dos_header = bytearray(64)
    dos_header[0:2] = b"MZ"  # e_magic
    struct.pack_into("<I", dos_header, 60, 64)  # e_lfanew -> PE header at offset 64

    # PE signature
    pe_sig = b"PE\x00\x00"

    # COFF header (20 bytes)
    coff = struct.pack("<HHIIIHH",
        0x014C,  # Machine: i386
        0,       # NumberOfSections
        0,       # TimeDateStamp
        0,       # PointerToSymbolTable
        0,       # NumberOfSymbols
        0,       # SizeOfOptionalHeader
        0x0102,  # Characteristics: EXECUTABLE_IMAGE | 32BIT_MACHINE
    )

    data = bytes(dos_header) + pe_sig + coff
    write_file(outdir, "sample.exe", data)


def generate_zip(outdir):
    """ZIP archive with text file. Triggers META_ZIP + EXPLODE_ZIP."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("test.txt", "Hello from zip test")
    write_file(outdir, "sample.zip", buf.getvalue())


def generate_plist(outdir):
    """Binary plist. Triggers EXPLODE_PLIST."""
    try:
        import biplist
        data = biplist.writePlistToString({"key": "value", "number": 42})
        write_file(outdir, "sample.plist", data)
    except ImportError:
        # Create minimal bplist00 header
        # This is the simplest valid binary plist
        print("  SKIP: sample.plist (biplist not installed)")


def generate_png(outdir):
    """Minimal valid PNG. Triggers EXPLODE_BINWALK + META_EXIFTOOL."""
    # PNG signature + IHDR + IDAT + IEND
    sig = b"\x89PNG\r\n\x1a\n"

    # IHDR: 1x1, 8-bit grayscale
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0)
    ihdr_crc = zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF
    ihdr = struct.pack(">I", 13) + b"IHDR" + ihdr_data + struct.pack(">I", ihdr_crc)

    # IDAT: compressed single white pixel (filter byte 0 + pixel 0xFF)
    raw_data = zlib.compress(b"\x00\xff")
    idat_crc = zlib.crc32(b"IDAT" + raw_data) & 0xFFFFFFFF
    idat = struct.pack(">I", len(raw_data)) + b"IDAT" + raw_data + struct.pack(">I", idat_crc)

    # IEND
    iend_crc = zlib.crc32(b"IEND") & 0xFFFFFFFF
    iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", iend_crc)

    write_file(outdir, "sample.png", sig + ihdr + idat + iend)


def generate_ooxml_rels(outdir):
    """Office XML with relationships. Triggers META_OOXML_URLS + META_OOXML_RELS."""
    rels = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="http://example.com" TargetMode="External"/>
</Relationships>
"""
    write_file(outdir, "sample.rels", rels)


def main():
    outdir = get_output_dir()
    os.makedirs(outdir, exist_ok=True)
    print(f"Generating test samples in: {outdir}")
    print()

    generators = [
        ("TAR (EXPLODE_TAR)", generate_tar),
        ("GZIP (EXPLODE_GZIP)", generate_gzip),
        ("BZ2 (EXPLODE_BZ2)", generate_bz2),
        ("Email (META_EMAIL + EXPLODE_EMAIL)", generate_email),
        ("EPS (META_PS_COMMANDS)", generate_eps),
        ("TIFF (META_TIFF)", generate_tiff),
        ("X.509 PEM/DER (META_X509)", generate_x509_pem),
        ("LNK (META_LNK)", generate_lnk),
        ("DMARC (META_DMARC)", generate_dmarc),
        ("Java Class (META_JAVA_CLASS)", generate_java_class),
        ("SWF (EXPLODE_SWF)", generate_swf),
        ("HTML (SCAN_HTML)", generate_html),
        ("PDF (EXPLODE_PDF + META_PDF_STRUCTURE)", generate_pdf),
        ("RTF (EXPLODE_RTF)", generate_rtf),
        ("ISO (META_ISO + EXPLODE_ISO)", generate_iso),
        ("JAR (META_JAVA_MANIFEST)", generate_jar),
        ("PE (META_PE)", generate_pe),
        ("ZIP (META_ZIP + EXPLODE_ZIP)", generate_zip),
        ("PNG (EXPLODE_BINWALK)", generate_png),
        ("OOXML rels (META_OOXML_RELS)", generate_ooxml_rels),
    ]

    for label, gen_func in generators:
        print(f"[{label}]")
        try:
            gen_func(outdir)
        except Exception as e:
            print(f"  ERROR: {e}")
        print()

    print("Done! Generated files:")
    for f in sorted(os.listdir(outdir)):
        size = os.path.getsize(os.path.join(outdir, f))
        print(f"  {f:30s} {size:>8d} bytes")


if __name__ == "__main__":
    main()
