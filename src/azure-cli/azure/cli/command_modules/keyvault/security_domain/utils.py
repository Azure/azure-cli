# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


class Utils:
    @staticmethod
    def convert_to_uint16(b: bytearray):
        ret = [0 for _ in range(len(b) // 2)]
        for i in range(0, len(b), 2):
            tmp = bytearray()
            tmp.append(b[i])
            tmp.append(b[i + 1])

            # It's already in the same byte order
            # as the system that encrypted it, so don't reverse it
            ret[i // 2] = (b[i + 1] << 8) | b[i]

        return ret


if __name__ == '__main__':
    b = bytearray()
    b.extend(b'swadawdawd')
    x = Utils.convert_to_uint16(b)
    print(x)
