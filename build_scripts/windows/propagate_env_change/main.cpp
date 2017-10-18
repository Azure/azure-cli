#include "windows.h"

int main(int argc, LPCWSTR argv[])
{
    LRESULT dwResult = SendMessageTimeout(HWND_BROADCAST,
        WM_SETTINGCHANGE,
        0,
        (LPARAM)L"Environment",
        SMTO_ABORTIFHUNG,
        5000,
        NULL);

    return (dwResult) ? 0 : 1;
}
