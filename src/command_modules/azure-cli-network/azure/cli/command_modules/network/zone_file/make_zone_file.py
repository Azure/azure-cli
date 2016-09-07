#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
#The MIT License (MIT)

#Copyright (c) 2016 Blockstack

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.
#pylint: skip-file

from .record_processors import (
    process_origin, process_ttl, process_soa, process_ns, process_a,
    process_aaaa, process_cname, process_mx, process_ptr, process_txt,
    process_srv, process_spf, process_uri
)
from .configs import DEFAULT_TEMPLATE


def make_zone_file(json_zone_file, template=None):
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
        "cname":   [ cname records ]
        "mx":      [ mx records ]
        "ptr":     [ ptr records ]
        "txt":     [ txt records ]
        "srv":     [ srv records ]
        "spf":     [ spf records ]
        "uri":     [ uri records ]
    }
    """

    if template is None:
        template = DEFAULT_TEMPLATE[:]

    soa_records = [json_zone_file.get('soa')] if json_zone_file.get('soa') else None

    zone_file = template
    zone_file = process_origin(json_zone_file.get('$origin', None), zone_file)
    zone_file = process_ttl(json_zone_file.get('$ttl', None), zone_file)
    zone_file = process_soa(soa_records, zone_file)
    zone_file = process_ns(json_zone_file.get('ns', None), zone_file)
    zone_file = process_a(json_zone_file.get('a', None), zone_file)
    zone_file = process_aaaa(json_zone_file.get('aaaa', None), zone_file)
    zone_file = process_cname(json_zone_file.get('cname', None), zone_file)
    zone_file = process_mx(json_zone_file.get('mx', None), zone_file)
    zone_file = process_ptr(json_zone_file.get('ptr', None), zone_file)
    zone_file = process_txt(json_zone_file.get('txt', None), zone_file)
    zone_file = process_srv(json_zone_file.get('srv', None), zone_file)
    zone_file = process_spf(json_zone_file.get('spf', None), zone_file)
    zone_file = process_uri(json_zone_file.get('uri', None), zone_file)

    # remove newlines, but terminate with one
    zone_file = "\n".join(
        filter(
            lambda l: len(l.strip()) > 0, [tl.strip() for tl in zone_file.split("\n")]
        )
    ) + "\n"

    return zone_file
