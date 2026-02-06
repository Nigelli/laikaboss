# Copyright 2017 Chuck DiRaimondi
# Modified by Sandia National Labs
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

from laikaboss.objectmodel import ExternalVars, ModuleObject, ScanError
from laikaboss.si_module import SI_MODULE
from laikaboss.util import laika_temp_dir
from laikaboss import config
import os
import tempfile
import dnfile


class META_DOTNET(SI_MODULE):
    def __init__(self):
        self.module_name = "META_DOTNET"

    def _run(self, scanObject, result, depth, args):
        moduleResult = []
        guids = {}

        try:
            with laika_temp_dir() as temp_dir, tempfile.NamedTemporaryFile(dir=temp_dir, delete=False) as temp_file_input:
                temp_file_input_name = temp_file_input.name
                temp_file_input.write(scanObject.buffer)
                temp_file_input.flush()

            try:
                pe = dnfile.dnPE(temp_file_input_name)

                if hasattr(pe, 'net') and pe.net is not None:
                    # Get MVID from Module table
                    if hasattr(pe.net, 'mdtables') and pe.net.mdtables is not None:
                        module_table = getattr(pe.net.mdtables, 'Module', None)
                        if module_table and len(module_table.rows) > 0:
                            mvid_index = module_table.rows[0].Mvid
                            if pe.net.guids and mvid_index > 0 and mvid_index <= len(pe.net.guids):
                                guids['MVID'] = str(pe.net.guids[mvid_index - 1])
                            else:
                                guids['MVID'] = "None"
                        else:
                            guids['MVID'] = "None"
                    else:
                        guids['MVID'] = "None"

                    # TypeLib ID - often stored in assembly custom attributes
                    # For now, set to None as it requires deeper parsing
                    guids['Typelib_ID'] = "None"

                pe.close()

            finally:
                if os.path.exists(temp_file_input_name):
                    os.unlink(temp_file_input_name)

            # Only attach metadata if we found something useful
            if guids:
                scanObject.addMetadata(self.module_name, 'DotNet_GUIDs', guids)

        except ScanError:
            raise

        return moduleResult
