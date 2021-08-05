# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# The MIT License (MIT)

# Copyright (c) 2016 Blockstack

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# pylint: skip-file
def make_zone_file(json_obj):
    """
    Generate the DNS zonefile, given a json-encoded description of the
    zone file (@json_zone_file) and the template to fill in (@template)

    json_zone_file = {
        "$origin": origin server,
        "$ttl":    default time-to-live,
        "soa":     [ soa records ],
        "ns":      [ ns records ],
        "a":       [ a records ],
        "aaaa":    [ aaaa records ]
        "caa":     [ caa records ]
        "cname":   [ cname records ]
        "mx":      [ mx records ]
        "ptr":     [ ptr records ]
        "txt":     [ txt records ]
        "srv":     [ srv records ]
        "spf":     [ spf records ]
        "uri":     [ uri records ]
    }
    """
    import azure.cli.command_modules.network.zone_file.record_processors as record_processors
    from six import StringIO

    zone_file = StringIO()

    HEADER = """
; Exported zone file from Azure DNS\n\
;      Zone name: {zone_name}\n\
;      Resource Group Name: {resource_group}\n\
;      Date and time (UTC): {datetime}\n\n\
$TTL {ttl}\n\
$ORIGIN {origin}\n\
    """
    zone_name = json_obj.pop('zone-name')
    print(HEADER.format(
        zone_name=zone_name,
        resource_group=json_obj.pop('resource-group'),
        datetime=json_obj.pop('datetime'),
        ttl=json_obj.pop('$ttl'),
        origin=json_obj.pop('$origin')
    ), file=zone_file)

    for record_set_name in json_obj.keys():

        record_set = json_obj[record_set_name]
        if record_set_name.endswith(zone_name):
            record_set_name = record_set_name[:-(len(zone_name) + 1)]
        if isinstance(record_set, str):
            # These are handled above so we can skip them
            continue

        first_line = True
        record_set_keys = list(record_set.keys())
        if 'soa' in record_set_keys:
            record_set_keys.remove('soa')
            record_set_keys = ['soa'] + record_set_keys

        for record_type in record_set_keys:

            record = record_set[record_type]
            if not isinstance(record, list):
                record = [record]

            for entry in record:
                method = 'process_{}'.format(record_type.strip('$'))
                getattr(record_processors, method)(zone_file, entry, record_set_name, first_line)
                first_line = False

            print('', file=zone_file)

    result = zone_file.getvalue()
    zone_file.close()

    return result
