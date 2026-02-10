#!/usr/bin/env python
# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC 
# (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S. 
# Government retains certain rights in this software.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
This module parses TIFF files/

Requires: libtiff5-dev Ubuntu package
"""

# Python library imports
import os
import io
import tempfile
import logging

# 3rd-party Python libraries - will fail at startup if not installed (intentional for security)
import tifffile
import numpy

# LaikaBoss imports
import laikaboss
import laikaboss.si_module
import laikaboss.objectmodel
from laikaboss.util import laika_temp_dir

_module_requires = ['tifffile', 'numpy']


class META_TIFF(laikaboss.si_module.SI_MODULE):

    def __init__(self):
        self.module_name = "META_TIFF"

    def _run(self, scanObject, result, depth, args):
        moduleResult = []

        try:
            with laika_temp_dir() as tempdir, tempfile.NamedTemporaryFile(dir=tempdir, delete=False) as fp:
                # Write scan object buffer to temp file
                fp.write(scanObject.buffer)
                fp.flush()
                temp_name = fp.name

            try:
                # Parse TIFF using tifffile
                with tifffile.TiffFile(temp_name) as tif:
                    self._extract_metadata(tif, scanObject)
                    children = self._find_anomalies(tif, scanObject, temp_name)

                    for child_data in children:
                        if isinstance(child_data, str):
                            child_data = child_data.encode('utf-8', 'replace')
                        if child_data and len(child_data) > 0:
                            moduleResult.append(laikaboss.objectmodel.ModuleObject(
                                buffer=child_data,
                                externalVars=laikaboss.objectmodel.ExternalVars(
                                    filename=scanObject.filename + "_subfile",
                                    contentType="application/octet-stream"
                                )
                            ))

            except Exception as e:
                logging.warning("META_TIFF: Unable to parse TIFF file: %s" % str(e))
                scanObject.addFlag('tiff:PARSING_FAIL')

            finally:
                if os.path.exists(temp_name):
                    os.unlink(temp_name)

        except Exception as e:
            logging.exception("META_TIFF error: %s" % str(e))

        return moduleResult

    def _extract_metadata(self, tif, scanObject):
        """Extract TIFF metadata and add to scan object."""
        try:
            for page_idx, page in enumerate(tif.pages):
                # Extract standard TIFF tags
                for tag in page.tags.values():
                    tag_name = tag.name
                    try:
                        if isinstance(tag.value, numpy.ndarray):
                            if 'Name' in tag_name or 'Description' in tag_name:
                                value = tag.value.tobytes().decode('utf-8', 'replace')
                            else:
                                value = str(tag.value.tolist())
                        else:
                            value = tag.value

                        scanObject.addMetadata(self.module_name, f"{tag_name}", value)
                    except Exception as e:
                        scanObject.addFlag('tiff:MALFORMED_IFD_ENTRY')
                        logging.debug(f"META_TIFF: Malformed tag {tag_name}: {e}")

                # Only process first page for metadata
                break

        except Exception as e:
            logging.warning("META_TIFF: Error extracting metadata: %s" % str(e))

    def _find_anomalies(self, tif, scanObject, filename):
        """Check for TIFF anomalies and extract hidden data."""
        children = []
        file_size = os.path.getsize(filename)

        try:
            # Check for data after the last IFD
            last_offset = 0
            for page in tif.pages:
                for tag in page.tags.values():
                    if hasattr(tag, 'valueoffset') and tag.valueoffset:
                        end_offset = tag.valueoffset + (tag.count * tifffile.TIFF.DATATYPES[tag.dtype].itemsize if hasattr(tag, 'dtype') else 0)
                        last_offset = max(last_offset, end_offset)

                # Check strip/tile offsets
                if hasattr(page, 'dataoffsets') and page.dataoffsets is not None:
                    for offset, bytecount in zip(page.dataoffsets, page.databytecounts):
                        end_offset = offset + bytecount
                        last_offset = max(last_offset, end_offset)

            # Check if there's extra data after the TIFF structure
            if last_offset > 0 and last_offset < file_size:
                extra_bytes = file_size - last_offset
                if extra_bytes > 10:  # threshold for unknown bytes
                    scanObject.addFlag('tiff:EXTRA_DATA_AFTER_EOF')
                    # Extract the extra data
                    with open(filename, 'rb') as f:
                        f.seek(last_offset)
                        extra_data = f.read()
                        if extra_data and len(extra_data.strip(b'\x00')) > 0:
                            children.append(extra_data)

            # Check for strips that extend beyond file size
            for page in tif.pages:
                if hasattr(page, 'dataoffsets') and page.dataoffsets is not None:
                    for offset, bytecount in zip(page.dataoffsets, page.databytecounts):
                        if offset + bytecount > file_size:
                            scanObject.addFlag('tiff:STRIP_OUT_OF_BOUNDS')
                        if offset > file_size:
                            scanObject.addFlag('tiff:CORRUPTED')

        except Exception as e:
            logging.debug("META_TIFF: Error checking anomalies: %s" % str(e))

        return children
